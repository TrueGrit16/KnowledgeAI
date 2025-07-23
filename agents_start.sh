#!/bin/bash
set -e

# Set OpenAI API key
export OPENAI_API_KEY=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

# Activate env if not already
ENV_NAME="knowledge-ai"
if ! conda info --envs | grep -q "$ENV_NAME"; then
  echo "❌ Conda env '$ENV_NAME' not found"
  exit 1
fi

eval "$(conda shell.bash hook)"
conda activate $ENV_NAME

# Ensure uvicorn is available
if ! command -v uvicorn &> /dev/null; then
  echo "❌ 'uvicorn' not found in env. Did you install requirements?"
  exit 1
fi

# Set Python path to enable relative imports
export PYTHONPATH=$(pwd)

echo "📦 Starting agents..."

uvicorn scripts.agents.rca_agent:app --port 9131 --host 127.0.0.1 > logs/rca.log 2>&1 &
sleep 2
if ! ps -p $! > /dev/null; then echo "❌ RCA Agent failed to start"; else echo "✅ RCA Agent running"; fi

uvicorn scripts.agents.sop_agent:app --port 9132 --host 127.0.0.1 > logs/sop.log 2>&1 &
sleep 2
if ! ps -p $! > /dev/null; then echo "❌ SOP Agent failed to start"; else echo "✅ SOP Agent running"; fi

uvicorn scripts.agents.ticket_agent:app --port 9133 --host 127.0.0.1 > logs/ticket.log 2>&1 &
sleep 2
if ! ps -p $! > /dev/null; then echo "❌ Ticket Agent failed to start"; else echo "✅ Ticket Agent running"; fi

uvicorn scripts.agents.super_agent:app --port 9191 --host 127.0.0.1 > logs/super.log 2>&1 &
sleep 2
if ! ps -p $! > /dev/null; then echo "❌ Super Agent failed to start"; else echo "✅ Super Agent running"; fi

echo "🚀 All agents triggered. Check logs in ./logs/*.log"
