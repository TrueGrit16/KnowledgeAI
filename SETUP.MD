# KnowledgeAI — End‑to‑End Setup & User Guide

This is the **single source of truth** to set up KnowledgeAI on a fresh machine, run the RAG pipeline, spin up the agents, test safely (with a mock LLM to avoid costs), and troubleshoot common issues we encountered.

---

## 📑 Table of Contents
1. [Overview](#overview)  
2. [Architecture at a Glance](#architecture-at-a-glance)  
3. [Directory Structure](#directory-structure)  
4. [Prerequisites](#prerequisites)  
5. [Environment Setup](#environment-setup)  
   - [Clone the Repository](#1-clone-the-repository)  
   - [Python Virtual Environment](#2-python-virtual-environment)  
   - [Install Python Dependencies](#3-install-python-dependencies)  
   - [Install External Tools (macOS)](#4-install-external-tools-macos)  
   - [Environment Variables (.env)](#5-environment-variables-env)  
6. [Data Prep for RAG](#data-prep-for-rag)  
7. [Run the Pipeline](#run-the-pipeline)  
8. [Vector Store Management](#vector-store-management)  
9. [Run the Agents](#run-the-agents)  
   - [Start](#start) • [Stop](#stop) • [Test](#test) • [Mock Mode](#mock-mode) • [Ports](#ports)  
10. [Scripts Reference](#scripts-reference)  
11. [Troubleshooting & Known Issues](#troubleshooting--known-issues)  
12. [Cost Control / Safety Notes](#cost-control--safety-notes)  
13. [Common Pitfalls](#common-pitfalls)  
14. [Cheatsheet](#cheatsheet)

---

## 📖 Overview

**KnowledgeAI** is a **Retrieval‑Augmented Generation (RAG)** project with a document pipeline and four FastAPI agents:

- **RCA Agent** — root‑cause analysis  
- **SOP Agent** — procedures & step‑by‑steps  
- **Ticket Agent** — summarise/resolve issue tickets  
- **Super Agent** — orchestrates, can call the others

The typical flow:
1. Put source docs into `raw/`.
2. Run the pipeline (`python -m scripts.pipeline all`) → extracts/captions/chunks/embeds into `vector_store/`.
3. Start agents → query locally over your embedded knowledge.

You can run everything in **mock mode** (`MOCK_LLM=1`) to **avoid API costs** while you iterate.

---

## 🧩 Architecture at a Glance

- **Extraction & Captioning**: `scripts/extract_and_caption.py`  
  - Uses `unstructured` for Office files/PDFs; uses **BLIP** (HF model `Salesforce/blip-image-captioning-base`) for image captions.  
- **Embedding**: `scripts/embed.py`  
  - Uses **SentenceTransformers** (`BAAI/bge-base-en` by default) and stores vectors in **Chroma** at `vector_store/`.  
- **Pipeline Orchestrator**: `scripts/pipeline.py`  
  - High‑level “`all`” command that runs extraction → embedding.
- **Agents**: `scripts/agents/*` (+ helper in `scripts/agents/shared.py`)  
  - Serve FastAPI endpoints; read from `vector_store/`; optionally call OpenAI (or mock).

---

## 📂 Directory Structure

```
KnowledgeAI/
├── raw/                         # <-- Drop your source docs here (PPTX, DOCX, XLSX, PDF, etc.)
├── output/                      # Extraction outputs / temporary artifacts
├── vector_store/                # Chroma DB files (created by pipeline)
├── scripts/
│   ├── pipeline.py              # Orchestrates end-to-end pipeline (extract → embed)
│   ├── extract_and_caption.py   # Unstructured + BLIP image captioning
│   ├── embed.py                 # Build / update Chroma vector store
│   ├── verify_embeddings.py     # Sanity checks on the vector store
│   ├── check_embedding_progress.py # Inspect progress / counts
│   ├── chat.py                  # (Optional) local CLI test client
│   ├── tools_rag.py             # RAG helper functions
│   └── agents/
│       ├── shared.py            # Shared loader: Chroma, retriever, etc.
│       ├── rca_agent.py         # RCA FastAPI app
│       ├── sop_agent.py         # SOP FastAPI app
│       ├── ticket_agent.py      # Ticket FastAPI app
│       └── super_agent.py       # Super FastAPI app (router/orchestrator)
├── agents_start.sh              # Start all agents (uses venv; no conda)
├── agents_stop.sh               # Stop all agents
├── agents_test.sh               # Health/test of endpoints
├── requirements.txt             # Pinned Python deps
├── .env                         # Environment variables (created by you)
└── SETUP.MD                     # This guide
```

> **Note:** Some scripts print informative logs to `logs/*.log`. Tail with `tail -f logs/*.log`.

---

## ✅ Prerequisites

- **macOS 12+ (Apple Silicon ok)** / Linux / WSL on Windows  
- **Python 3.11** recommended (3.9+ supported)  
- **Git** installed & configured  
- (Optional) **OpenAI API key** for live LLM calls

---

## ⚙️ Environment Setup

### 1. Clone the Repository
```bash
git clone https://github.com/TrueGrit16/KnowledgeAI.git
cd KnowledgeAI
```

### 2. Python Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate      # macOS/Linux
# On Windows: .venv\Scripts\activate
python -m pip install --upgrade pip wheel setuptools
```

### 3. Install Python Dependencies
```bash
# Main deps (includes langchain, chroma, sentence-transformers, fastapi, uvicorn, etc.)
pip install -r requirements.txt

# Enable Unstructured extras for Office files:
pip install "unstructured[docx]" "unstructured[xlsx]" "unstructured[pptx]"
```

### 4. Install External Tools (macOS)
These are used by `unstructured` and optional conversions.

```bash
brew install imagemagick ghostscript poppler tesseract ffmpeg cmake
brew install --cask libreoffice
```

> **wkhtmltopdf?** The Homebrew cask is discontinued. It’s **optional** for this repo.  
> If you ever need it, use a Docker image or download a macOS pkg from the upstream releases. Not required for the current pipeline.

### 5. Environment Variables (.env)
Create a `.env` file in repo root:

```env
# === LLM / Cost Control ===
MOCK_LLM=1                      # 1 = NO paid API calls; agents return mock outputs
OPENAI_API_KEY=                 # Set only if MOCK_LLM=0 (live calls)
# OPENAI_BASE_URL=             # (Optional) custom base for self-hosted/OpenAI-compatible APIs

# === RAG / Storage ===
VECTOR_STORE_PATH=./vector_store

# === Logging / Misc ===
LOG_LEVEL=INFO
TOKENIZERS_PARALLELISM=false    # Avoid HF tokenizers fork warnings
HF_HUB_DISABLE_TELEMETRY=1
```

> **Important:** Agents read `.env` at startup. If you change `.env`, restart agents.

---

## 📥 Data Prep for RAG

1. Put source files in `raw/`.  
2. Supported (via `unstructured` + extras): **.pptx, .docx, .xlsx, .pdf, .txt, .md**, images, etc.  
3. If a file fails:
   - **PPTX `PackageNotFoundError`** → file path wrong / not present. Ensure the file exists at `raw/<exact name>.pptx`.  
   - **DOCX “not a ZIP archive”** → file is corrupted or not a real .docx. Re‑save using Word/LibreOffice: *File → Save As → .docx*.  
   - **XLSX extra** → ensure `pip install "unstructured[xlsx]"` is installed.

---

## ▶️ Run the Pipeline

The orchestrator runs **extraction → captioning → embedding**:

```bash
python -m scripts.pipeline all
```

What you’ll see:
- **Extraction + Captioning** logs per file (uses BLIP model on first run; downloads from Hugging Face).  
- **Embedding** with `BAAI/bge-base-en` into Chroma at `vector_store/`.

> **Tip:** First run may download ~80MB ONNX/SBERT assets; allow network time.  
> If you use **Cloudflare WARP / Corp VPN** and see SSL errors (`SSLCertVerificationError`), **temporarily disable** the VPN or configure your corporate CA bundle.

---

## 🗃 Vector Store Management

- **Where:** `vector_store/` (configurable via `.env: VECTOR_STORE_PATH`).  
- **Rebuild from scratch:**  
  ```bash
  rm -rf vector_store/*
  python -m scripts.pipeline all
  ```
- **Quick sanity checks:**
  ```bash
  python -m scripts.verify_embeddings
  python -m scripts.check_embedding_progress
  ```

---

## 🤖 Run the Agents

### Start
Use the provided launcher (uses your **.venv**, **not conda**):
```bash
./agents_start.sh
# Output:
# ▶️  Starting rca_agent on 127.0.0.1:9131 …
# ▶️  Starting sop_agent on 127.0.0.1:9132 …
# ▶️  Starting ticket_agent on 127.0.0.1:9133 …
# ▶️  Starting super_agent on 127.0.0.1:9191 …
```

> If you see `conda: command not found`, you’re using an older script.  
> This repo’s `agents_start.sh` is **venv‑based** and does not require Conda.

### Stop
```bash
./agents_stop.sh
```

### Test
```bash
# Safe test with mocked LLM (no costs):
MOCK_LLM=1 ./agents_test.sh

# Normal test (will call OpenAI if MOCK_LLM=0 and OPENAI_API_KEY set):
./agents_test.sh
```

The tester hits:
- `RCA`: `http://127.0.0.1:9131/rca`
- `SOP`: `http://127.0.0.1:9132/sop`
- `Ticket`: `http://127.0.0.1:9133/ticket`
- `Super`: `http://127.0.0.1:9191/super` (routes to RCA/SOP/Ticket)

It prints **HTTP status** and a **response snippet**.

### Mock Mode
- Set `MOCK_LLM=1` in `.env` **or** prefix the command:  
  `MOCK_LLM=1 ./agents_test.sh`  
- On startup, agents log that **mock mode** is on.  
- If you still see costs in your OpenAI usage, one of the agents might not be reading `.env`. **Restart agents** and tail logs:
  ```bash
  tail -f logs/*.log
  ```

### Ports
- RCA: **9131**  
- SOP: **9132**  
- Ticket: **9133**  
- Super: **9191**

---

## 🧰 Scripts Reference

**Pipeline**
- `python -m scripts.pipeline all` → end‑to‑end (extract → embed)
- `scripts/extract_and_caption.py` → extraction & BLIP captions
- `scripts/embed.py` → build/update Chroma vector store
- `scripts/verify_embeddings.py` / `scripts/check_embedding_progress.py` → inspections

**Agents**
- `scripts/agents/shared.py` → Chroma loader (⚠️ LangChain deprecation notice: use `langchain_chroma`).
  - If you see:  
    `LangChainDeprecationWarning: The class 'Chroma' was deprecated…`  
    Prefer:  
    ```python
    from langchain_chroma import Chroma
    ```
    and ensure `langchain-chroma` is installed (already in requirements).
- `scripts/agents/*_agent.py` → individual FastAPI apps

**Shell Launchers**
- `agents_start.sh` → start all agents (venv)  
- `agents_stop.sh` → stop all agents  
- `agents_test.sh` → curl tests with timeouts & retries

---

## 🛠 Troubleshooting & Known Issues

### 1) SSL errors to Hugging Face
```
SSLCertVerificationError: self-signed certificate in certificate chain
```
- Usually due to **VPN (Cloudflare WARP)** or corp proxy interception.  
- Fix: temporarily **disable WARP** during the first model download, or set your CA bundle properly.

### 2) PPTX `PackageNotFoundError`
- The path printed does not exist (often due to filename mismatch).  
- Ensure the file is actually in `raw/` with the **exact** name.

### 3) DOCX “not a ZIP archive”
- File is corrupted or not a real `.docx`.  
- Re‑save via MS Word or LibreOffice: *File → Save As → .docx*.

### 4) XLSX extractor missing
- Install `pip install "unstructured[xlsx]"`.

### 5) HuggingFace tokenizers fork warning
```
huggingface/tokenizers: The current process just got forked...
```
- Set `TOKENIZERS_PARALLELISM=false` in `.env` (already suggested).

### 6) LangChain Chroma deprecation
- Import from `langchain_chroma` instead of `langchain.vectorstores`.  
- Already handled in requirements; adjust imports in `scripts/agents/shared.py` if needed.

### 7) Unexpected OpenAI spend in mock mode
- Ensure agents load `.env` and **MOCK_LLM=1** is set **before start**.  
- Restart agents. Confirm logs mention mock mode.  
- Use `MOCK_LLM=1 ./agents_test.sh` to force mock for the test runner.

---

## 🛡 Cost Control / Safety Notes

- **Default to mock during development**: `MOCK_LLM=1`.  
- Only switch to live (`MOCK_LLM=0`) when you’re confident.  
- **Test only one agent** at a time if you’re live.  
- Keep logs open (`tail -f logs/*.log`) to see if any agent hits OpenAI.

---

## ⚠️ Common Pitfalls

- Forgetting to activate `.venv` → packages “missing”.  
- Changing `.env` **without restarting** agents.  
- Expecting `wkhtmltopdf` — not required here (Homebrew cask is disabled).  
- Running pipeline while VPN blocks SSL (first‑run model downloads).  
- Re‑running pipeline without clearing the vector store when you need a clean rebuild.

---

## 🧾 Cheatsheet

```bash
# 0) One-time setup
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip wheel setuptools
pip install -r requirements.txt
pip install "unstructured[docx]" "unstructured[xlsx]" "unstructured[pptx]"
brew install imagemagick ghostscript poppler tesseract ffmpeg cmake
brew install --cask libreoffice
cp .env.example .env   # if provided; otherwise create as shown above
# Edit .env: MOCK_LLM=1 for safe dev

# 1) Prepare data
mkdir -p raw
# Drop your .pptx/.docx/.xlsx/.pdf files into raw/

# 2) Build vectors
python -m scripts.pipeline all

# 3) Start agents (reads .env)
./agents_start.sh
tail -f logs/*.log  # in a separate tab (confirm mock mode)

# 4) Test safely
MOCK_LLM=1 ./agents_test.sh

# 5) Stop
./agents_stop.sh

# 6) Clean rebuild (if needed)
rm -rf vector_store/*
python -m scripts.pipeline all
```

---

If anything here is unclear or you hit a new edge case, please open an issue with logs and your environment details. Happy building! 🚀