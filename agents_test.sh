#!/usr/bin/env bash
set -euo pipefail

# ==========================================
# Agent endpoint smoke tests (low-cost)
#  - Single HTTP request per attempt (no double POSTs)
#  - Per‑endpoint timeouts
#  - Retries are configurable
#  - Defaults avoid hammering paid endpoints
# ==========================================

# Tweakables --------------------------------------------------------------
HOST=${HOST:-127.0.0.1}

RCA_PORT=${RCA_PORT:-9131}
SOP_PORT=${SOP_PORT:-9132}
TICKET_PORT=${TICKET_PORT:-9133}
SUPER_PORT=${SUPER_PORT:-9191}

# Retries & delays
RETRIES=${RETRIES:-1}
RETRY_DELAY=${RETRY_DELAY:-1}
SLEEP_BETWEEN=${SLEEP_BETWEEN:-0}

# Per-endpoint timeouts (seconds)
RCA_TIMEOUT=${RCA_TIMEOUT:-10}
SOP_TIMEOUT=${SOP_TIMEOUT:-30}
TICKET_TIMEOUT=${TICKET_TIMEOUT:-10}
SUPER_TIMEOUT=${SUPER_TIMEOUT:-30}

# Cost-saver: allow running agents in mock mode unless explicitly disabled
export MOCK_LLM=${MOCK_LLM:-0}
export TOKENIZERS_PARALLELISM=${TOKENIZERS_PARALLELISM:-false}

# Payloads ---------------------------------------------------------------
RCA_PAYLOAD='{"topic": "TESTING: Incorrect document uploaded"}'
SOP_PAYLOAD='{"topic": "TESTING: Outcome Letter generation"}'
TICKET_PAYLOAD='{"topic": "TESTING: Incorrect eligibility mapping"}'
SUPER_PAYLOAD_RCA='{"mode": "rca", "payload": {"topic": "TESTING: Routing from SUPER to RCA"}}'
SUPER_PAYLOAD_SOP='{"mode": "sop", "payload": {"topic": "TESTING: Routing from SUPER to SOP"}}'
SUPER_PAYLOAD_TICKET='{"mode": "ticket", "payload": {"topic": "TESTING: Routing from SUPER to TICKET"}}'

# Helpers ----------------------------------------------------------------
# POST with retries; prints "<status> | <first 200 chars>"
post_with_retries() {
  local url="$1"; shift
  local data="$1"; shift
  local timeout="$1"; shift

  local attempt=1
  local status
  local body
  local tmp

  while :; do
    tmp=$(mktemp)
    # Single request: body -> $tmp, status via -w
    status=$(curl -sS -m "$timeout" \
      -H 'Content-Type: application/json' \
      -X POST "$url" -d "$data" \
      -o "$tmp" -w '%{http_code}' || true)

    # Read a short preview to keep logs tidy (and costs visible)
    body=$(head -c 200 "$tmp" 2>/dev/null || true)
    rm -f "$tmp"

    if [[ "$status" == "200" ]]; then
      echo "200 | ${body}"
      return 0
    fi

    if (( attempt >= RETRIES )); then
      echo "${status} | ${body}"
      return 1
    fi

    sleep "$RETRY_DELAY"
    ((attempt++))
  done
}

check_endpoint() {
  local name="$1"; shift
  local port="$1"; shift
  local path="$1"; shift
  local payload="$1"; shift
  local timeout="$1"; shift

  local url="http://${HOST}:${port}/${path}"
  echo "\n🔹 Testing ${name} -> ${url} (timeout=${timeout}s, retries=${RETRIES})"

  if out=$(post_with_retries "$url" "$payload" "$timeout"); then
    echo "✅ ${name} is working (${out})"
  else
    echo "❌ ${name} failed (${out})"
    FAILED=1
  fi

  if (( SLEEP_BETWEEN > 0 )); then
    sleep "$SLEEP_BETWEEN"
  fi
  return 0
}

# -----------------------------------------------------------------------
FAILED=0

echo "🧪 Testing Agent Endpoints..."

check_endpoint "RCA"          "$RCA_PORT"    "rca"    "$RCA_PAYLOAD"          "$RCA_TIMEOUT"
check_endpoint "SOP"          "$SOP_PORT"    "sop"    "$SOP_PAYLOAD"          "$SOP_TIMEOUT"
check_endpoint "Ticket"       "$TICKET_PORT" "ticket" "$TICKET_PAYLOAD"       "$TICKET_TIMEOUT"
check_endpoint "Super→RCA"    "$SUPER_PORT"  "super"  "$SUPER_PAYLOAD_RCA"    "$SUPER_TIMEOUT"
check_endpoint "Super→SOP"    "$SUPER_PORT"  "super"  "$SUPER_PAYLOAD_SOP"    "$SUPER_TIMEOUT"
check_endpoint "Super→Ticket" "$SUPER_PORT"  "super"  "$SUPER_PAYLOAD_TICKET" "$SUPER_TIMEOUT"

exit $FAILED