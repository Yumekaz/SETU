#!/usr/bin/env python3
"""Phase 6 comprehensive verification — backend, frontend, API probes, browser."""

from __future__ import annotations

import hashlib
import json
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


def _phase6_test_client(db_name: str) -> object:
    """Build a TestClient on an isolated scratch DB for evidence capture."""
    sys.path.insert(0, str(ROOT / "backend"))
    sys.path.insert(0, str(ROOT))
    from app.database import init_db
    from app.main import app
    from fastapi.testclient import TestClient

    os.environ["DATABASE_URL"] = f"sqlite:////{SCRATCH / db_name}"
    os.environ.setdefault("SETU_MC_N_SIMULATIONS", "50")
    os.environ.setdefault("SETU_EXTRACTOR_MODE", "rules")
    init_db()
    return TestClient(app)


def write_backend_feeds_log() -> None:
    """Capture health + backtest feeds to phase6_backend_feeds.log (plan step 2)."""
    client = _phase6_test_client("phase6_verify.db")
    health = client.get("/health").json()
    t1 = client.get("/api/backtest/trajectory").json()
    t2 = client.get("/api/backtest/trajectory").json()
    tl1 = client.get("/api/backtest/timeline").json()
    tl2 = client.get("/api/backtest/timeline").json()
    lines = [
        f"health={json.dumps(health)}",
        f"trajectory_points={len(t1.get('points', []))}",
        f"trajectory_bit_identical={t1 == t2}",
        f"timeline_rows={len(tl1)}",
        f"timeline_bit_identical={tl1 == tl2}",
    ]
    (SCRATCH / "phase6_backend_feeds.log").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_default_and_unrehearsed_log() -> None:
    """Capture dashboard + MALACCA probe outcomes (plan step 5)."""
    client = _phase6_test_client("phase6_default.db")
    log: list[str] = []

    pipe = client.post("/api/pipeline/run", json={"source": "cache"})
    log.append(f"pipeline_status={pipe.status_code}")
    forecasts = client.get("/api/forecast/latest").json()
    if len(forecasts) == 0:
        fc_run = client.post("/api/forecast/run")
        log.append(f"forecast_run_status={fc_run.status_code}")
        forecasts = client.get("/api/forecast/latest").json()
    scores = client.get("/api/risk-scores/latest").json()
    corridors = {s["corridor"] for s in scores}
    log.append(f"forecast_count={len(forecasts)} score_count={len(scores)}")
    log.append(f"corridors={sorted(corridors)}")

    cascade = client.post(
        "/api/cascade/simulate",
        json={"corridor": "MALACCA", "n_simulations": 50},
    )
    fc_after = client.post("/api/forecast/run")
    rec = client.post("/api/recommendations/run?force=true")
    log.append(f"malacca_cascade={cascade.status_code} post_cascade_forecast={fc_after.status_code}")
    log.append(f"recs={rec.status_code}")
    if cascade.status_code == 200:
        body = cascade.json()
        log.append(f"cascade_corridor={body.get('corridor')}")
        impact = body.get("price_impact_pct", {})
        log.append(
            "price_impact_pct="
            f"p10={impact.get('p10')} p50={impact.get('p50')} p90={impact.get('p90')}"
        )
    if rec.status_code == 200:
        log.append(f"rec_options={len(rec.json().get('options', []))}")

    (SCRATCH / "phase6_default_and_unrehearsed.log").write_text(
        "\n".join(log) + "\n",
        encoding="utf-8",
    )


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
    write_backend_feeds_log()
    write_default_and_unrehearsed_log()


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


def _browser_log_ok(gate_name: str, *, cold_start: bool) -> tuple[bool, str]:
    log_path = SCRATCH / f"{gate_name}_browser.log"
    run_path = SCRATCH / f"{gate_name}_run.log"
    if not log_path.exists() or log_path.stat().st_size < 50:
        return False, f"{log_path.name} missing or empty"
    if not run_path.exists() or run_path.stat().st_size < 10:
        return False, f"{run_path.name} missing or empty"
    text = log_path.read_text(encoding="utf-8", errors="replace")
    for needle in ("cape_badge=true", "forecast_populated=true", "page_errors=0"):
        if needle not in text:
            return False, f"missing {needle} in {log_path.name}"
    if cold_start and "cold_start=true" not in text:
        return False, "missing cold_start=true"
    markers_line = next((ln for ln in text.splitlines() if "map_markers=" in ln), "")
    if markers_line:
        try:
            count = int(markers_line.split("map_markers=")[1].split()[0])
            if count < 5:
                return False, f"map_markers={count}"
        except (IndexError, ValueError):
            return False, "unparseable map_markers"
    frontend_log = SCRATCH / f"{gate_name}_frontend.log"
    if frontend_log.exists():
        flog = frontend_log.read_text(encoding="utf-8", errors="replace").lower()
        if "already in use" in flog:
            return False, "frontend port conflict in log"
    return True, "ok"


def _invoke_browser_gate(gate_name: str) -> None:
    """Run one browser gate in an isolated subprocess (ephemeral ports)."""
    gate_script = ROOT / "scripts" / "phase6_browser_gate.py"
    proc = run_cmd(
        [sys.executable, str(gate_script), "--gate", gate_name],
        env={"SCRATCH_DIR": str(SCRATCH)},
        timeout=600,
    )
    run_log = SCRATCH / f"{gate_name}_run.log"
    if proc.stdout or proc.stderr:
        existing = run_log.read_text(encoding="utf-8") if run_log.exists() else ""
        run_log.write_text(existing + proc.stdout + proc.stderr, encoding="utf-8")

    cold = gate_name == "browser_cold_start"
    log_ok, log_reason = _browser_log_ok(gate_name, cold_start=cold)
    ok = proc.returncode == 0 and log_ok
    detail = f"exit={proc.returncode} log={log_reason}"
    if gate_name == "browser_check_seeded":
        detail += " internal_runs=2"
    gate(gate_name, ok, detail)


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

    if not shutil.which("npm"):
        gate("browser_cold_start", False, "npm unavailable")
        gate("browser_check_seeded", False, "npm unavailable")
        return

    _invoke_browser_gate("browser_cold_start")
    _invoke_browser_gate("browser_check_seeded")
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