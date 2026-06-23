#!/usr/bin/env bash
# Start SETU demo stack (Docker Compose).
set -euo pipefail
cd "$(dirname "$0")/.."

if ! docker info >/dev/null 2>&1; then
  echo "Docker not accessible. Try:"
  echo "  sudo bash scripts/fix-docker-permissions.sh"
  echo "  (log out/in) then re-run: bash scripts/demo-up.sh"
  echo "Or once: sudo docker compose up --build"
  exit 1
fi

echo "Syncing fixtures for frontend build..."
python3 scripts/generate_mocks.py

echo "Building and starting SETU..."
docker compose up --build