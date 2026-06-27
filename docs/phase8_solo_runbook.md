# Phase 8 Solo Runbook

Every team member must run the full demo **without another person's help** (SRS §18, EC-37).

## Option A — Docker (recommended)

```bash
cd SETU
bash scripts/demo-up.sh
```

Wait for:
- Backend: http://localhost:8000/health → `{"status":"ok","version":"1.0.0","phase":8}`
- Frontend: http://localhost:5173

In a **second terminal**:

```bash
bash scripts/demo_preflight.sh
```

Must print `PREFLIGHT=PASS`.

Follow [phase8_demo_script.md](phase8_demo_script.md).

## Option B — Local dev

**Terminal 1 — backend:**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export SETU_EXTRACTOR_MODE=rules
export SETU_MC_N_SIMULATIONS=50
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Terminal 2 — frontend:**

```bash
cd frontend
npm install
npm run dev
```

Then `bash scripts/demo_preflight.sh` and open http://localhost:5173.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Dashboard bootstrap failed` | Backend down or CORS; check :8000/health |
| `PREFLIGHT=FAIL health_unreachable` | Start stack first |
| Stuck PENDING recommendation (409) | Use `?force=true` via UI scenario button (already does) |
| Map tiles 404 | Benign offline fallback; run `python3 scripts/cache_demo_tiles.py` |
| Slow first load | Cold start ~60s; wait for forecast panel to populate |

## Solo sign-off

After a successful solo run, add a row to [phase8_rehearsal_log.md](phase8_rehearsal_log.md).