# SETU Data Sources — Phase 0

Real sample pulls are cached in `/data/samples/` via `scripts/pull_samples.py`.
Each source is isolated — a failure in one does not block others.

| Source | Access | API Key | Sample file | Notes |
|--------|--------|---------|-------------|-------|
| **GDELT** | Direct HTTP download | No | `gdelt_events_sample.json` | GDELT 2.0 via `gdeltv2/lastupdate.txt`; fallback if unreachable |
| **OFAC SDN** | Direct HTTP download | No | `ofac_sdn_sample.json` | Treasury CSV; documented fallback if unreachable |
| **EIA Brent** | Open Data API v2 | Yes (`EIA_API_KEY`) | `eia_brent_sample.json` | Live pull when key set; else documented fallback |
| **EIA India imports** | Open Data API v2 | Yes (`EIA_API_KEY`) | `eia_india_imports_sample.json` | VERIFY series IDs; fallback documents v2 shape |
| **FRED** | API or public CSV | Optional (`FRED_API_KEY`) | `fred_brent_sample.json` | Public CSV works without key |

## GDELT

- **Provider:** GDELT Project (public, free)
- **Primary endpoint:** `http://data.gdeltproject.org/gdeltv2/lastupdate.txt` → latest `*.export.CSV.zip`
- **Legacy (deprecated):** `http://data.gdeltproject.org/events/YYYYMMDD.export.CSV.zip`
- **Fields used (Phase 1+):** `GLOBALEVENTID`, `EventCode`, `GoldsteinScale`, `ActionGeo_*`, `SOURCEURL`, `SQLDATE`
- **Meta flag:** `source.live` — `true` when a real export was downloaded

## OFAC

- **Provider:** US Treasury Office of Foreign Assets Control
- **Endpoint:** `https://www.treasury.gov/ofac/downloads/sdn.csv`
- **Fallback:** Documented SDN row shape if CSV unreachable
- **Use in SETU:** Sanctions-adjacent `SignalEvent` type filtering (Phase 1)

## EIA

- **Provider:** US Energy Information Administration
- **API docs:** https://www.eia.gov/opendata/
- **Brent series:** `RBRTE` — `/v2/petroleum/pri/spt/data/`
- **India imports:** `/v2/international/data/` with `countryRegionId=IND` — **VERIFY** `productId` against live catalog
- **Registration:** Free API key at https://www.eia.gov/opendata/register.php
- **Fallback:** If `EIA_API_KEY` is unset, both Brent and India import samples document expected v2 response shapes

## FRED

- **Provider:** Federal Reserve Bank of St. Louis
- **Series:** `DCOILBRENTEU` — Europe Brent Spot Price FOB
- **Public CSV (no key):** `https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILBRENTEU`
- **Fallback:** API JSON shape sample if both API key and CSV pull fail

## Pulling samples

```bash
cp .env.example .env   # optional: EIA_API_KEY, FRED_API_KEY
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

Curated event rows in `/data/hormuz_2026_timeline.csv`.

Columns: `date`, `event_type`, `description`, `source_url`, `brent_usd`, `notes`