#!/bin/sh
set -eu

SEED="/app/bundled-data"
MARKER="/data/samples/gdelt_hormuz_backtest.json"

if [ -d "$SEED" ] && [ ! -f "$MARKER" ]; then
  mkdir -p /data
  cp -r "$SEED/." /data/
fi

# Keep versioned reference assets current across image upgrades. The named
# /data volume deliberately preserves operational state (including SQLite),
# but replay configuration and committed evidence caches must come from the
# image that is actually being run.
if [ -d "$SEED" ]; then
  mkdir -p /data/config /data/graph /data/samples
  cp -r "$SEED/config/." /data/config/
  cp -r "$SEED/graph/." /data/graph/
  cp -r "$SEED/samples/." /data/samples/
  cp "$SEED/hormuz_2026_timeline.csv" /data/hormuz_2026_timeline.csv
fi

APP_MODULE="${SETU_APP_MODULE:-app.main_repro:app}"
exec uvicorn "$APP_MODULE" --host 0.0.0.0 --port 8000
