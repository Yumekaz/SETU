"""SETU FastAPI application — Phase 0 skeleton."""

from __future__ import annotations

import json
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import backtest as backtest_router
from app.routers import cascade as cascade_router
from app.routers import forecast as forecast_router
from app.routers import recommendations as recommendations_router
from app.routers import signals as signals_router

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_SCHEMAS_DIR = ROOT / "schemas"
SCHEMAS_DIR = Path(os.getenv("SCHEMAS_DIR", str(DEFAULT_SCHEMAS_DIR)))


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="SETU API",
    description="Strategic Energy Trade Uncertainty — Phase 6",
    version="0.7.0",
    lifespan=lifespan,
)

app.include_router(signals_router.router)
app.include_router(cascade_router.router)
app.include_router(forecast_router.router)
app.include_router(recommendations_router.router)
app.include_router(backtest_router.router)

cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in cors_origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str | int]:
    return {"status": "ok", "version": "0.7.0", "phase": 6}


@app.get("/api/contracts")
def get_contracts() -> dict[str, object]:
    """Serve frozen JSON schema contracts from /schemas/."""
    contracts: dict[str, object] = {}
    if not SCHEMAS_DIR.exists():
        return contracts

    for schema_file in sorted(SCHEMAS_DIR.glob("*.json")):
        with schema_file.open(encoding="utf-8") as f:
            contracts[schema_file.stem] = json.load(f)

    return contracts
