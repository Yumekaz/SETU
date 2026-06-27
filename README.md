# SETU — Strategic Energy Trade Uncertainty

Geopolitical risk intelligence and cascade simulation for India's crude oil import corridors.

**Phase 8 (submission):** `version: 1.0.0`, `phase: 8` — demo-ready for GitHub + video.

## Quick Start (Docker)

**Ubuntu Snap Docker:** the `docker` group may not exist. One-time fix:

```bash
sudo bash scripts/fix-docker-permissions.sh
# log out and back in, then:
bash scripts/demo-up.sh
```

Or skip the fix and use sudo: `sudo docker compose up --build`

```bash
cd SETU
docker compose up --build
```

No `.env` file is required for the demo path — the stack uses cached offline data and `SETU_EXTRACTOR_MODE=rules` by default. Copy `.env.example` to `.env` only when you need live EIA/FRED pulls.

Automated zero-manual repro check (backend pipeline + health, no `.env` copy):

```bash
bash scripts/verify_docker_repro.sh
```

## Submission / Demo

Before recording your video or presenting live:

```bash
bash scripts/demo_preflight.sh          # PREFLIGHT=PASS required
python3 scripts/run_phase8_verification.py
```

| Doc | Purpose |
|-----|---------|
| [docs/phase8_demo_script.md](docs/phase8_demo_script.md) | Timed live + video script |
| [docs/phase8_solo_runbook.md](docs/phase8_solo_runbook.md) | One-person demo steps |
| [docs/submission/README.md](docs/submission/README.md) | Upload checklist |
| [docs/submission/video_outline.md](docs/submission/video_outline.md) | 5–8 min recording guide |

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **Health check:** http://localhost:8000/health
- **Contracts:** http://localhost:8000/api/contracts

## Local Development (without Docker)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Code generation (schemas → types)

```bash
python scripts/generate_models.py
```

### Pull real data samples

```bash
python scripts/pull_samples.py
```

### Generate mock fixtures

```bash
python scripts/generate_mocks.py
```

### Tests

```bash
pytest tests/ -v
```

## Repository Layout

```
SETU/
├── backend/          # FastAPI skeleton
├── frontend/         # React + Vite + Tailwind
├── schemas/          # JSON Schema (draft-07) — single source of truth
├── scripts/          # Codegen, data pulls, mock generation
├── data/             # SQLite DB, samples, fixtures, timeline CSV
├── docs/             # SRS, brief, data sources, phase sign-off
├── tests/            # Schema + health tests
└── ml/               # Reserved for Phase 3+
```

## Data Contracts

Frozen JSON schemas in `/schemas/` per SETU SRS Section 6:

| Contract | Schema file |
|----------|-------------|
| SignalEvent | `signal_event.json` |
| RiskScore | `risk_score.json` |
| CascadeResult | `cascade_result.json` |
| GraphNode / GraphEdge | `graph_node.json`, `graph_edge.json` |
| Recommendation | `recommendation.json` |

Shared enums: `corridor.json`, `percentile_band.json`

Generated types:
- Backend: `backend/app/models/generated.py` (Pydantic via datamodel-code-generator)
- Frontend: `frontend/src/types/generated.ts`

## Phase 0 Acceptance

See [docs/phase0_signoff.md](docs/phase0_signoff.md) for acceptance criteria evidence.