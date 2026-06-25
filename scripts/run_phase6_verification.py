#!/usr/bin/env python3
"""Phase 6 comprehensive verification — backend, frontend, API probes, browser."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"
SCRATCH = Path(os.environ.get("SCRATCH_DIR", "/tmp/grok-goal-df3a238e5ed0/implementer"))
SCRATCH.mkdir(parents=True, exist_ok=True)

SUMMARY_PATH = SCRATCH / "phase6_verification.txt"
gates: dict[str, str] = {}


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
    all_pass = all(v == "PASS" for v in gates.values()) and all(
        v != "SKIP_FAIL" for v in gates.values()
    )
    lines.append("")
    lines.append(f"overall={'PASS' if all_pass else 'FAIL'}")
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nWrote {SUMMARY_PATH}")


def verify_phase6_api_twice() -> None:
    env = {
        "DATABASE_URL": f"sqlite:////{SCRATCH / 'phase6_verify.db'}",
        "SETU_MC_N_SIMULATIONS": "50",
        "SETU_EXTRACTOR_MODE": "rules",
    }
    log_path = SCRATCH / "phase6_backend_feeds.log"
    log_lines: list[str] = []

    sys.path.insert(0, str(ROOT / "backend"))
    sys.path.insert(0, str(ROOT))
    from app.database import init_db
    from app.main import app
    from fastapi.testclient import TestClient

    os.environ.update(env)
    init_db()
    client = TestClient(app)

    health = client.get("/health").json()
    log_lines.append(f"health={json.dumps(health)}")
    health_ok = health == {"status": "ok", "version": "0.7.0", "phase": 6}
    gate("backend_health", health_ok, json.dumps(health))

    t1 = client.get("/api/backtest/trajectory").json()
    t2 = client.get("/api/backtest/trajectory").json()
    log_lines.append(f"trajectory_points={len(t1.get('points', []))}")
    traj_ok = (
        len(t1.get("points", [])) >= 140
        and t1.get("points", [{}])[0].get("date") == "2026-02-01"
        and t1 == t2
    )
    gate("backend_trajectory_twice", traj_ok, f"points={len(t1.get('points', []))}")

    tl1 = client.get("/api/backtest/timeline").json()
    tl2 = client.get("/api/backtest/timeline").json()
    log_lines.append(f"timeline_rows={len(tl1)}")
    tl_ok = (
        8 <= len(tl1) <= 12
        and all(r.get("source_url", "").strip() for r in tl1)
        and tl1 == tl2
    )
    gate("backend_timeline_twice", tl_ok, f"rows={len(tl1)}")

    log_path.write_text("\n".join(log_lines) + "\n", encoding="utf-8")


def probe_default_dashboard() -> None:
    sys.path.insert(0, str(ROOT / "backend"))
    sys.path.insert(0, str(ROOT))
    from app.database import init_db
    from app.main import app
    from fastapi.testclient import TestClient

    db = SCRATCH / "phase6_default.db"
    os.environ["DATABASE_URL"] = f"sqlite:////{db}"
    os.environ.setdefault("SETU_MC_N_SIMULATIONS", "50")
    os.environ.setdefault("SETU_EXTRACTOR_MODE", "rules")
    init_db()
    client = TestClient(app)

    log_path = SCRATCH / "phase6_default_and_unrehearsed.log"
    log: list[str] = []

    pipe = client.post("/api/pipeline/run", json={"source": "cache"})
    log.append(f"pipeline_status={pipe.status_code}")
    forecasts = client.get("/api/forecast/latest").json()
    if len(forecasts) == 0:
        fc_run = client.post("/api/forecast/run")
        log.append(f"forecast_run_status={fc_run.status_code}")
        forecasts = client.get("/api/forecast/latest").json()
    scores = client.get("/api/risk-scores/latest").json()
    log.append(f"forecast_count={len(forecasts)} score_count={len(scores)}")

    ok = (
        pipe.status_code == 200
        and len(forecasts) >= 1
        and bool(forecasts[0].get("trajectory"))
        and len(scores) >= 1
    )
    gate("default_dashboard_populated", ok)

    client.post("/api/forecast/run")
    cascade = client.post(
        "/api/cascade/simulate",
        json={"corridor": "MALACCA", "n_simulations": 50},
    )
    rec = client.post("/api/recommendations/run?force=true")
    log.append(f"malacca_cascade={cascade.status_code} recs={rec.status_code}")
    if cascade.status_code == 200:
        log.append(f"cascade_corridor={cascade.json().get('corridor')}")
    if rec.status_code == 200:
        log.append(f"rec_options={len(rec.json().get('options', []))}")

    unrehearsed_ok = (
        cascade.status_code == 200
        and cascade.json().get("corridor") == "MALACCA"
        and rec.status_code == 200
        and len(rec.json().get("options", [])) >= 1
    )
    gate("unrehearsed_malacca_flow", unrehearsed_ok)
    log_path.write_text("\n".join(log) + "\n", encoding="utf-8")


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


def verify_browser() -> None:
    node = shutil.which("node")
    npm = shutil.which("npm")
    npx = shutil.which("npx")
    if not node or not npm or not npx:
        gate("browser_check_twice", False, "node/npm unavailable")
        (SCRATCH / "phase6_browser_fallback.log").write_text(
            "node/npm not available — browser check skipped\n", encoding="utf-8"
        )
        return

    pw_check = run_cmd([npx, "playwright", "--version"], cwd=FRONTEND, timeout=30)
    if pw_check.returncode != 0:
        gate("browser_check_twice", False, "playwright unavailable")
        (SCRATCH / "phase6_browser_fallback.log").write_text(
            pw_check.stdout + pw_check.stderr, encoding="utf-8"
        )
        return

    dist = FRONTEND / "dist"
    if not dist.exists():
        gate("browser_check_twice", False, "frontend dist missing — run build first")
        return

    backend_proc: subprocess.Popen[str] | None = None
    frontend_proc: subprocess.Popen[str] | None = None
    api_port = "8765"
    ui_port = "5173"
    api_url = f"http://127.0.0.1:{api_port}"
    ui_url = f"http://127.0.0.1:{ui_port}"

    try:
        db = SCRATCH / "phase6_browser.db"
        backend_env = os.environ.copy()
        backend_env.update(
            {
                "DATABASE_URL": f"sqlite:////{db}",
                "SETU_MC_N_SIMULATIONS": "50",
                "SETU_EXTRACTOR_MODE": "rules",
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
                api_port,
            ],
            cwd=ROOT / "backend",
            env=backend_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if not wait_http(f"{api_url}/health", timeout=90):
            gate("browser_check_twice", False, "backend health timeout")
            return

        if backend_proc.poll() is not None:
            gate("browser_check_twice", False, "backend exited early")
            return

        seed = run_cmd(
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
        (SCRATCH / "phase6_browser_seed.log").write_text(
            seed.stdout + seed.stderr, encoding="utf-8"
        )
        if seed.returncode != 0:
            gate("browser_check_twice", False, "baseline seed failed")
            return

        frontend_env = os.environ.copy()
        frontend_env["VITE_API_URL"] = api_url
        frontend_proc = subprocess.Popen(
            [npm, "run", "preview", "--", "--host", "127.0.0.1", "--port", ui_port],
            cwd=FRONTEND,
            env=frontend_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        if not wait_http(ui_url, timeout=90):
            gate("browser_check_twice", False, "frontend timeout")
            return

        browser_env = os.environ.copy()
        browser_env["SETU_API_URL"] = api_url
        browser_env["SETU_UI_URL"] = ui_url
        browser_env["SCRATCH_DIR"] = str(SCRATCH)
        browser = run_cmd(
            ["node", str(ROOT / "scripts" / "phase6_browser_check.mjs")],
            cwd=FRONTEND,
            env=browser_env,
            timeout=300,
        )
        (SCRATCH / "phase6_browser_run.log").write_text(
            browser.stdout + browser.stderr, encoding="utf-8"
        )
        gate(
            "browser_check_twice",
            browser.returncode == 0,
            f"exit={browser.returncode}",
        )
    finally:
        for proc in (frontend_proc, backend_proc):
            if proc and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()


def run_pytest_twice() -> tuple[int, int]:
    env = {
        "SETU_MC_N_SIMULATIONS": "50",
        "SETU_EXTRACTOR_MODE": "rules",
    }
    counts: list[int] = []
    for i in (1, 2):
        proc = run_cmd(
            ["python3", "-m", "pytest", "tests/", "-q", "--tb=line"],
            env=env,
            timeout=900,
        )
        log = SCRATCH / f"phase6_pytest_run{i}.log"
        log.write_text(proc.stdout + proc.stderr, encoding="utf-8")
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
    return counts[0], counts[1]


def main() -> int:
    print(f"Phase 6 verification — scratch={SCRATCH}")
    pytest1, pytest2 = run_pytest_twice()
    vitest_passed, _ = verify_frontend()
    verify_phase6_api_twice()
    probe_default_dashboard()
    verify_browser()

    extra = [
        f"pytest_run1_passed={pytest1}",
        f"pytest_run2_passed={pytest2}",
        f"vitest_passed={vitest_passed}",
    ]
    write_summary(extra)
    all_pass = all(v == "PASS" for v in gates.values())
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())