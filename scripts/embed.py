#!/usr/bin/env python
"""Split cleaned markdown, embed with bge-base, store in Chroma."""
from pathlib import Path
from logconf import logging
import json, hashlib, chromadb
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from rich.progress import track

BASE   = Path(__file__).resolve().parent.parent
TXT    = BASE / "clean"
DBPATH = (BASE / "vector_store").expanduser()

client = chromadb.PersistentClient(path=str(DBPATH))
collection = client.get_or_create_collection("knowledge_base")


splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=80)
model    = SentenceTransformer("BAAI/bge-base-en", device="mps")

for jf in track(TXT.glob("*.json"), description="Embedding chunks"):
    doc = json.loads(jf.read_text())
    for chunk in splitter.split_text(doc["body"]):
        cid = hashlib.md5(chunk.encode()).hexdigest()
        try:
            collection.add(
                documents=[chunk],
                metadatas=[{"src": doc["source"]}],
                ids=[cid],
            )
        except ValueError:
            logging.debug(f"↩️ Duplicate chunk skipped {cid}")

logging.info("✅ Embedding complete")
