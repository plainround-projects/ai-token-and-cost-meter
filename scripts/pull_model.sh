#!/usr/bin/env bash
# Download a small open-weight model through ollama. The weights live in ollama's own store, never in this repository.
set -euo pipefail
model="${1:-qwen2.5:0.5b}"
if ! command -v ollama >/dev/null; then
  echo "ollama is not installed: https://ollama.com/download (or run llama.cpp's llama-server and set OPENAI_BASE_URL)" >&2
  exit 1
fi
ollama pull "$model"
echo "pulled $model; serve it with 'ollama serve' (the app does this) and set MODEL_PROVIDER=openai-compatible"
