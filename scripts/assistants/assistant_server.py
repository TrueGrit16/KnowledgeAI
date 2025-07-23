import os
import openai
from fastapi import FastAPI, Request
import httpx
import uvicorn
import logging

openai.api_key = os.getenv("OPENAI_API_KEY")
SUPER_AGENT_URL = "http://127.0.0.1:9191/super"

app = FastAPI()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s %(name)s | %(message)s")

@app.post("/run_agent_task")
async def run_agent_task(request: Request):
    payload = await request.json()
    logging.info(f"📥 Assistant called with: {payload}")

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(SUPER_AGENT_URL, json=payload)
            resp.raise_for_status()
            response_json = await resp.json()
            logging.info(f"✅ Response from super agent: {response_json}")
            return response_json
        except Exception as e:
            logging.exception("❌ Failed to get response from SuperAgent")
            return {"error": "Failed to contact SuperAgent", "detail": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=9999)
