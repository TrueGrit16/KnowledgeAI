#!/bin/bash

echo "🛑 Stopping agents..." | tee -a logs/stop.log

AGENTS=(rca sop ticket super)
PORTS=(9131 9132 9133 9191)

for i in "${!AGENTS[@]}"; do
  agent=${AGENTS[$i]}
  port=${PORTS[$i]}
  echo "$(date) - 🛑 Sending SIGTERM to $agent agent on port $port" | tee -a logs/${agent}.log
  lsof -ti tcp:$port | xargs kill -15
done

echo "$(date) ✅ All agents stopped." | tee -a logs/stop.log
