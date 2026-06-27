#!/usr/bin/env bash
# Zero-manual Docker repro: no .env copy required for demo path.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRATCH="${SCRATCH_DIR:-/tmp/grok-goal-ff8428ca3705/implementer}"
LOG="$SCRATCH/phase7_docker_repro.log"
mkdir -p "$SCRATCH"
exec > >(tee -a "$LOG") 2>&1

echo "=== phase7 docker repro start $(date -Iseconds) ==="
cd "$ROOT"

if ! docker info >/dev/null 2>&1; then
  echo "DOCKER_UNAVAILABLE=true"
  exit 2
fi

python3 scripts/generate_mocks.py
COMPOSE_FILE="docker-compose.repro.yml"
export DOCKER_BUILDKIT=1
docker compose -f "$COMPOSE_FILE" down -v --remove-orphans 2>/dev/null || true
if [[ "${SKIP_DOCKER_BUILD:-0}" != "1" ]]; then
  docker compose -f "$COMPOSE_FILE" build backend
fi
docker compose -f "$COMPOSE_FILE" up -d backend

deadline=$((SECONDS + 180))
health_ok=false
while (( SECONDS < deadline )); do
  if curl -sf http://127.0.0.1:8000/health | grep -qE '"phase":\s*8'; then
    health_ok=true
    break
  fi
  sleep 2
done

if ! $health_ok; then
  echo "FAIL=health timeout"
  docker compose -f "$COMPOSE_FILE" logs --tail=50 backend
  docker compose -f "$COMPOSE_FILE" down -v --remove-orphans
  exit 1
fi

curl -sf http://127.0.0.1:8000/health
echo ""

pipe_code=$(curl -sf -o /tmp/setu_pipe.json -w "%{http_code}" \
  -X POST http://127.0.0.1:8000/api/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{"source":"cache"}')
echo "pipeline_status=$pipe_code"

scores=$(curl -sf http://127.0.0.1:8000/api/risk-scores/latest)
score_count=$(python3 -c "import json,sys; print(len(json.load(sys.stdin)))" <<<"$scores")
echo "score_count=$score_count"
corridors=$(python3 -c "import json,sys; d=json.load(sys.stdin); print(sorted({x['corridor'] for x in d}))" <<<"$scores")
echo "corridors=$corridors"

docker compose -f "$COMPOSE_FILE" down -v --remove-orphans

if [[ "$pipe_code" != "200" ]] || [[ "$score_count" -lt 3 ]]; then
  echo "FAIL=demo state not reached"
  exit 1
fi

echo "PASS=docker repro ok"
exit 0