#!/usr/bin/env bash
# One-time fix for Canonical snap Docker (creates docker group + socket access).
# Run: sudo bash scripts/fix-docker-permissions.sh
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run with sudo: sudo bash scripts/fix-docker-permissions.sh"
  exit 1
fi

TARGET_USER="${SUDO_USER:-${USER}}"
if [[ "${TARGET_USER}" == "root" ]]; then
  echo "Run as: sudo bash scripts/fix-docker-permissions.sh (from your user account)"
  exit 1
fi

if ! getent group docker >/dev/null; then
  groupadd docker
  echo "Created group: docker"
fi

usermod -aG docker "${TARGET_USER}"
echo "Added ${TARGET_USER} to docker group"

if [[ -S /var/run/docker.sock ]]; then
  chown root:docker /var/run/docker.sock
  chmod 660 /var/run/docker.sock
  echo "Fixed /var/run/docker.sock permissions"
fi

if command -v snap >/dev/null && snap list docker >/dev/null 2>&1; then
  snap restart docker || true
fi

echo ""
echo "Done. LOG OUT and LOG BACK IN (or reboot), then run:"
echo "  docker ps"
echo "  cd ~/Desktop/SETU && docker compose up --build"