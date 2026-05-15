#!/usr/bin/env bash
set -Eeuo pipefail

NETWORK="plantify-network"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$PROJECT_ROOT"

echo "Project root: $PROJECT_ROOT"

if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  if ! docker network inspect "$NETWORK" >/dev/null 2>&1; then
    echo "Creating Docker network: $NETWORK"
    docker network create --driver bridge "$NETWORK"
  else
    echo "Docker network exists"
  fi
fi

if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi

export PATH="$HOME/.local/bin:$PATH"

uv --version

rm -rf .venv
uv venv --python 3.12
source .venv/bin/activate

echo "Python: $(which python)"

uv sync


if command -v nvidia-smi &> /dev/null; then
    echo "GPU detected, installing PyTorch CUDA..."
    uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
else
    echo "No GPU detected, installing PyTorch CPU..."
    uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
fi

echo "Installing gradient boosting stack..."
uv pip install -U xgboost lightgbm catboost

if [ -f "/workspace/.scripts/compile-grpc.sh" ]; then
  bash /workspace/.scripts/compile-grpc.sh
fi
if command -v nvidia-smi &> /dev/null; then
    echo "Setup complete (GPU ML ready)."
else
  echo "Setup complete (CPU ML ready)."