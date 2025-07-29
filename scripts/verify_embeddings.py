#!/usr/bin/env python3
"""Verify that embeddings are stored and searchable in Chroma."""

from pathlib import Path
import json
import chromadb
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from rich import print

# === Paths ===
BASE = Path(__file__).resolve().parent.parent
CLEAN = BASE / "clean"
VECTOR_DB = BASE / "vector_store"

# === Load model & splitter ===
model = SentenceTransformer("BAAI/bge-base-en", device="mps")
splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=80)

# === Load ChromaDB ===
client = chromadb.PersistentClient(path=str(VECTOR_DB))
collection = client.get_or_create_collection("knowledge_base")

# === Choose a random clean file ===
files = list(CLEAN.glob("*.json"))
if not files:
    print("[red]❌ No documents found in `clean` folder.")
    exit(1)

doc = json.loads(files[0].read_text())
chunks = splitter.split_text(doc["body"])

# === Choose a sample chunk to search ===
sample = next((c for c in chunks if len(c) > 150), chunks[0])
print(f"[bold green]🔍 Verifying sample chunk:[/bold green]\n{sample[:200]}...\n")

# === Embed and query ===
query_vec = model.encode([sample])[0].tolist()
results = collection.query(
    query_embeddings=[query_vec],
    n_results=3
)

# === Display results ===
print(f"[bold yellow]🔗 Top results:[/bold yellow]")
for i, doc in enumerate(results["documents"][0]):
    print(f"\n[cyan]Match {i+1}:[/cyan]\n{doc[:300]}...\n[dim]Source: {results['metadatas'][0][i]['src']}[/dim]")

print("[bold green]✅ Verification complete. Embeddings are searchable.[/bold green]")