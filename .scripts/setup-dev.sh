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

# uv install
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi

export PATH="$HOME/.local/bin:$PATH"

uv --version

rm -rf .venv
uv venv --python 3.11
source .venv/bin/activate

echo "Python: $(which python)"

uv sync

echo "Installing TensorFlow GPU..."
uv pip install "tensorflow[and-cuda]"

if [ -f "/workspace/.scripts/compile-grpc.sh" ]; then
  bash /workspace/.scripts/compile-grpc.sh