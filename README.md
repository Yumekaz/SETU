# SETU — Strategic Energy Trade Uncertainty

Geopolitical risk intelligence and cascade simulation for India's crude oil import corridors.

**Phase 0:** Foundations & contract freeze — no modeling logic, only plumbing.

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
cp .env.example .env   # add EIA_API_KEY for live pulls
docker compose up --build
```

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