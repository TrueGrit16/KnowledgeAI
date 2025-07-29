
"""
scripts/check_embedding_progress.py

Counts how many embedding chunks *should* exist versus how many are actually stored in Chroma,
and prints a progress percentage.
"""

import os
import json
from pathlib import Path

import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter

# === Configuration (must match your embed.py) ===
CLEAN_DIR = Path(__file__).resolve().parent.parent / "clean"
VECTOR_DB = Path(__file__).resolve().parent.parent / "vector_store"
COLLECTION_NAME = "knowledge_base"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 80

def main():
    # Initialize Chroma client & collection
    client = chromadb.PersistentClient(path=str(VECTOR_DB))
    col = client.get_or_create_collection(COLLECTION_NAME)

    # Initialize splitter (must match your embed.py settings)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    # Count expected chunks
    total_chunks = 0
    for fn in CLEAN_DIR.glob("*.json"):
        with open(fn, "r") as f:
            doc = json.load(f)
        total_chunks += len(splitter.split_text(doc["body"]))

    # Count actual embeddings
    try:
        done = col.count()
    except Exception:
        # Fallback if count() not available
        done = len(col.get()["ids"])

    # Print progress
    pct = (done / total_chunks * 100) if total_chunks > 0 else 0
    print(f"{done}/{total_chunks} → {pct:.1f}% complete")

if __name__ == "__main__":
    main()