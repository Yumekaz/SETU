# Submission Package Checklist

## Required (working assumption until portal VERIFY)

- [ ] Public GitHub repo URL: `PENDING — paste before upload`
- [ ] Demo video URL: `PENDING — record using video_outline.md`
- [ ] README clone-to-demo steps verified on clean machine
- [ ] `bash scripts/demo_preflight.sh` → `PREFLIGHT=PASS`
- [ ] `python3 scripts/run_phase8_verification.py` → `overall=PASS`

## Optional (if portal requires)

- [ ] Slide deck from [deck_outline.md](deck_outline.md)
- [ ] Trimmed architecture: [../phase8_architecture.md](../phase8_architecture.md)

## Before upload

1. Complete [../phase8_submission_verify.md](../phase8_submission_verify.md)
2. Run secret scan: `python3 scripts/scan_secrets.py`
3. Confirm no `.env` committed (see [repo_hygiene.md](repo_hygiene.md))