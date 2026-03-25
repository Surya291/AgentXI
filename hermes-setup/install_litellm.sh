#!/usr/bin/env bash
# Install or upgrade LiteLLM proxy into a local venv (recommended).
# After the 1.82.8 incident, prefer a version explicitly published as safe on PyPI;
# this script installs the latest litellm[proxy] from PyPI.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi

.venv/bin/pip install --upgrade pip setuptools wheel
.venv/bin/pip install --upgrade "litellm[proxy]"

echo "Installed:"
.venv/bin/pip show litellm | sed -n '1,5p'
echo
echo "Binary: ${SCRIPT_DIR}/.venv/bin/litellm"
echo "Start proxy: ${SCRIPT_DIR}/start_litellm.sh"
