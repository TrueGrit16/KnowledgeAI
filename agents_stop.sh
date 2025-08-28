#!/usr/bin/env bash
set -euo pipefail

# Gracefully stop all agents started by agents_start.sh
# Uses PID files first (logs/<name>.pid). Falls back to lsof.

LOGDIR=${LOGDIR:-logs}
HOST=${HOST:-127.0.0.1}

# name:port list must match agents_start.sh
AGENTS=(
  "rca:9131"
  "sop:9132"
  "ticket:9133"
  "super:9191"
)

mkdir -p "$LOGDIR"
echo "🛑 Stopping agents…" | tee -a "$LOGDIR/stop.log"

kill_safely() {
  local pid="$1"; shift
  local name="$1"; shift
  local logfile="$LOGDIR/${name}.log"

  if ! kill -0 "$pid" >/dev/null 2>&1; then
    echo "ℹ️  ${name}: pid ${pid} is not running" | tee -a "$logfile" "$LOGDIR/stop.log"
    return 0
  fi

  echo "$(date) - ${name}: sending SIGTERM to pid ${pid}" | tee -a "$logfile" "$LOGDIR/stop.log"
  kill -15 "$pid" 2>/dev/null || true

  # wait up to 8s for graceful shutdown
  for _ in {1..16}; do
    if ! kill -0 "$pid" >/dev/null 2>&1; then
      echo "$(date) - ✅ ${name}: stopped" | tee -a "$logfile" "$LOGDIR/stop.log"
      return 0
    fi
    sleep 0.5
  done

  echo "$(date) - ⚠️  ${name}: still alive, sending SIGKILL" | tee -a "$logfile" "$LOGDIR/stop.log"
  kill -9 "$pid" 2>/dev/null || true
}

stop_agent() {
  local spec="$1"; shift
  local name="${spec%%:*}"
  local port="${spec##*:}"
  local pidfile="$LOGDIR/${name}.pid"
  local logfile="$LOGDIR/${name}.log"

  # Prefer pidfile
  if [[ -f "$pidfile" ]]; then
    pid=$(cat "$pidfile" || true)
    if [[ -n "${pid}" ]]; then
      kill_safely "$pid" "$name"
    fi
    rm -f "$pidfile"
    return 0
  fi

  # Fallback: lsof by port (macOS/BSD compatible)
  if command -v lsof >/dev/null 2>&1; then
    pids=$(lsof -ti tcp:"$port" || true)
    if [[ -n "${pids}" ]]; then
      for p in $pids; do
        kill_safely "$p" "$name"
      done
      return 0
    fi
  fi

  # Last resort: try pkill by uvicorn + port flag
  if command -v pkill >/dev/null 2>&1; then
    echo "$(date) - ${name}: attempting pkill by command line match" | tee -a "$logfile" "$LOGDIR/stop.log"
    pkill -f "uvicorn .*--port ${port}" || true
  fi

  echo "$(date) - ℹ️  ${name}: no running process found" | tee -a "$logfile" "$LOGDIR/stop.log"
}

for spec in "${AGENTS[@]}"; do
  stop_agent "$spec"
done

echo "$(date) - ✅ All stop requests processed." | tee -a "$LOGDIR/stop.log"
