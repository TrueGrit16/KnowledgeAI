#!/bin/bash

echo "🧪 Testing Agent Endpoints..."

check_endpoint() {
    local name=$1
    local port=$2
    local path=$3
    local payload=$4

    echo "🔹 Testing $name Agent..."
    curl -s -o /dev/null -w "%{http_code}" -X POST http://127.0.0.1:$port/$path \
        -H "Content-Type: application/json" \
        -d "$payload" | grep -q "200" && echo "✅ $name is working" || echo "❌ $name failed"
}

# Define payloads
RCA_PAYLOAD='{"topic": "TESTING: Application downtime due to memory leak"}'
SOP_PAYLOAD='{"topic": "TESTING: Case creation in IPS"}'
TICKET_PAYLOAD='{"topic": "TESTING: Cannot submit expense report"}'
SUPER_PAYLOAD_RCA='{"mode": "rca", "payload": {"topic": "TESTING: Routing from SUPER to RCA"}}'
SUPER_PAYLOAD_SOP='{"mode": "sop", "payload": {"topic": "TESTING: Routing from SUPER to SOP"}}'
SUPER_PAYLOAD_TICKET='{"mode": "ticket", "payload": {"topic": "TESTING: Routing from SUPER to TICKET"}}'

# Run tests
check_endpoint "RCA" 9131 "rca" "$RCA_PAYLOAD"
check_endpoint "SOP" 9132 "sop" "$SOP_PAYLOAD"
check_endpoint "Ticket" 9133 "ticket" "$TICKET_PAYLOAD"
check_endpoint "Super to RCA" 9191 "super" "$SUPER_PAYLOAD_RCA"
check_endpoint "Super to SOP" 9191 "super" "$SUPER_PAYLOAD_SOP"
check_endpoint "Super to Ticket" 9191 "super" "$SUPER_PAYLOAD_TICKET"