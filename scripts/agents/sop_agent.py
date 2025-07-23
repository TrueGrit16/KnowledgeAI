from fastapi import FastAPI
from pydantic import BaseModel
from scripts.logconf import logging
from scripts.agents.shared import vectordb, client
import signal
import sys

def handle_shutdown(sig, frame):
    logging.info("🛑 SOP agent shutting down.")
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_shutdown)

app = FastAPI()

class SOPRequest(BaseModel):
    topic: str

@app.post("/sop")
def sop_generation(req: SOPRequest):
    logging.info(f"🔥 Received SOP request: {req.topic}")
    try:
        docs = vectordb.similarity_search(req.topic, k=8)
        context = "\n---\n".join([d.page_content for d in docs])
        prompt = f"""You're a knowledge assistant. Draft a step-by-step SOP from the below context.
        
Context:
{context}

Output in markdown-style numbered steps.
"""
        res = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}]
        )
        return {"sop": res.choices[0].message.content.strip()}
    except Exception as e:
        logging.exception("SOP agent failed")
        return {"sop": "Error generating SOP"}
