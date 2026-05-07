#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.prod.yml"
COMPOSE_ENV_FILE="${PROJECT_ROOT}/.env.compose"

PROJECT_NAME="plantify_production"
SERVICE="plantify-ml-api"
CONTAINER_NAME="plantify-ml-api"

cd "${PROJECT_ROOT}"

COMPOSE_ARGS=()

if [[ -f "${COMPOSE_ENV_FILE}" ]]; then
  COMPOSE_ARGS+=(--env-file "${COMPOSE_ENV_FILE}")
fi

COMPOSE_ARGS+=(-p "${PROJECT_NAME}" -f "${COMPOSE_FILE}")

echo "Using compose file: ${COMPOSE_FILE}"
echo "Using env file: ${COMPOSE_ENV_FILE}"
echo

echo "Stopping ${SERVICE}..."
docker compose "${COMPOSE_ARGS[@]}" stop "${SERVICE}" || true

echo "Removing old ${SERVICE} container from compose..."
docker compose "${COMPOSE_ARGS[@]}" rm -f "${SERVICE}" || true

echo "Removing any existing Docker container named ${CONTAINER_NAME}..."
docker rm -f "${CONTAINER_NAME}" || true

echo "Rebuilding and starting fresh ${SERVICE}..."
docker compose "${COMPOSE_ARGS[@]}" up --build --force-recreate -d --no-deps "${SERVICE}"

echo
docker compose "${COMPOSE_ARGS[@]}" ps "${SERVICE}"

echo
docker compose "${COMPOSE_ARGS[@]}" logs --tail=50 "${SERVICE}"

echo
echo "Container env check:"
docker exec "${CONTAINER_NAME}" sh -lc 'env | grep -E "GRPC|APP|HOST_PORT"'