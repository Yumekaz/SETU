#!/bin/sh
set -eu

SEED="/app/bundled-data"
MARKER="/data/samples/gdelt_hormuz_backtest.json"

if [ -d "$SEED" ] && [ ! -f "$MARKER" ]; then
  mkdir -p /data
  cp -r "$SEED/." /data/
fi

APP_MODULE="${SETU_APP_MODULE:-app.main_repro:app}"
exec uvicorn "$APP_MODULE" --host 0.0.0.0 --port 8000