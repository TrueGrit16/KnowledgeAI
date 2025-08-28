#!/usr/bin/env bash
# Activate virtual environment
source .venv/bin/activate

# Load environment from .env if present (export all vars)
if [ -f ./.env ]; then
  set -a
  . ./.env
  set +a
fi

# main script
set -euo pipefail

# ── Configuration ──────────────────────────────────────────────────────────────
HOST="${HOST:-127.0.0.1}"
LOGDIR="${LOGDIR:-logs}"
PYAPP_BASE="scripts.agents"   # base module for agent apps

# Agent name → [module, port]
AGENTS=(
  "rca_agent:${PYAPP_BASE}.rca_agent:app:9131"
  "sop_agent:${PYAPP_BASE}.sop_agent:app:9132"
  "ticket_agent:${PYAPP_BASE}.ticket_agent:app:9133"
  "super_agent:${PYAPP_BASE}.super_agent:app:9191"
)

# Preferred environments: try .venv first, then Conda env `knowledge-ai`
VENV_PATH=".venv"
CONDA_ENV="knowledge-ai"

# ── Secrets / env ─────────────────────────────────────────────────────────────
# Do NOT hardcode secrets here. Optionally load from .env if present.
if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo "⚠️  OPENAI_API_KEY is not set. Continuing, but API calls may fail."
fi

# ── Ensure logs directory ─────────────────────────────────────────────────────
mkdir -p "${LOGDIR}"

# ── Activate Python environment ───────────────────────────────────────────────
_env_ok=false
# Prefer local venv if present
if [[ -f "${VENV_PATH}/bin/activate" ]]; then
  echo "🔧 Using venv: ${VENV_PATH}"
  # shellcheck disable=SC1091
  source "${VENV_PATH}/bin/activate"
  _env_ok=true
fi

# Otherwise try conda if available
if [[ "${_env_ok}" = false ]] && command -v conda >/dev/null 2>&1; then
  if conda env list | awk '{print $1}' | grep -qx "${CONDA_ENV}"; then
    echo "🔧 Using conda env: ${CONDA_ENV}"
    # shellcheck disable=SC1091
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate "${CONDA_ENV}"
    _env_ok=true
  fi
fi

if [[ "${_env_ok}" = false ]]; then
  cat <<EOF
❌ No Python env found.
Create one of the following and re-run:
  # Option A: venv
  python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt

  # Option B: conda
  conda create -n ${CONDA_ENV} python=3.11 -y && conda activate ${CONDA_ENV} && pip install -r requirements.txt
EOF
  exit 1
fi

# Ensure relative imports work (repo root)
export PYTHONPATH="$(pwd)${PYTHONPATH:+:${PYTHONPATH}}"

# ── Sanity checks ─────────────────────────────────────────────────────────────
if ! python -c "import uvicorn, fastapi" >/dev/null 2>&1; then
  echo "❌ Missing deps: uvicorn/fastapi. Install requirements first."
  echo "   pip install -r requirements.txt"
  exit 1
fi

# ── Functions ─────────────────────────────────────────────────────────────────
start_agent () {
  local name="$1"; shift
  local module="$1"; shift
  local app="$1"; shift
  local port="$1"; shift

  local logfile="${LOGDIR}/${name}.log"
  local pidfile="${LOGDIR}/${name}.pid"

  echo "▶️  Starting ${name} on http://${HOST}:${port} …"
  nohup uvicorn "${module}:${app}" --host "${HOST}" --port "${port}" --reload \
    >"${logfile}" 2>&1 &
  local pid=$!
  echo "${pid}" > "${pidfile}"
  sleep 1
  if kill -0 "${pid}" >/dev/null 2>&1; then
    echo "✅ ${name} running (pid ${pid}) — logs: ${logfile}"
  else
    echo "❌ ${name} failed to start — check ${logfile}"
  fi
}

# ── Launch all agents ─────────────────────────────────────────────────────────
echo "📦 Starting agents…"
for spec in "${AGENTS[@]}"; do
  IFS=":" read -r name module app port <<<"${spec}"
  start_agent "${name}" "${module}" "${app}" "${port}"
  sleep 1
done

echo "🚀 All agents triggered. Tail logs with: tail -f ${LOGDIR}/*.log"