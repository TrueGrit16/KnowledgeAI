# scripts/agents/super_agent.py
from fastapi import FastAPI, Request
import httpx
from scripts.logconf import logging
import signal
import sys

def handle_shutdown(sig, frame):
    logging.info("🛑 Super agent shutting down.")
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_shutdown)

logging.basicConfig(level=logging.INFO)

AGENTS = {
    "rca": "http://127.0.0.1:9131/rca",
    "sop": "http://127.0.0.1:9132/sop",
    "ticket": "http://127.0.0.1:9133/ticket"
}

app = FastAPI()

@app.post("/super")
async def super_agent(request: Request):
    try:
        data = await request.json()
        mode = data.get("mode")
        payload = data.get("payload", {})

        if mode not in AGENTS:
            return {"error": f"Invalid mode '{mode}'"}

        async with httpx.AsyncClient(timeout=90.0) as client:
            logging.info(f"🔁 Forwarding to {mode} agent...")
            res = await client.post(AGENTS[mode], json=payload)
            res.raise_for_status()
            response_json = res.json()  # ✅ FIXED HERE — no await
            logging.info(f"✅ Response from {mode} agent: {response_json}")
            return response_json

    except httpx.HTTPStatusError as e:
        return {
            "error": f"{mode} agent returned HTTP error",
            "status_code": e.response.status_code,
            "detail": e.response.text
        }
    except Exception as e:
        logging.exception("Super agent failed")
        return {"error": f"Failed to contact {mode} agent", "detail": str(e)}


