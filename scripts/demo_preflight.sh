#!/usr/bin/env bash
# Pre-demo checks: secrets scan + API health + demo path probes.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API="${SETU_API_URL:-http://127.0.0.1:8000}"
FAIL=0

cd "$ROOT"

echo "=== SETU demo preflight $(date -Iseconds) ==="

echo "[1/4] Secret scan"
if ! python3 scripts/scan_secrets.py; then
  echo "FAIL=secret_scan"
  FAIL=1
fi

echo "[2/4] Health probe ($API)"
health="$(curl -sf "$API/health" 2>/dev/null || true)"
if [[ -z "$health" ]]; then
  echo "FAIL=health_unreachable (start stack: bash scripts/demo-up.sh)"
  FAIL=1
elif ! python3 -c "import json,sys; d=json.loads(sys.argv[1]); sys.exit(0 if d=={'status':'ok','version':'1.0.0','phase':8} else 1)" "$health"; then
  echo "FAIL=health_bad body=$health"
  FAIL=1
else
  echo "health=$health"
fi

if [[ "$FAIL" -eq 0 ]]; then
  echo "[3/4] Pipeline"
  pipe_code=$(curl -sf -o /tmp/setu_preflight_pipe.json -w "%{http_code}" \
    -X POST "$API/api/pipeline/run" \
    -H "Content-Type: application/json" \
    -d '{"source":"cache"}' || echo "000")
  if [[ "$pipe_code" != "200" ]]; then
    echo "FAIL=pipeline status=$pipe_code"
    FAIL=1
  fi

  echo "[4/4] Demo path (cascade + forecast + recommendations)"
  cas_code=$(curl -sf -o /tmp/setu_preflight_cascade.json -w "%{http_code}" \
    -X POST "$API/api/cascade/simulate" \
    -H "Content-Type: application/json" \
    -d '{"corridor":"MALACCA","n_simulations":50}' || echo "000")
  fc_code=$(curl -sf -o /dev/null -w "%{http_code}" -X POST "$API/api/forecast/run" || echo "000")
  rec_code=$(curl -sf -o /tmp/setu_preflight_rec.json -w "%{http_code}" \
    -X POST "$API/api/recommendations/run?force=true" || echo "000")
  if [[ "$cas_code" != "200" ]] || [[ "$fc_code" != "200" ]] || [[ "$rec_code" != "200" ]]; then
    echo "FAIL=demo_path cascade=$cas_code forecast=$fc_code rec=$rec_code"
    FAIL=1
  else
    opts=$(python3 -c "import json; print(len(json.load(open('/tmp/setu_preflight_rec.json')).get('options',[])))")
    echo "demo_options=$opts"
    if [[ "$opts" -lt 1 ]]; then
      echo "FAIL=no_recommendation_options"
      FAIL=1
    fi
  fi
fi

if [[ "$FAIL" -eq 0 ]]; then
  echo "PREFLIGHT=PASS"
  exit 0
fi
echo "PREFLIGHT=FAIL"
exit 1