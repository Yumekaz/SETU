# Public Repo Hygiene

## Secrets

```bash
python3 scripts/scan_secrets.py
```

Must exit 0. Scans `git ls-files` only.

## Never commit

- `.env` (use `.env.example` as template)
- API keys, tokens, local `.db` with private data
- Large model weights (`.gguf`)

## Clone-to-demo (judge path)

```bash
git clone <repo-url> SETU && cd SETU
bash scripts/demo-up.sh
# second terminal:
bash scripts/demo_preflight.sh
```

Open http://localhost:5173

No `.env` required for demo path.

## CI / verification

```bash
SCRATCH_DIR=/tmp/setu-verify python3 scripts/run_phase8_verification.py
```