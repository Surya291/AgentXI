#!/usr/bin/env bash
# Switch Hermes default chat model to one of the LiteLLM route names (no Hermes code changes).
# Requires: hermes on PATH, model.provider=custom, base_url pointing at LiteLLM.
set -euo pipefail

MODELS=(
  "google/gemini-3-flash-preview"
  "google/gemini-3.1-pro-preview"
  "google/gemini-3.1-flash-image-preview"
  "google/gemini-3.1-flash-lite-preview"
)
ALIASES=(flash pro image lite)

usage() {
  echo "Usage: $0 [flash|pro|image|lite|1|2|3|4]"
  echo "  With no args, shows a numbered menu."
  exit "${1:-0}"
}

pick() {
  local i name
  echo "Hermes default model (LiteLLM route id):"
  for i in "${!MODELS[@]}"; do
    name="${ALIASES[$i]:-$i}"
    printf "  %d) %s  (%s)\n" "$((i + 1))" "$name" "${MODELS[$i]}"
  done
  read -r -p "Choice [1-4]: " c || true
  case "$c" in
    1) echo "${MODELS[0]}" ;;
    2) echo "${MODELS[1]}" ;;
    3) echo "${MODELS[2]}" ;;
    4) echo "${MODELS[3]}" ;;
    *) echo "" ;;
  esac
}

model=""
if [[ $# -eq 0 ]]; then
  model="$(pick)"
  if [[ -z "$model" ]]; then
    echo "Cancelled."
    exit 1
  fi
else
  case "$1" in
    -h|--help) usage 0 ;;
    1|flash) model="${MODELS[0]}" ;;
    2|pro) model="${MODELS[1]}" ;;
    3|image) model="${MODELS[2]}" ;;
    4|lite) model="${MODELS[3]}" ;;
    google/*) model="$1" ;;
    *) echo "Unknown option: $1"; usage 1 ;;
  esac
fi

if ! command -v hermes &>/dev/null; then
  echo "hermes not found on PATH."
  exit 1
fi

hermes config set model.default "$model"
echo "Default model is now: $model"
echo "New Hermes sessions use this; in an open chat use: /model $model"
