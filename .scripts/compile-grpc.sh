#!/usr/bin/env bash
set -Eeuo pipefail

echo "Preparing .generated folder..."
rm -rf .generated
mkdir -p .generated
touch .generated/__init__.py

echo "Generating gRPC Python files..."
uv run python -m grpc_tools.protoc \
  -I ./protos \
  --python_out=./.generated \
  --grpc_python_out=./.generated \
  --pyi_out=./.generated \
  ./protos/*.proto

echo "GRPC compilation successful!!!"