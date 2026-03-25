#!/usr/bin/env bash
# Call local LiteLLM proxy (must be running: ./start_litellm.sh).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing ${ENV_FILE}. Copy from .env.example and set GEMINI_API_KEY and LITELLM_MASTER_KEY."
  exit 1
fi

# shellcheck disable=SC1090
source "${ENV_FILE}"

PORT="${LITELLM_PORT:-4000}"
MODEL="${TEST_MODEL:-google/gemini-3-flash-preview}"

if [[ -z "${LITELLM_MASTER_KEY:-}" ]]; then
  echo "LITELLM_MASTER_KEY not set in .env"
  exit 1
fi

echo "POST http://127.0.0.1:${PORT}/v1/chat/completions model=${MODEL}"
curl -sS "http://127.0.0.1:${PORT}/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${LITELLM_MASTER_KEY}" \
  -d "{
    \"model\": \"${MODEL}\",
    \"messages\": [{\"role\": \"user\", \"content\": \"Reply with one word: ok\"}]
  }"
echo
