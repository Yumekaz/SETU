#!/usr/bin/env python3
"""Isolated Phase 6 browser gate — one subprocess, ephemeral ports, per-gate transcript."""

from __future__ import annotations

import argparse
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"
SCRATCH = Path(os.environ.get("SCRATCH_DIR", "/tmp/grok-goal-df3a238e5ed0/implementer"))


def pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def ensure_port_free(port: int, *, attempts: int = 5) -> None:
    """Best-effort release of listeners on port before bind."""
    for _ in range(attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                probe.bind(("127.0.0.1", port))
                return
            except OSError:
                pass
        try:
            subprocess.run(
                ["fuser", "-k", f"{port}/tcp"],
                capture_output=True,
                timeout=5,
                check=False,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        time.sleep(0.5)
    raise RuntimeError(f"port {port} still in use after cleanup attempts")


def wait_http(url: str, timeout: float = 90.0) -> bool:
    import urllib.error
    import urllib.request

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status < 500:
                    return True
        except (urllib.error.URLError, TimeoutError, OSError):
            time.sleep(0.5)
    return False


def frontend_log_ok(log_path: Path) -> tuple[bool, str]:
    if not log_path.exists():
        return False, "frontend log missing"
    text = log_path.read_text(encoding="utf-8", errors="replace")
    if "already in use" in text.lower():
        return False, "port already in use in frontend log"
    if "error:" in text.lower() and "error when starting preview server" in text.lower():
        return False, "preview server error in frontend log"
    return True, "ok"


def validate_browser_log(log_path: Path, *, cold_start: bool) -> tuple[bool, str]:
    if not log_path.exists():
        return False, "browser log missing"
    text = log_path.read_text(encoding="utf-8", errors="replace")
    if len(text.strip()) < 50:
        return False, f"browser log too short ({len(text)} bytes)"

    required = [
        "cape_badge=true",
        "forecast_populated=true",
        "page_errors=0",
    ]
    if cold_start:
        required.append("cold_start=true")
    for needle in required:
        if needle not in text:
            return False, f"missing {needle}"

    markers_line = next((ln for ln in text.splitlines() if "map_markers=" in ln), "")
    if markers_line:
        try:
            count = int(markers_line.split("map_markers=")[1].split()[0])
            if count < 5:
                return False, f"map_markers={count} < 5"
        except (IndexError, ValueError):
            return False, "could not parse map_markers"

    return True, "ok"


def terminate(proc: subprocess.Popen[str] | None) -> None:
    if proc is None or proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


def run_gate(gate_name: str) -> int:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    cold_start = gate_name == "browser_cold_start"
    seed = gate_name == "browser_check_seeded"

    node = shutil.which("node")
    npm = shutil.which("npm")
    if not node or not npm:
        (SCRATCH / f"{gate_name}_run.log").write_text("node/npm unavailable\n", encoding="utf-8")
        return 1

    api_port = pick_free_port()
    ui_port = pick_free_port()
    while ui_port == api_port:
        ui_port = pick_free_port()

    api_url = f"http://127.0.0.1:{api_port}"
    ui_url = f"http://127.0.0.1:{ui_port}"
    db_path = SCRATCH / ("phase6_browser_cold.db" if cold_start else "phase6_browser.db")

    backend_log = SCRATCH / f"{gate_name}_backend.log"
    frontend_log = SCRATCH / f"{gate_name}_frontend.log"
    browser_log = SCRATCH / f"{gate_name}_browser.log"
    run_log = SCRATCH / f"{gate_name}_run.log"

    backend_proc: subprocess.Popen[str] | None = None
    frontend_proc: subprocess.Popen[str] | None = None
    lines: list[str] = [
        f"gate={gate_name}",
        f"api_url={api_url}",
        f"ui_url={ui_url}",
        f"api_port={api_port}",
        f"ui_port={ui_port}",
        f"cold_start={cold_start}",
        f"seed={seed}",
    ]

    try:
        ensure_port_free(api_port)
        ensure_port_free(ui_port)

        backend_env = os.environ.copy()
        backend_env.update(
            {
                "DATABASE_URL": f"sqlite:////{db_path}",
                "SETU_MC_N_SIMULATIONS": "50",
                "SETU_EXTRACTOR_MODE": "rules",
                "CORS_ORIGINS": f"{ui_url},http://localhost:{ui_port}",
            }
        )
        backend_proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(api_port),
            ],
            cwd=ROOT / "backend",
            env=backend_env,
            stdout=backend_log.open("w", encoding="utf-8"),
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        if not wait_http(f"{api_url}/health", timeout=90):
            lines.append("FAIL=backend health timeout")
            run_log.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return 1
        if backend_proc.poll() is not None:
            lines.append("FAIL=backend exited early")
            run_log.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return 1

        build_proc = subprocess.run(
            [npm, "run", "build"],
            cwd=FRONTEND,
            env={**os.environ, "VITE_API_URL": api_url},
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        (SCRATCH / f"{gate_name}_build.log").write_text(
            build_proc.stdout + build_proc.stderr, encoding="utf-8"
        )
        if build_proc.returncode != 0:
            lines.append("FAIL=frontend build failed")
            run_log.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return 1

        if seed:
            seed_proc = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    f"""
import urllib.request, json
api = "{api_url}"
def post(path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        api + path,
        data=data,
        headers={{"Content-Type": "application/json"}} if body else {{}},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.status
post("/api/pipeline/run", {{"source": "cache"}})
post("/api/forecast/run")
print("seeded")
""",
                ],
                capture_output=True,
                text=True,
                timeout=180,
                check=False,
            )
            (SCRATCH / f"{gate_name}_seed.log").write_text(
                seed_proc.stdout + seed_proc.stderr, encoding="utf-8"
            )
            if seed_proc.returncode != 0:
                lines.append("FAIL=baseline seed failed")
                run_log.write_text("\n".join(lines) + "\n", encoding="utf-8")
                return 1

        frontend_env = os.environ.copy()
        frontend_env["VITE_API_URL"] = api_url
        frontend_proc = subprocess.Popen(
            [
                npm,
                "run",
                "preview",
                "--",
                "--host",
                "127.0.0.1",
                "--port",
                str(ui_port),
                "--strictPort",
            ],
            cwd=FRONTEND,
            env=frontend_env,
            stdout=frontend_log.open("w", encoding="utf-8"),
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        time.sleep(2)
        if frontend_proc.poll() is not None:
            lines.append("FAIL=frontend exited before health check")
            run_log.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return 1
        log_ok, log_reason = frontend_log_ok(frontend_log)
        if not log_ok:
            lines.append(f"FAIL=frontend log: {log_reason}")
            run_log.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return 1
        if not wait_http(ui_url, timeout=90):
            lines.append("FAIL=frontend HTTP timeout")
            run_log.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return 1
        if frontend_proc.poll() is not None:
            lines.append("FAIL=frontend exited during wait")
            run_log.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return 1
        log_ok, log_reason = frontend_log_ok(frontend_log)
        if not log_ok:
            lines.append(f"FAIL=frontend log after wait: {log_reason}")
            run_log.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return 1

        browser_env = os.environ.copy()
        browser_env["SETU_API_URL"] = api_url
        browser_env["SETU_UI_URL"] = ui_url
        browser_env["SCRATCH_DIR"] = str(SCRATCH)
        browser_env["SETU_BROWSER_LOG"] = str(browser_log)
        browser_env["SETU_GATE_NAME"] = gate_name
        if cold_start:
            browser_env["SETU_BROWSER_COLD_START"] = "1"

        browser = subprocess.run(
            ["node", str(ROOT / "scripts" / "phase6_browser_check.mjs")],
            cwd=FRONTEND,
            env=browser_env,
            capture_output=True,
            text=True,
            timeout=420 if cold_start else 300,
            check=False,
        )
        run_log.write_text(
            "\n".join(lines)
            + "\n"
            + browser.stdout
            + browser.stderr
            + f"\nbrowser_exit={browser.returncode}\n",
            encoding="utf-8",
        )
        if browser.returncode != 0:
            return 1

        valid, reason = validate_browser_log(browser_log, cold_start=cold_start)
        if not valid:
            run_log.write_text(
                run_log.read_text(encoding="utf-8") + f"FAIL=log validation: {reason}\n",
                encoding="utf-8",
            )
            return 1

        run_log.write_text(
            run_log.read_text(encoding="utf-8") + "PASS=gate ok\n",
            encoding="utf-8",
        )
        return 0
    finally:
        terminate(frontend_proc)
        terminate(backend_proc)
        for proc in (frontend_proc, backend_proc):
            if proc and proc.poll() is None:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except (ProcessLookupError, PermissionError):
                    proc.kill()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--gate",
        required=True,
        choices=["browser_cold_start", "browser_check_seeded"],
    )
    args = parser.parse_args()
    return run_gate(args.gate)


if __name__ == "__main__":
    raise SystemExit(main())