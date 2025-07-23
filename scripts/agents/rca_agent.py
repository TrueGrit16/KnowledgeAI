from fastapi import FastAPI
from pydantic import BaseModel
from scripts.logconf import logging
from scripts.agents.shared import vectordb, client
import signal
import sys

def handle_shutdown(sig, frame):
    logging.info("🛑 RCA agent shutting down.")
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_shutdown)

app = FastAPI()

class RCARequest(BaseModel):
    topic: str  

@app.post("/rca")
def root_cause_analysis(req: RCARequest):
    try:
        logging.info(f"🔥 RCA request: {req.topic}")
        docs = vectordb.similarity_search(req.topic, k=8)
        context = "\n---\n".join([d.page_content for d in docs])
        prompt = f"""You are an SRE assistant. Based on the context below, find and summarize the most probable root cause:
        
Context:
{context}

Output a concise Root Cause Analysis (RCA) in 5-7 lines.
"""
        res = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}]
        )
        return {"rca": res.choices[0].message.content.strip()}
    except Exception:
        logging.exception("RCA agent failed")
        return {"rca": "Error processing RCA"}
