#!/usr/bin/env bash
# Starts a local n8n (127.0.0.1 only) with this demo workflow imported and active.
# Usage: ./run_n8n.sh            (first run imports + activates the workflow)
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$PWD"

# Optional secrets (ANTHROPIC_API_KEY, AI_MODEL) live in .env - never in the workflow.
if [ -f .env ]; then set -a; . ./.env; set +a; fi

export N8N_USER_FOLDER="$ROOT/.n8n-local"
export N8N_HOST=127.0.0.1 N8N_LISTEN_ADDRESS=127.0.0.1 N8N_PORT="${N8N_PORT:-5678}"
export N8N_PROTOCOL=http N8N_SECURE_COOKIE=false
export N8N_DIAGNOSTICS_ENABLED=false N8N_VERSION_NOTIFICATIONS_ENABLED=false
export N8N_TEMPLATES_ENABLED=false N8N_PERSONALIZATION_ENABLED=false
export N8N_BLOCK_ENV_ACCESS_IN_NODE=false          # lets nodes read $env (key, paths)
export N8N_RESTRICT_FILE_ACCESS_TO="$ROOT/knowledge_base;$ROOT/data"
export SUPPORT_KB_FILE="$ROOT/knowledge_base/faq.json"
export SUPPORT_DATA_DIR="$ROOT/data"
export GENERIC_TIMEZONE="${GENERIC_TIMEZONE:-Europe/Berlin}"

mkdir -p data
[ -f data/tickets.csv ] || echo 'ticket_id,received_at,channel,name,email,category,confidence,classifier,faq_id,escalated,status,message,reply' > data/tickets.csv
touch data/manager_alerts.jsonl

N8N="$ROOT/node_modules/.bin/n8n"
[ -x "$N8N" ] || { echo "n8n not installed - run: npm install"; exit 1; }

if [ ! -f "$N8N_USER_FOLDER/.imported" ]; then
  "$N8N" import:workflow --input="$ROOT/workflow.json"
  "$N8N" publish:workflow --id=SupportAgent0001
  touch "$N8N_USER_FOLDER/.imported"
fi
exec "$N8N" start
