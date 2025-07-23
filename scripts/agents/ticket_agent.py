from fastapi import FastAPI
from pydantic import BaseModel
from scripts.logconf import logging
from scripts.agents.shared import vectordb, client
import signal
import sys

def handle_shutdown(sig, frame):
    logging.info("🛑 Ticket agent shutting down.")
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_shutdown)

app = FastAPI()

class TicketRequest(BaseModel):
    topic: str  # 🎯 Change from `title` & `notes` to a unified `topic`

@app.post("/ticket")
def resolve_ticket(req: TicketRequest):
    try:
        logging.info(f"🎫 Ticket received: {req.topic}")
        docs = vectordb.similarity_search(req.topic, k=8)
        context = "\n---\n".join([d.page_content for d in docs])
        prompt = f"""You're a support engineer. Draft a suggested resolution for the below ticket using past case knowledge.

Context:
{context}

Ticket:
{req.topic}

Output a one-paragraph summary and a ready-to-send ticket reply.
"""
        res = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}]
        )
        return {"resolution": res.choices[0].message.content.strip()}
    except Exception:
        logging.exception("Ticket agent failed")
        return {"resolution": "Error resolving ticket"}
