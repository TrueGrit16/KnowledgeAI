#!/usr/bin/env python3
"""Standalone FastAPI search tool — no openai_agents, no mcp. MCP will invoke this as subprocess."""
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel
# from logconf import logging
from scripts.logconf import logging
# from langchain_community.vectorstores import Chroma
from langchain_chroma import Chroma

BASE = Path(__file__).resolve().parent.parent
VECTOR_DIR = (BASE / "vector_store").expanduser()
vectordb = Chroma(persist_directory=str(VECTOR_DIR), collection_name="knowledge_base")

app = FastAPI()

class SearchRequest(BaseModel):
    query: str

class SearchResponse(BaseModel):
    passages: list[str]

@app.post("/search-kb", response_model=SearchResponse)
def search_kb(req: SearchRequest):
    try:
        docs = vectordb.similarity_search(req.query, k=8)
        return {"passages": [d.page_content for d in docs]}
    except Exception as e:
        logging.exception("search_kb failed")
        return {"passages": []}

@app.get("/health")
def health():
    return {"status": "ok"}
