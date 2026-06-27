# Phase 8 Sign-Off — Submission & Demo

**Health:** `phase: 8`, `version: 1.0.0`

## Deliverables

| Item | Location |
|------|----------|
| Submission VERIFY | `docs/phase8_submission_verify.md` |
| Demo script (full + short) | `docs/phase8_demo_script.md` |
| Q&A playbook | `docs/phase8_qa_playbook.md` |
| Solo runbook | `docs/phase8_solo_runbook.md` |
| Venue checklist | `docs/phase8_venue_checklist.md` |
| Architecture summary | `docs/phase8_architecture.md` |
| Submission pack | `docs/submission/` |
| Demo preflight | `scripts/demo_preflight.sh` |
| Verification harness | `scripts/run_phase8_verification.py` |
| Demo API tests | `tests/test_phase8_api.py` |

## SRS §18 AC reconciliation

| Criterion | Met | Notes |
|-----------|-----|-------|
| Submission package matches verified format | Partial | VERIFY doc template; fill on portal check |
| Demo rehearsed ≥3 times, timed | Partial | Log template + 1 automated row; team fills live runs |
| Every member runs solo | Partial | Runbook ready; per-person log rows pending |

## Video

Recorded by team — outline at `docs/submission/video_outline.md`. Paste URL in `docs/submission/README.md`.

## Verification evidence (2026-06-26)

| Gate | Result |
|------|--------|
| `run_phase8_verification.py` ×2 | `overall=PASS` |
| Full pytest | 177 passed |
| Demo preflight probe | PASS |
| Phase 7 regression | PASS |

Evidence: `/tmp/grok-goal-phase8/phase8_verification.txt`

## Regression

Phase 7 harness invoked from `run_phase8_verification.py`.