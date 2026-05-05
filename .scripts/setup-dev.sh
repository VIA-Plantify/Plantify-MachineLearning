#!/usr/bin/env bash
set -Eeuo pipefail

NETWORK="plantify-network"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$PROJECT_ROOT"

echo "Project root: $PROJECT_ROOT"

echo "Checking Docker..."
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  if ! docker network inspect "$NETWORK" >/dev/null 2>&1; then
    echo "Creating Docker network: $NETWORK"
    docker network create --driver bridge "$NETWORK"
  else
    echo "Docker network already exists: $NETWORK"
  fi

  echo "Base Docker setup complete."
else
  echo "Docker not available, skipping Docker network setup."
fi

echo "Checking uv..."
uv --version

echo "Syncing Python environment..."
uv sync

echo "Starting grpc initialization..."

bash /workspace/.scripts/compile-grpc.sh

echo "Dev setup complete."