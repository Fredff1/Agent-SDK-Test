#!/usr/bin/env bash
set -euo pipefail

# Bootstrap script to export config values and start backend/frontend locally.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "Root dir $ROOT_DIR"
CONFIG_PATH="${APP_CONFIG_PATH:-${ROOT_DIR}/config/local.yaml}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"

export PYTHONPATH="${ROOT_DIR}/src:${PYTHONPATH:-}"

load_env_from_yaml() {
  if [[ ! -f "$CONFIG_PATH" ]]; then
    echo "Config file not found at ${CONFIG_PATH}, relying on existing environment variables."
    return 0
  fi

  eval "$(
    CONFIG_PATH="$CONFIG_PATH" python - <<'PY'
import os
import yaml

cfg_path = os.environ["CONFIG_PATH"]
try:
    with open(cfg_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
except FileNotFoundError:
    data = {}

llm = data.get("llm", data)
lang = data.get("langfuse", {})

def emit(env_key, value):
    if os.getenv(env_key) is None and value not in (None, ""):
        print(f'export {env_key}="{value}"')

emit("LLM_BASE_URL", llm.get("base_url"))
emit("LLM_API_KEY", llm.get("api_key"))
emit("LLM_MODEL_NAME", llm.get("model_name"))
emit("LLM_OUTPUT_STREAMING", llm.get("output_streaming"))

emit("LANGFUSE_HOST", lang.get("host"))
emit("LANGFUSE_PUBLIC_KEY", lang.get("public_key"))
emit("LANGFUSE_SECRET_KEY", lang.get("secret_key"))
emit("LANGFUSE_RELEASE", lang.get("release"))
emit("LANGFUSE_ENABLED", lang.get("enabled"))
PY
  )"
}

start_backend() {
  load_env_from_yaml
  uvicorn airloop.server.api:app --reload --port "${BACKEND_PORT}"
}

start_frontend() {
  load_env_from_yaml
  cd "${ROOT_DIR}/src/airloop-ui"
  npm run dev -- --port "${FRONTEND_PORT}"
}

case "${1:-both}" in
  backend)
    start_backend
    ;;
  frontend)
    start_frontend
    ;;
  both)
    start_backend &
    backend_pid=$!
    start_frontend &
    frontend_pid=$!
    wait ${backend_pid} ${frontend_pid}
    ;;
  *)
    echo "Usage: $0 [backend|frontend|both]"
    exit 1
    ;;
esac
