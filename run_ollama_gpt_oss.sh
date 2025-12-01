#!/usr/bin/env bash
set -euo pipefail

MODEL_NAME="${1:-gpt-oss:20b}"


echo "[ollama] Waiting for API to be ready on http://localhost:11434 ..."
until curl -sSf http://localhost:11434/api/tags >/dev/null 2>&1; do
  sleep 2
done

echo "[ollama] Pulling model ${MODEL_NAME} inside the ollama container..."
docker compose exec -T ollama ollama pull "${MODEL_NAME}"

echo "[ollama] Model ${MODEL_NAME} is ready"
