#!/usr/bin/env python3
"""Phase 8 verification — submission docs, demo path, Phase 7 regression."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRATCH = Path(
    __import__("os").environ.get("SCRATCH_DIR", "/tmp/grok-goal-ff8428ca3705/implementer")
)
SCRATCH.mkdir(parents=True, exist_ok=True)
SUMMARY_PATH = SCRATCH / "phase8_verification.txt"
gates: dict[str, str] = {}

REQUIRED_DOCS = [
    ROOT / "docs" / "phase8_submission_verify.md",
    ROOT / "docs" / "phase8_demo_script.md",
    ROOT / "docs" / "phase8_qa_playbook.md",
    ROOT / "docs" / "phase8_solo_runbook.md",
    ROOT / "docs" / "phase8_venue_checklist.md",
    ROOT / "docs" / "phase8_architecture.md",
    ROOT / "docs" / "phase8_rehearsal_log.md",
    ROOT / "docs" / "submission" / "README.md",
    ROOT / "docs" / "submission" / "repo_hygiene.md",
    ROOT / "docs" / "submission" / "video_outline.md",
]

DEMO_SCRIPT_MARKERS = ("Time budget", "Short", "Baseline dashboard")


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
    timeout: int = 900,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    import os

    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        cmd,
        cwd=ROOT,
        env=merged,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def check_docs() -> None:
    missing = [p for p in REQUIRED_DOCS if not p.exists()]
    gate("phase8_docs_present", not missing, f"missing={len(missing)}")
    demo = ROOT / "docs" / "phase8_demo_script.md"
    ok_markers = demo.exists() and all(
        marker in demo.read_text(encoding="utf-8") for marker in DEMO_SCRIPT_MARKERS
    )
    gate("demo_script_markers", ok_markers)


def check_submission_verify() -> None:
    path = ROOT / "docs" / "phase8_submission_verify.md"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    confirmed = "confirmed_on=" in text and "PENDING" not in text.split("confirmed_on=")[-1][:40]
    detail = "confirmed" if confirmed else "still_pending"
    gate("submission_verify_doc", path.exists() and confirmed, detail)


def check_rehearsal_log() -> None:
    path = ROOT / "docs" / "phase8_rehearsal_log.md"
    if not path.exists():
        gate("rehearsal_log", False, "missing")
        return
    text = path.read_text(encoding="utf-8")
    rows = [
        ln
        for ln in text.splitlines()
        if ln.strip().startswith("|")
        and "---" not in ln
        and "Date" not in ln
        and "PENDING" not in ln.upper()
    ]
    completed_full = [
        ln for ln in rows
        if "| full |" in ln.lower() and "| automated |" not in ln.lower()
    ]
    gate(
        "rehearsal_log",
        len(completed_full) >= 3,
        f"completed_full_human_runs={len(completed_full)}",
    )


def run_phase8_tests() -> None:
    proc = run_cmd(
        [sys.executable, "-m", "pytest", "tests/test_phase8_api.py", "-q", "--tb=line"],
        timeout=120,
        env={"SETU_MC_N_SIMULATIONS": "50", "SETU_EXTRACTOR_MODE": "rules"},
    )
    (SCRATCH / "phase8_api_pytest.log").write_text(proc.stdout + proc.stderr, encoding="utf-8")
    gate("phase8_api_tests", proc.returncode == 0)


def run_demo_preflight_probe() -> None:
    """In-process demo path (no live server required)."""
    sys.path.insert(0, str(ROOT / "backend"))
    sys.path.insert(0, str(ROOT))
    import os

    db = SCRATCH / "phase8_preflight_probe.db"
    os.environ["DATABASE_URL"] = f"sqlite:////{db}"
    os.environ["SETU_MC_N_SIMULATIONS"] = "50"
    os.environ["SETU_EXTRACTOR_MODE"] = "rules"
    from app.database import init_db
    from app.main import app
    from fastapi.testclient import TestClient

    init_db()
    client = TestClient(app)
    expected = {"status": "ok", "version": "1.0.0", "phase": 8}
    lines: list[str] = []
    ok = client.get("/health").json() == expected
    lines.append(f"health={ok}")
    if ok:
        client.post("/api/pipeline/run", json={"source": "cache"})
        cas = client.post(
            "/api/cascade/simulate",
            json={"corridor": "MALACCA", "n_simulations": 50},
        )
        client.post("/api/forecast/run")
        rec = client.post("/api/recommendations/run?force=true")
        ok = (
            cas.status_code == 200
            and rec.status_code == 200
            and len(rec.json().get("options", [])) >= 1
        )
        lines.append(f"demo_path={ok}")
    (SCRATCH / "phase8_preflight_probe.log").write_text("\n".join(lines) + "\n", encoding="utf-8")
    gate("demo_preflight_probe", ok)


def run_secret_scan() -> None:
    proc = run_cmd([sys.executable, str(ROOT / "scripts" / "scan_secrets.py")], timeout=60)
    gate("secret_scan", proc.returncode == 0)


def run_phase7_regression() -> None:
    proc = run_cmd(
        [sys.executable, str(ROOT / "scripts" / "run_phase7_verification.py")],
        timeout=1800,
        env={"SCRATCH_DIR": str(SCRATCH / "phase7_regression")},
    )
    (SCRATCH / "phase7_regression_invoke.log").write_text(
        proc.stdout + proc.stderr, encoding="utf-8"
    )
    summary = SCRATCH / "phase7_regression" / "phase7_verification.txt"
    ok = proc.returncode == 0
    if summary.exists():
        ok = ok and "overall=PASS" in summary.read_text(encoding="utf-8")
    gate("phase7_regression", ok, f"exit={proc.returncode}")


def run_browser_if_available() -> None:
    npm = shutil.which("npm")
    node = shutil.which("node")
    npx = shutil.which("npx")
    if not npm or not node or not npx:
        (SCRATCH / "phase8_browser.log").write_text("npm/node/npx unavailable\n", encoding="utf-8")
        gate("browser_demo_path", True, "skipped unavailable")
        return
    proc = run_cmd(
        ["node", str(ROOT / "scripts" / "phase6_browser_check.mjs")],
        timeout=300,
        env={"SCRATCH_DIR": str(SCRATCH), "SETU_GATE_NAME": "phase8"},
    )
    (SCRATCH / "phase8_browser.log").write_text(proc.stdout + proc.stderr, encoding="utf-8")
    gate("browser_demo_path", proc.returncode == 0, f"exit={proc.returncode}")


def write_summary() -> None:
    lines = [f"scratch={SCRATCH}", f"root={ROOT}", ""]
    for name, status in gates.items():
        lines.append(f"{name}={status}")
    lines.append("")
    lines.append(f"overall={'PASS' if all(v == 'PASS' for v in gates.values()) else 'FAIL'}")
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nWrote {SUMMARY_PATH}")


def main() -> int:
    print(f"Phase 8 verification — scratch={SCRATCH}")
    check_docs()
    check_submission_verify()
    check_rehearsal_log()
    run_secret_scan()
    run_phase8_tests()
    run_demo_preflight_probe()
    run_phase7_regression()
    run_browser_if_available()
    write_summary()
    return 0 if all(v == "PASS" for v in gates.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
