# SETU Data Sources — Phase 0

Real sample pulls are cached in `/data/samples/` via `scripts/pull_samples.py`.

| Source | Access | API Key | Sample file | Notes |
|--------|--------|---------|-------------|-------|
| **GDELT** | Direct HTTP download | No | `gdelt_events_sample.json` | Events 2.0 daily export CSV from `http://data.gdeltproject.org/events/` |
| **OFAC SDN** | Direct HTTP download | No | `ofac_sdn_sample.json` | Treasury CSV at `https://www.treasury.gov/ofac/downloads/sdn.csv` |
| **EIA** | Open Data API v2 | Yes (`EIA_API_KEY`) | `eia_brent_sample.json` | Live pull when key set; else documented fallback matching v2 shape |
| **FRED** | API or public CSV | Optional (`FRED_API_KEY`) | `fred_brent_sample.json` | Public CSV at `fredgraph.csv?id=DCOILBRENTEU` works without key |

## GDELT

- **Provider:** GDELT Project (public, free)
- **Endpoint:** `http://data.gdeltproject.org/events/YYYYMMDD.export.CSV.zip`
- **Fields used (Phase 1+):** `GLOBALEVENTID`, `EventCode`, `GoldsteinScale`, `ActionGeo_*`, `SOURCEURL`, `SQLDATE`
- **Rate limits:** None documented for direct file download; cache locally after first pull
- **VERIFY:** Confirm latest export date availability on day 1 — file lag is typically 15 minutes to 1 day

## OFAC

- **Provider:** US Treasury Office of Foreign Assets Control
- **Endpoint:** `https://www.treasury.gov/ofac/downloads/sdn.csv`
- **Fields:** Entity number, SDN name, program, vessel metadata
- **Rate limits:** None for public CSV; file updates on sanctions list changes
- **Use in SETU:** Sanctions-adjacent `SignalEvent` type filtering (Phase 1)

## EIA

- **Provider:** US Energy Information Administration
- **API docs:** https://www.eia.gov/opendata/
- **Key series:** `RBRTE` — Brent spot price (daily)
- **Registration:** Free API key at https://www.eia.gov/opendata/register.php
- **Fallback:** If `EIA_API_KEY` is unset, `pull_samples.py` writes a minimal valid v2 response documenting expected shape

## FRED

- **Provider:** Federal Reserve Bank of St. Louis
- **Series:** `DCOILBRENTEU` — Europe Brent Spot Price FOB
- **API docs:** https://fred.stlouisfed.org/docs/api/fred/
- **Public CSV (no key):** `https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILBRENTEU`
- **Fallback:** API JSON shape sample if both API key and CSV pull fail

## Pulling samples

```bash
# Optional: add keys to .env for live EIA/FRED API pulls
cp .env.example .env

python scripts/pull_samples.py
```

Output wrapper format:

```json
{
  "pulled_at": "ISO-8601 UTC",
  "source": { "provider": "...", "url": "...", "live": true },
  "data": { }
}
```

## Hormuz 2026 backtest timeline

Curated event rows in `/data/hormuz_2026_timeline.csv` — cited sources for Phase 5 backtest harness. URLs are reference anchors; verify against live GDELT ingest before modeling.