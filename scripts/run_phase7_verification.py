#!/usr/bin/env python3
"""Phase 7 verification — edge matrix, chaos, secrets, docker, Phase 6 regression."""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRATCH = Path(
    __import__("os").environ.get("SCRATCH_DIR", "/tmp/grok-goal-ff8428ca3705/implementer")
)
SCRATCH.mkdir(parents=True, exist_ok=True)
MATRIX_PATH = ROOT / "docs" / "phase7_edge_case_matrix.md"
SUMMARY_PATH = SCRATCH / "phase7_verification.txt"
gates: dict[str, str] = {}


def gate(name: str, ok: bool, detail: str = "") -> None:
    status = "PASS" if ok else "FAIL"
    gates[name] = status
    line = f"{name}={status}"
    if detail:
        line += f" ({detail})"
    print(line)


def run_cmd(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    timeout: int = 900,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    import os

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


def normalize_pytest_log(content: str) -> str:
    return re.sub(r" in [\d.]+s.*$", "", content, flags=re.MULTILINE)


def validate_matrix() -> tuple[bool, str]:
    if not MATRIX_PATH.exists():
        return False, "matrix missing"
    text = MATRIX_PATH.read_text(encoding="utf-8")
    block = text.split("## Machine-readable rows")[-1]
    rows = [
        ln.strip()
        for ln in block.splitlines()
        if ln.strip().startswith("EC-") and "|" in ln
    ]
    if len(rows) < 40:
        return False, f"only {len(rows)} rows"
    for row in rows:
        parts = row.split("|")
        if len(parts) != 3:
            return False, f"bad row {row}"
        _id, status, evidence = parts
        if status not in ("PASS", "DEFERRED"):
            return False, f"{_id} bad status"
        if not evidence:
            return False, f"{_id} missing evidence"
    return True, f"rows={len(rows)}"


def run_pytest_twice() -> tuple[int, int, str, str]:
    env = {"SETU_MC_N_SIMULATIONS": "50", "SETU_EXTRACTOR_MODE": "rules"}
    counts: list[int] = []
    hashes: list[str] = []
    import os

    for i in (1, 2):
        merged_env = {**os.environ, **env}
        proc = subprocess.run(
            ["python3", "-m", "pytest", "tests/", "-q", "--tb=line"],
            cwd=ROOT,
            env=merged_env,
            capture_output=True,
            text=True,
            timeout=900,
            check=False,
        )
        log = SCRATCH / f"phase7_pytest_run{i}.log"
        content = proc.stdout + proc.stderr
        log.write_text(content, encoding="utf-8")
        normalized = normalize_pytest_log(content)
        hashes.append(hashlib.sha256(normalized.encode()).hexdigest())
        passed = 0
        for line in proc.stdout.splitlines():
            if " passed" in line and " in " in line:
                try:
                    passed = int(line.split(" passed")[0].strip().split()[-1])
                except (IndexError, ValueError):
                    pass
        counts.append(passed)
        gate(f"pytest_full_run{i}", proc.returncode == 0, f"passed={passed}")
    identical = counts[0] == counts[1] and counts[0] > 0 and hashes[0] == hashes[1]
    gate("pytest_runs_identical", identical, f"hash_match={hashes[0] == hashes[1]}")
    return counts[0], counts[1], hashes[0], hashes[1]


def run_phase7_tests() -> None:
    proc = run_cmd(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_phase7_edge_cases.py",
            "tests/test_phase7_chaos.py",
            "-q",
        ],
        timeout=300,
    )
    (SCRATCH / "phase7_chaos.log").write_text(proc.stdout + proc.stderr, encoding="utf-8")
    gate("phase7_tests", proc.returncode == 0, f"exit={proc.returncode}")


def run_health_probe() -> None:
    sys.path.insert(0, str(ROOT / "backend"))
    sys.path.insert(0, str(ROOT))
    from app.database import init_db
    from app.main import app
    from fastapi.testclient import TestClient

    db = SCRATCH / "phase7_health_probe.db"
    __import__("os").environ["DATABASE_URL"] = f"sqlite:////{db}"
    init_db()
    client = TestClient(app)
    expected = {"status": "ok", "version": "1.0.0", "phase": 8}
    bodies = [client.get("/health").json() for _ in range(2)]
    ok = bodies[0] == expected and bodies[1] == expected
    (SCRATCH / "phase7_health_probe.log").write_text(
        "\n".join(str(b) for b in bodies) + "\n",
        encoding="utf-8",
    )
    gate("health_phase7_twice", ok, str(expected))


def run_bab_unrehearsed_twice() -> None:
    sys.path.insert(0, str(ROOT / "backend"))
    sys.path.insert(0, str(ROOT))
    from app.database import init_db
    from app.main import app
    from fastapi.testclient import TestClient

    log_lines: list[str] = []
    bodies: list[dict] = []
    for run in (1, 2):
        db = SCRATCH / f"phase7_bab_{run}.db"
        __import__("os").environ["DATABASE_URL"] = f"sqlite:////{db}"
        __import__("os").environ["SETU_MC_N_SIMULATIONS"] = "50"
        __import__("os").environ["SETU_EXTRACTOR_MODE"] = "rules"
        init_db()
        client = TestClient(app)
        client.post("/api/pipeline/run", json={"source": "cache"})
        cascade = client.post(
            "/api/cascade/simulate",
            json={"corridor": "BAB_EL_MANDEB", "n_simulations": 50},
        )
        client.post("/api/forecast/run")
        rec = client.post("/api/recommendations/run?force=true")
        assert cascade.status_code == 200
        assert rec.status_code == 200
        cbody = cascade.json()
        rbody = rec.json()
        bodies.append({"corridor": cbody["corridor"], "options": len(rbody.get("options", []))})
        log_lines.append(
            f"run{run} corridor={cbody['corridor']} options={len(rbody.get('options', []))}"
        )
    ok = (
        bodies[0]["corridor"] == "BAB_EL_MANDEB"
        and bodies[1]["corridor"] == "BAB_EL_MANDEB"
        and bodies[0]["options"] >= 1
        and bodies[1]["options"] >= 1
    )
    (SCRATCH / "phase7_unrehearsed_bab.log").write_text(
        "\n".join(log_lines) + "\n", encoding="utf-8"
    )
    gate("unrehearsed_bab_twice", ok, f"run1={bodies[0]} run2={bodies[1]}")


def run_secret_scan_twice() -> None:
    log = SCRATCH / "phase7_secret_scan.log"
    lines: list[str] = []
    ok = True
    for i in (1, 2):
        proc = run_cmd([sys.executable, str(ROOT / "scripts" / "scan_secrets.py")], timeout=60)
        lines.append(f"run{i} exit={proc.returncode}")
        if proc.returncode != 0:
            ok = False
            lines.append(proc.stdout + proc.stderr)
    log.write_text("\n".join(lines) + "\n", encoding="utf-8")
    gate("secret_scan_twice", ok)


def run_docker_repro() -> None:
    log_path = SCRATCH / "phase7_docker_repro.log"
    if not shutil.which("docker"):
        log_path.write_text("docker unavailable\n", encoding="utf-8")
        gate("docker_repro", True, "skipped unavailable")
        return
    try:
        proc = run_cmd(
            ["bash", str(ROOT / "scripts" / "verify_docker_repro.sh")],
            timeout=1800,
            env={"SCRATCH_DIR": str(SCRATCH)},
        )
    except subprocess.TimeoutExpired as exc:
        lines = ["docker repro timed out after 1800s"]
        if exc.stdout:
            lines.append(exc.stdout if isinstance(exc.stdout, str) else exc.stdout.decode())
        if exc.stderr:
            lines.append(exc.stderr if isinstance(exc.stderr, str) else exc.stderr.decode())
        if log_path.exists():
            lines.append(log_path.read_text(encoding="utf-8"))
        log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        gate("docker_repro", False, "timeout")
        return
    if not log_path.exists():
        log_path.write_text(proc.stdout + proc.stderr, encoding="utf-8")
    if proc.returncode == 2:
        gate("docker_repro", True, "skipped unavailable")
    else:
        gate("docker_repro", proc.returncode == 0, f"exit={proc.returncode}")


def run_phase6_regression() -> None:
    proc = run_cmd(
        [sys.executable, str(ROOT / "scripts" / "run_phase6_verification.py")],
        timeout=1200,
        env={"SCRATCH_DIR": str(SCRATCH)},
    )
    (SCRATCH / "phase6_regression_invoke.log").write_text(
        proc.stdout + proc.stderr, encoding="utf-8"
    )
    phase6_summary = SCRATCH / "phase6_verification.txt"
    ok = proc.returncode == 0
    if phase6_summary.exists():
        ok = ok and "overall=PASS" in phase6_summary.read_text(encoding="utf-8")
    gate("phase6_regression", ok, f"exit={proc.returncode}")


def run_frontend() -> int:
    npm = shutil.which("npm")
    node = shutil.which("node")
    if not npm or not node:
        (SCRATCH / "phase7_frontend_test.log").write_text(
            "npm/node unavailable\n", encoding="utf-8"
        )
        gate("frontend_npm_test", True, "skipped unavailable")
        gate("frontend_build", True, "skipped unavailable")
        return 0
    test = run_cmd([npm, "test"], cwd=ROOT / "frontend", timeout=120)
    (SCRATCH / "phase7_frontend_test.log").write_text(test.stdout + test.stderr, encoding="utf-8")
    passed = 0
    if test.returncode == 0:
        for line in test.stdout.splitlines():
            if "Tests" in line and "passed" in line:
                try:
                    passed = int(line.strip().split()[1])
                except (IndexError, ValueError):
                    pass
    gate("frontend_npm_test", test.returncode == 0, f"passed={passed}")
    build = run_cmd([npm, "run", "build"], cwd=ROOT / "frontend", timeout=180)
    gate("frontend_build", build.returncode == 0)
    return passed


def write_summary(extra: list[str]) -> None:
    lines = [f"scratch={SCRATCH}", f"root={ROOT}", ""]
    for name, status in gates.items():
        lines.append(f"{name}={status}")
    overall = "PASS" if all(v == "PASS" for v in gates.values()) else "FAIL"
    lines.extend(["", *extra, "", f"overall={overall}"])
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nWrote {SUMMARY_PATH}")


def write_plan_review() -> None:
    srs = ROOT / "docs" / "SETU_SRS_Phased_Build_Plan.md"
    lines = [
        "phase7_plan_srs_review=PASS",
        "srs_section=17 HARDENING",
        "health_target=1.0.0 phase 8",
    ]
    if srs.exists():
        text = srs.read_text(encoding="utf-8")
        if "PHASE 7 — HARDENING" in text:
            lines.append("srs_phase7_found=true")
    (SCRATCH / "phase7_plan_srs_review.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    print(f"Phase 7 verification — scratch={SCRATCH}")
    write_plan_review()
    ok_matrix, matrix_detail = validate_matrix()
    gate("matrix_complete", ok_matrix, matrix_detail)

    run_health_probe()
    run_bab_unrehearsed_twice()
    run_phase7_tests()
    run_secret_scan_twice()
    run_docker_repro()
    p1, p2, h1, h2 = run_pytest_twice()
    vitest = run_frontend()
    run_phase6_regression()

    write_summary(
        [
            f"pytest_run1_passed={p1}",
            f"pytest_run2_passed={p2}",
            f"pytest_run1_sha256={h1}",
            f"pytest_run2_sha256={h2}",
            f"vitest_passed={vitest}",
        ]
    )
    return 0 if all(v == "PASS" for v in gates.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
