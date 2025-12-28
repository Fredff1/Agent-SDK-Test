#!/usr/bin/env bash
set -euo pipefail

# Simple helper to trigger offline or conversation eval via API.
# Usage:
#   scripts/run_eval.sh offline
#   scripts/run_eval.sh convo "<cid1>,<cid2>" latest|all

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_URL="${API_URL:-http://127.0.0.1:8000}"
MODE="${1:-offline}"

if [[ "${MODE}" == "offline" ]]; then
  echo "Running offline eval cases..."
  resp=$(curl -s -X POST "${API_URL}/api/offline_eval" \
    -H "Content-Type: application/json" \
    -d '{}')
  RESP="${resp}" python - <<'PY'
import json, os, sys, re
data = os.environ["RESP"]
start = data.find("{")
if start == -1:
    print(data)
    sys.exit(1)
try:
    obj = json.loads(data[start:])
    print(json.dumps(obj, ensure_ascii=False, indent=2))
except Exception:
    print(data)
    raise
PY
elif [[ "${MODE}" == "convo" ]]; then
  CIDS="${2:-}"
  RUN_MODE="${3:-latest}"
  if [[ -z "${CIDS}" ]]; then
    echo "Provide comma-separated conversation IDs as second argument."
    exit 1
  fi
  ids_json=$(CIDS="${CIDS}" RUN_MODE="${RUN_MODE}" python - <<'PY'
import os, json
cids = os.environ["CIDS"]
mode = os.environ["RUN_MODE"]
cid_list = [c.strip() for c in cids.split(",") if c.strip()]
print(json.dumps({"conversation_ids": cid_list, "mode": mode}))
PY
)
  echo "Running conversation eval for: ${CIDS} (mode=${RUN_MODE})"
  resp=$(curl -s -X POST "${API_URL}/api/conversation_eval" \
    -H "Content-Type: application/json" \
    -d "${ids_json}")
  RESP="${resp}" python - <<'PY'
import json, os, sys
data = os.environ["RESP"]
start = data.find("{")
if start == -1:
    print(data)
    sys.exit(1)
try:
    obj = json.loads(data[start:])
    print(json.dumps(obj, ensure_ascii=False, indent=2))
except Exception:
    print(data)
    raise
PY
else
  echo "Usage:"
  echo "  scripts/run_eval.sh offline"
  echo "  scripts/run_eval.sh convo \"cid1,cid2\" latest|all"
  exit 1
fi
