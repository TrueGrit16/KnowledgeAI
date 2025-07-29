#!/usr/bin/env python
"""Parallel embedding of clean markdown into Chroma vector store."""

from pathlib import Path
from logconf import logging
import json, hashlib, chromadb
from concurrent.futures import ThreadPoolExecutor
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from rich.progress import Progress, SpinnerColumn, TextColumn

# === Paths ===
BASE = Path(__file__).resolve().parent.parent
TXT = BASE / "clean"
DBPATH = (BASE / "vector_store").expanduser()

# === Chroma Setup ===
client = chromadb.PersistentClient(path=str(DBPATH))
collection = client.get_or_create_collection("knowledge_base")

# === Text Splitter & Embedding Model ===
splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=80)
model = SentenceTransformer("BAAI/bge-base-en", device="mps")

# === Track existing IDs to skip duplicates ===
existing_ids = set()
try:
    records = collection.get(limit=100000)
    existing_ids = set(records["ids"])
except Exception as e:
    logging.warning(f"⚠️ Failed to preload existing IDs: {e}")

# === Embedding Function ===
def embed_file(jf: Path):
    try:
        doc = json.loads(jf.read_text())
        chunks = splitter.split_text(doc["body"])
        embeddings = model.encode(chunks, batch_size=16, show_progress_bar=False)

        added = 0
        for chunk, vector in zip(chunks, embeddings):
            cid = hashlib.md5(chunk.encode()).hexdigest()
            if cid not in existing_ids:
                collection.add(
                    documents=[chunk],
                    embeddings=[vector.tolist()],
                    metadatas=[{"src": doc["source"]}],
                    ids=[cid],
                )
                added += 1
        logging.info(f"📌 Embedded {jf.name}: {added}/{len(chunks)} new chunks")
    except Exception:
        logging.exception(f"❌ Failed embedding {jf.name}")

# === Run in Parallel with Progress ===
json_files = list(TXT.glob("*.json"))

with Progress(
    SpinnerColumn(), TextColumn("[bold blue]{task.fields[filename]}"), transient=True
) as progress:
    with ThreadPoolExecutor(max_workers=4) as pool:
        tasks = []
        for jf in json_files:
            progress.add_task("embedding", filename=jf.name)
            tasks.append(pool.submit(embed_file, jf))

logging.info("✅ Embedding complete")