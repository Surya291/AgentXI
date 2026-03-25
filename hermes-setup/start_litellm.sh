#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"
CONFIG_FILE="${SCRIPT_DIR}/litellm_config.yaml"
CONFIG_EXAMPLE_FILE="${SCRIPT_DIR}/litellm_config.yaml.example"
VENV_LITELLM="${SCRIPT_DIR}/.venv/bin/litellm"

if [[ -f "${ENV_FILE}" ]]; then
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
fi

if [[ -z "${GEMINI_API_KEY:-}" ]]; then
  echo "Error: GEMINI_API_KEY is not set."
  echo "Create ${ENV_FILE} from .env.example and set GEMINI_API_KEY."
  exit 1
fi

if [[ -z "${LITELLM_MASTER_KEY:-}" ]]; then
  echo "Error: LITELLM_MASTER_KEY is not set."
  echo "Create ${ENV_FILE} from .env.example and set LITELLM_MASTER_KEY."
  exit 1
fi

if [[ ! -f "${CONFIG_FILE}" ]]; then
  if [[ -f "${CONFIG_EXAMPLE_FILE}" ]]; then
    cp "${CONFIG_EXAMPLE_FILE}" "${CONFIG_FILE}"
    echo "Created ${CONFIG_FILE} from example."
  else
    echo "Error: ${CONFIG_FILE} not found and no example file exists."
    exit 1
  fi
fi

# Ensure LiteLLM master key matches the env value.
if grep -qE '^  master_key:' "${CONFIG_FILE}"; then
  sed -i "s|^  master_key:.*$|  master_key: \"${LITELLM_MASTER_KEY}\"|" "${CONFIG_FILE}"
else
  cat >> "${CONFIG_FILE}" <<EOF

general_settings:
  master_key: "${LITELLM_MASTER_KEY}"
EOF
fi

cd "${SCRIPT_DIR}"
if [[ -x "${VENV_LITELLM}" ]]; then
  LITELLM_CMD="${VENV_LITELLM}"
elif command -v litellm >/dev/null 2>&1; then
  LITELLM_CMD="litellm"
else
  echo "Error: litellm not found. Run: ${SCRIPT_DIR}/install_litellm.sh"
  exit 1
fi

exec "${LITELLM_CMD}" --config "${CONFIG_FILE}" --port "${LITELLM_PORT:-4000}"
