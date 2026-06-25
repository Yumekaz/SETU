#!/usr/bin/env python3
"""Phase 6 comprehensive verification — backend, frontend, API probes, browser."""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"
SCRATCH = Path(os.environ.get("SCRATCH_DIR", "/tmp/grok-goal-df3a238e5ed0/implementer"))
SCRATCH.mkdir(parents=True, exist_ok=True)

SUMMARY_PATH = SCRATCH / "phase6_verification.txt"
gates: dict[str, str] = {}


@contextmanager
def env_snapshot():
    """Snapshot and restore os.environ around probe blocks."""
    saved = os.environ.copy()
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(saved)


def run_cmd(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    timeout: int = 600,
) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        cmd,
        cwd=cwd or ROOT,
        env=merged,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def gate(name: str, ok: bool, detail: str = "") -> None:
    status = "PASS" if ok else "FAIL"
    gates[name] = status
    line = f"{name}={status}"
    if detail:
        line += f" ({detail})"
    print(line)


def write_summary(extra: list[str] | None = None) -> None:
    lines = [f"scratch={SCRATCH}", f"root={ROOT}", ""]
    for name, status in gates.items():
        lines.append(f"{name}={status}")
    if extra:
        lines.extend(["", *extra])
    all_pass = all(v == "PASS" for v in gates.values())
    lines.append("")
    lines.append(f"overall={'PASS' if all_pass else 'FAIL'}")
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nWrote {SUMMARY_PATH}")


def normalize_pytest_log(content: str) -> str:
    """Strip wall-clock duration from summary so identical runs hash equally."""
    return re.sub(r" in [\d.]+s.*$", "", content, flags=re.MULTILINE)


def run_phase6_api_pytest() -> None:
    """Delegate API/dashboard probes to tests/test_phase6_api.py (single source of truth)."""
    env = {
        "SETU_MC_N_SIMULATIONS": "50",
        "SETU_EXTRACTOR_MODE": "rules",
    }
    proc = run_cmd(
        ["python3", "-m", "pytest", "tests/test_phase6_api.py", "-q", "--tb=line"],
        env=env,
        timeout=300,
    )
    log_path = SCRATCH / "phase6_api_pytest.log"
    log_path.write_text(proc.stdout + proc.stderr, encoding="utf-8")
    gate(
        "phase6_api_pytest",
        proc.returncode == 0,
        f"exit={proc.returncode}",
    )


def verify_frontend() -> tuple[int, int]:
    npm = shutil.which("npm")
    if not npm:
        gate("frontend_npm_test", False, "npm not found")
        gate("frontend_build", False, "npm not found")
        return 0, 0

    test = run_cmd([npm, "test"], cwd=FRONTEND, timeout=120)
    (SCRATCH / "phase6_frontend_test.log").write_text(
        test.stdout + test.stderr, encoding="utf-8"
    )
    vitest_pass = test.returncode == 0
    passed = 0
    if vitest_pass:
        for line in test.stdout.splitlines():
            if "Tests" in line and "passed" in line:
                try:
                    passed = int(line.strip().split()[1])
                except (IndexError, ValueError):
                    pass
    gate("frontend_npm_test", vitest_pass, f"exit={test.returncode} passed={passed}")

    build = run_cmd([npm, "run", "build"], cwd=FRONTEND, timeout=180)
    (SCRATCH / "phase6_frontend_build.log").write_text(
        build.stdout + build.stderr, encoding="utf-8"
    )
    gate("frontend_build", build.returncode == 0, f"exit={build.returncode}")
    return passed, test.returncode


def wait_http(url: str, timeout: float = 60.0) -> bool:
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


def _run_browser_gate(
    gate_name: str,
    *,
    db_path: Path,
    seed: bool,
    cold_start: bool,
    api_port: str = "8765",
    ui_port: str = "4173",
) -> None:
    node = shutil.which("node")
    npm = shutil.which("npm")
    if not node or not npm:
        gate(gate_name, False, "node/npm unavailable")
        return

    api_url = f"http://127.0.0.1:{api_port}"
    ui_url = f"http://127.0.0.1:{ui_port}"
    backend_proc: subprocess.Popen[str] | None = None
    frontend_proc: subprocess.Popen[str] | None = None
    backend_log = SCRATCH / f"{gate_name}_backend.log"
    frontend_log = SCRATCH / f"{gate_name}_frontend.log"

    try:
        backend_env = os.environ.copy()
        backend_env.update(
            {
                "DATABASE_URL": f"sqlite:////{db_path}",
                "SETU_MC_N_SIMULATIONS": "50",
                "SETU_EXTRACTOR_MODE": "rules",
                "CORS_ORIGINS": f"http://127.0.0.1:{ui_port},http://localhost:{ui_port}",
            }
        )
        backend_log.parent.mkdir(parents=True, exist_ok=True)
        backend_proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                api_port,
            ],
            cwd=ROOT / "backend",
            env=backend_env,
            stdout=backend_log.open("w", encoding="utf-8"),
            stderr=subprocess.STDOUT,
        )
        if not wait_http(f"{api_url}/health", timeout=90):
            gate(gate_name, False, "backend health timeout")
            return
        if backend_proc.poll() is not None:
            gate(gate_name, False, "backend exited early")
            return

        if seed:
            seed_proc = run_cmd(
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
                timeout=180,
            )
            (SCRATCH / f"{gate_name}_seed.log").write_text(
                seed_proc.stdout + seed_proc.stderr, encoding="utf-8"
            )
            if seed_proc.returncode != 0:
                gate(gate_name, False, "baseline seed failed")
                return

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
                ui_port,
                "--strictPort",
            ],
            cwd=FRONTEND,
            env=frontend_env,
            stdout=frontend_log.open("w", encoding="utf-8"),
            stderr=subprocess.STDOUT,
        )
        if not wait_http(ui_url, timeout=90):
            gate(gate_name, False, "frontend timeout")
            return

        browser_env = os.environ.copy()
        browser_env["SETU_API_URL"] = api_url
        browser_env["SETU_UI_URL"] = ui_url
        browser_env["SCRATCH_DIR"] = str(SCRATCH)
        if cold_start:
            browser_env["SETU_BROWSER_COLD_START"] = "1"
        browser = run_cmd(
            ["node", str(ROOT / "scripts" / "phase6_browser_check.mjs")],
            cwd=FRONTEND,
            env=browser_env,
            timeout=420 if cold_start else 300,
        )
        (SCRATCH / f"{gate_name}_run.log").write_text(
            browser.stdout + browser.stderr, encoding="utf-8"
        )
        detail = f"exit={browser.returncode}"
        if gate_name == "browser_check_seeded":
            detail += " internal_runs=2"
        gate(gate_name, browser.returncode == 0, detail)
    finally:
        for proc in (frontend_proc, backend_proc):
            if proc and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()


def verify_browser() -> None:
    npx = shutil.which("npx")
    if not npx:
        gate("browser_cold_start", False, "npx unavailable")
        gate("browser_check_seeded", False, "npx unavailable")
        (SCRATCH / "phase6_browser_fallback.log").write_text(
            "npx not available — browser check skipped\n", encoding="utf-8"
        )
        return

    pw_check = run_cmd([npx, "playwright", "--version"], cwd=FRONTEND, timeout=30)
    if pw_check.returncode != 0:
        gate("browser_cold_start", False, "playwright unavailable")
        gate("browser_check_seeded", False, "playwright unavailable")
        (SCRATCH / "phase6_browser_fallback.log").write_text(
            pw_check.stdout + pw_check.stderr, encoding="utf-8"
        )
        return

    api_url = "http://127.0.0.1:8765"
    npm = shutil.which("npm")
    if not npm:
        gate("browser_cold_start", False, "npm unavailable")
        gate("browser_check_seeded", False, "npm unavailable")
        return
    browser_build = run_cmd(
        [npm, "run", "build"],
        cwd=FRONTEND,
        env={**os.environ, "VITE_API_URL": api_url},
        timeout=180,
    )
    (SCRATCH / "phase6_browser_build.log").write_text(
        browser_build.stdout + browser_build.stderr, encoding="utf-8"
    )
    if browser_build.returncode != 0:
        gate("browser_cold_start", False, "browser build failed")
        gate("browser_check_seeded", False, "browser build failed")
        return

    _run_browser_gate(
        "browser_cold_start",
        db_path=SCRATCH / "phase6_browser_cold.db",
        seed=False,
        cold_start=True,
    )
    _run_browser_gate(
        "browser_check_seeded",
        db_path=SCRATCH / "phase6_browser.db",
        seed=True,
        cold_start=False,
    )
def run_pytest_twice() -> tuple[int, int, str, str]:
    env = {
        "SETU_MC_N_SIMULATIONS": "50",
        "SETU_EXTRACTOR_MODE": "rules",
    }
    counts: list[int] = []
    hashes: list[str] = []
    for i in (1, 2):
        proc = run_cmd(
            ["python3", "-m", "pytest", "tests/", "-q", "--tb=line"],
            env=env,
            timeout=900,
        )
        log = SCRATCH / f"phase6_pytest_run{i}.log"
        content = proc.stdout + proc.stderr
        log.write_text(content, encoding="utf-8")
        normalized = normalize_pytest_log(content)
        hashes.append(hashlib.sha256(normalized.encode("utf-8")).hexdigest())
        ok = proc.returncode == 0
        passed = 0
        for line in proc.stdout.splitlines():
            if " passed" in line and " in " in line:
                try:
                    passed = int(line.split(" passed")[0].strip().split()[-1])
                except (IndexError, ValueError):
                    pass
        counts.append(passed)
        gate(f"pytest_full_run{i}", ok, f"passed={passed} exit={proc.returncode}")
    identical = counts[0] == counts[1] and counts[0] > 0 and hashes[0] == hashes[1]
    gate(
        "pytest_runs_identical",
        identical,
        f"run1={counts[0]} run2={counts[1]} hash_match={hashes[0] == hashes[1]}",
    )
    return counts[0], counts[1], hashes[0], hashes[1]


def main() -> int:
    print(f"Phase 6 verification — scratch={SCRATCH}")
    with env_snapshot():
        pytest1, pytest2, hash1, hash2 = run_pytest_twice()
        vitest_passed, _ = verify_frontend()
        run_phase6_api_pytest()
        verify_browser()

    extra = [
        f"pytest_run1_passed={pytest1}",
        f"pytest_run2_passed={pytest2}",
        f"pytest_run1_sha256={hash1}",
        f"pytest_run2_sha256={hash2}",
        f"vitest_passed={vitest_passed}",
    ]
    write_summary(extra)
    all_pass = all(v == "PASS" for v in gates.values())
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())