"""SETU FastAPI application — Phase 0 skeleton."""

from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMAS_DIR = ROOT / "schemas"

app = FastAPI(
    title="SETU API",
    description="Strategic Energy Trade Uncertainty — Phase 0",
    version="0.1.0",
)

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


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str | int]:
    return {"status": "ok", "version": "0.1.0", "phase": 0}


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