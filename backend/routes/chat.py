# backend/routes/chat.py
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse, ServerSentEvent
from pydantic import BaseModel, Field
import httpx, logging, os, uuid, json
from pathlib import Path
import datetime as dt

router = APIRouter()

# ---- Config ----
SUPER_URL = os.getenv("SUPER_URL", "http://127.0.0.1:9191/super")
# Default to a project-level logs dir; allow override via CHAT_LOG env.
CHAT_LOG = Path(os.getenv("CHAT_LOG", "backend/logs/chat.log"))
# Ensure parent directory exists to avoid FileNotFoundError
CHAT_LOG.parent.mkdir(parents=True, exist_ok=True)

class ChatReq(BaseModel):
    text: str = Field(..., description="User prompt")
    mode: str = Field("sop", pattern=r"^(sop|rca|ticket)$")

async def _call_super(payload: dict) -> dict:
    """Call the SUPER agent and return JSON.
    Raises HTTP 502 on failure.
    """
    async with httpx.AsyncClient(timeout=45) as client:
        try:
            res = await client.post(SUPER_URL, json=payload)
            res.raise_for_status()
            return res.json()
        except Exception as e:
            logging.exception("chat→super error")
            raise HTTPException(502, f"Agent error: {e}")

def _log_chat(mode: str, question: str, answer: dict) -> None:
    """Append one JSONL record to CHAT_LOG. Best-effort; never crash request."""
    try:
        rec = {
            "id": uuid.uuid4().hex,
            "ts": dt.datetime.utcnow().isoformat(),
            "mode": mode,
            "question": question,
            "answer": answer,
        }
        with CHAT_LOG.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        logging.exception("Failed to write chat log")

@router.post("/chat")
async def chat(req: ChatReq):
    payload = {"mode": req.mode, "payload": {"topic": req.text}}
    data = await _call_super(payload)

    # Log interaction (best-effort)
    _log_chat(req.mode, req.text, data)

    # Return only the first value (agent answer)
    return next(iter(data.values()))

@router.get("/chat/stream")
async def chat_stream(text: str, mode: str = "sop"):
    """Server-Sent Events stream so the FE can render tokens chunk-by-chunk."""
    payload = {"mode": mode, "payload": {"topic": text}}

    async def event_generator():
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", SUPER_URL, json=payload) as res:
                res.raise_for_status()
                async for line in res.aiter_lines():
                    if not line:
                        continue
                    if line.strip() == "[DONE]":
                        # signal end of stream
                        yield ServerSentEvent(data="", event="end")
                        break
                    try:
                        chunk = json.loads(line)
                        # extract the text for the chosen mode
                        text_chunk = chunk.get(mode) or next(iter(chunk.values()))
                        yield ServerSentEvent(data=text_chunk)
                    except json.JSONDecodeError:
                        # skip non-JSON keepalive lines
                        continue

    return EventSourceResponse(event_generator())