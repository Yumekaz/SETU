"""Daily per-corridor feature engineering via Phase 1 score replay."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from app.forecast.config import CORRIDOR_ORDER, DEFAULT_FEATURES_PATH, FEATURE_COLUMNS
from app.forecast.dataset import load_features_df
from app.forecast.prices import load_brent_daily_series
from app.models.generated import Corridor, SignalEvent
from app.signals.dedup import deduplicate_events
from app.signals.extract import extract_signal
from app.signals.ingest_gdelt import load_backtest_cache
from app.signals.score import build_risk_scores

ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_CACHE = ROOT / "data" / "samples" / "gdelt_hormuz_backtest.json"
WINDOW_START = date(2026, 2, 1)
WINDOW_END = date(2026, 6, 30)


def _fixed_ingested_at() -> datetime:
    return datetime(2026, 6, 23, 12, 0, 0, tzinfo=timezone.utc)


def extract_events_from_cache(cache_path: Path | None = None) -> list[SignalEvent]:
    rows = load_backtest_cache(cache_path or DEFAULT_CACHE)
    ingested_at = _fixed_ingested_at()
    accepted: list[SignalEvent] = []
    for row in rows:
        result = extract_signal(row, ingested_at=ingested_at)
        if result.status == "accepted" and result.event is not None:
            accepted.append(result.event)
    kept, _ = deduplicate_events(accepted)
    return kept


def build_daily_features(
    events: list[SignalEvent] | None = None,
    *,
    start: date = WINDOW_START,
    end: date = WINDOW_END,
    cache_path: Path | None = None,
) -> pd.DataFrame:
    """Replay scoring daily; return long-format features per corridor."""
    evts = events if events is not None else extract_events_from_cache(cache_path)
    brent = load_brent_daily_series(start, end)

    rows: list[dict] = []
    current = start
    while current <= end:
        prior_date = current - timedelta(days=7)
        prior_scores = {
            s.corridor: s.score
            for s in build_risk_scores(evts, score_date=prior_date)
        }
        scores = build_risk_scores(evts, score_date=current, prior_scores=prior_scores)
        score_by_corridor = {s.corridor: s for s in scores}

        ts = pd.Timestamp(current)
        brent_today = float(brent.loc[ts])
        brent_lag_ts = ts - pd.Timedelta(days=7)
        brent_lag = float(brent.loc[brent_lag_ts]) if brent_lag_ts in brent.index else brent_today
        price_lag = ((brent_today - brent_lag) / brent_lag * 100.0) if brent_lag else 0.0

        for corridor_str in CORRIDOR_ORDER:
            corridor = Corridor(corridor_str)
            day_events = [
                e
                for e in evts
                if e.corridor == corridor and e.event_date == current
            ]
            goldstein_aggregate = (
                sum(abs(e.goldstein_scale) for e in day_events) / len(day_events)
                if day_events
                else 0.0
            )
            rs = score_by_corridor[corridor]
            rows.append(
                {
                    "date": current.isoformat(),
                    "corridor": corridor_str,
                    "risk_score": float(rs.score),
                    "goldstein_aggregate": round(goldstein_aggregate, 6),
                    "event_count": len(day_events),
                    "price_lag": round(price_lag, 6),
                    "trend_7d": rs.trend_7d.value,
                }
            )
        current += timedelta(days=1)

    df = pd.DataFrame(rows)
    for col in FEATURE_COLUMNS:
        if col not in df.columns:
            raise ValueError(f"missing feature column {col}")
    return df


def write_features_parquet(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def parquet_has_all_corridors(path: Path) -> bool:
    """Return True when parquet exists and contains every CORRIDOR_ORDER entry."""
    if not path.exists():
        return False
    present = set(load_features_df(path)["corridor"].unique())
    return set(CORRIDOR_ORDER) <= present


def ensure_features_parquet(path: Path | None = None) -> None:
    """Build or rebuild daily features when missing or corridor-incomplete."""
    target = path or DEFAULT_FEATURES_PATH
    if parquet_has_all_corridors(target):
        return
    write_features_parquet(build_daily_features(), target)
