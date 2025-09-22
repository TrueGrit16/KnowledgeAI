# KnowledgeAI — End‑to‑End Setup & User Guide (Backend + Frontend Chat)

This is the **single source of truth** to set up KnowledgeAI on a fresh machine, prepare the RAG data, run the backend API, and launch the **frontend chat** UI. It captures all the practical gotchas we hit while bringing the stack up on macOS.

---

## 📑 Table of Contents
1. [What You Get](#what-you-get)  
2. [Architecture at a Glance](#architecture-at-a-glance)  
3. [Directory Structure](#directory-structure)  
4. [Prerequisites](#prerequisites)  
5. [Python Backend Setup](#python-backend-setup)  
6. [RAG Data Prep & Pipeline](#rag-data-prep--pipeline)  
7. [Start the Backend API](#start-the-backend-api)  
8. [Frontend (Vite + React + Tailwind)](#frontend-vite--react--tailwind)  
9. [Run the Chat End‑to‑End](#run-the-chat-end-to-end)  
10. [Scripts Reference](#scripts-reference)  
11. [Troubleshooting](#troubleshooting)  
12. [Cheatsheet](#cheatsheet)

---

## ✅ What You Get

- A **document pipeline** (extract → caption images → chunk → embed to Chroma).
- **Four agents** (RCA, SOP, Ticket, Super) you can run locally via FastAPI.
- A **simple chat UI** (Vite + React + Tailwind) that talks to the backend `POST /chat` endpoint.

---

## 🧩 Architecture at a Glance

- **Pipeline** (Python): `scripts/pipeline.py` orchestrates:
  - `scripts/extract_and_caption.py` → uses *unstructured* + BLIP to parse docs & caption images.
  - `scripts/embed.py` → builds Chroma vector DB with SBERT (`BAAI/bge-base-en`).
- **Agents** (Python/FastAPI): live under `scripts/agents/`; helper in `scripts/agents/shared.py`.
- **Backend API** (Python/FastAPI): `backend/main.py`, route mounted in `backend/routes/chat.py` exposes `POST /chat`.
- **Frontend** (Vite/React/Tailwind): under `frontend/`. The UI posts to `/chat` (Vite proxy → backend).

---

## 📂 Directory Structure

```
KnowledgeAI/
├── backend/
│   ├── logs/
│   │   └── chat.log                 # created/used by backend chat route
│   ├── routes/
│   │   ├── __init__.py
│   │   └── chat.py                  # POST /chat
│   └── main.py                      # FastAPI app (imports routes, CORS, etc.)
├── clean/                           # optional exports
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chat.tsx
│   │   │   ├── ChatBubble.tsx
│   │   │   └── ChatInput.tsx
│   │   ├── pages/App.tsx
│   │   ├── styles/index.css
│   │   ├── utils/api.ts
│   │   └── main.tsx
│   ├── .env                         # (optional) front-end overrides
│   ├── index.html
│   ├── package.json
│   ├── postcss.config.cjs
│   ├── tailwind.config.js
│   └── vite.config.ts               # includes proxy for /chat → http://127.0.0.1:8000
├── logs/
├── raw/                             # put your source documents here
├── raw_imgs/                        # extracted images
├── scripts/
│   ├── agents/
│   │   ├── rca_agent.py
│   │   ├── sop_agent.py
│   │   ├── ticket_agent.py
│   │   ├── super_agent.py
│   │   └── shared.py
│   ├── assistants/                  # helper utilities
│   ├── extract_and_caption.py
│   ├── embed.py
│   ├── verify_embeddings.py
│   ├── check_embedding_progress.py
│   ├── tools_rag.py
│   └── pipeline.py
├── vector_store/                    # Chroma DB
├── agents_start.sh / agents_stop.sh / agents_test.sh
├── requirements.txt
└── .env                             # backend/agents environment
```

---

## 🧰 Prerequisites

- **macOS** (Apple Silicon OK) or Linux/WSL  
- **Python 3.11** recommended  
- **Node.js 18+** (Node 20+ recommended) and `npm`  
- **Git**  
- OpenAI API key (only if you intend to call OpenAI; the chat route can also use local answers, depending on your code path)

---

## 🐍 Python Backend Setup

1. **Create & activate venv**
   ```bash
   cd KnowledgeAI
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip wheel setuptools
   ```

2. **Install Python deps**
   ```bash
   pip install -r requirements.txt

   # Extras used by unstructured for Office docs
   pip install "unstructured[docx]" "unstructured[xlsx]" "unstructured[pptx]"
   ```

3. **System packages (macOS)**
   ```bash
   brew install imagemagick ghostscript poppler tesseract ffmpeg cmake
   brew install --cask libreoffice
   ```

4. **Backend env (.env at repo root)**
   ```env
   # === Backend / RAG ===
   VECTOR_STORE_PATH=./vector_store

   # === Logging ===
   LOG_LEVEL=INFO
   TOKENIZERS_PARALLELISM=false
   HF_HUB_DISABLE_TELEMETRY=1

   # === LLM (optional) ===
   OPENAI_API_KEY=
   ```

---

## 📦 RAG Data Prep & Pipeline

1. Place documents in `raw/` (`.pptx`, `.docx`, `.xlsx`, `.pdf`, `.txt`, images).
2. Build vectors:
   ```bash
   python -m scripts.pipeline all
   ```
   - First run will download HF models (BLIP + SBERT). If you use Cloudflare WARP/corp VPN and hit SSL issues, temporarily disable it.

---

## 🚀 Start the Backend API

1. Ensure the backend log directory exists **once**:
   ```bash
   mkdir -p backend/logs
   ```
2. Launch API:
   ```bash
   uvicorn backend.main:app --reload --port 8000
   ```
   - FastAPI will serve on `http://127.0.0.1:8000`.
   - `backend/routes/chat.py` appends to `backend/logs/chat.log` (created automatically if the directory exists).

---

## 💻 Frontend (Vite + React + Tailwind)

> The UI posts to `/chat`. Vite’s dev server proxies `/chat` → `http://127.0.0.1:8000` (see `vite.config.ts`).  
> **Therefore, start the backend first** to avoid `ECONNREFUSED` at the proxy.

1. **Install Node deps**
   ```bash
   cd frontend
   npm ci         # or: npm install
   ```

2. **(Optional) Frontend .env**  
   If you want to override the default proxy/URLs, create `frontend/.env`:
   ```env
   # example — only if you changed backend port/host
   VITE_BACKEND_URL=http://127.0.0.1:8000
   ```
   Ensure `utils/api.ts` reads this if present; otherwise the proxy handles `/chat`.

3. **Run the dev server**
   ```bash
   npm run dev
   ```
   - Vite opens `http://localhost:5173`.
   - When you send a message, the UI sends `POST /chat` which the dev proxy forwards to `http://127.0.0.1:8000/chat`.

4. **Build for production**
   ```bash
   npm run build
   npm run preview  # optional local preview
   ```

---

## 🔗 Run the Chat End‑to‑End

1. Terminal A (repo root):
   ```bash
   source .venv/bin/activate
   uvicorn backend.main:app --reload --port 8000
   ```
2. Terminal B:
   ```bash
   cd frontend
   npm run dev
   ```
3. Open the browser at `http://localhost:5173`, type in the chat box, and hit **Enter**.  
   Check `backend/logs/chat.log` for request/response traces.

---

## 📜 Scripts Reference

**Pipeline**
- `python -m scripts.pipeline all` — end‑to‑end doc processing
- `scripts/extract_and_caption.py` — unstructured + BLIP captions
- `scripts/embed.py` — Chroma embeddings
- `scripts/verify_embeddings.py`, `scripts/check_embedding_progress.py` — diagnostics

**Agents (optional)**
- `./agents_start.sh` — start RCA/SOP/Ticket/Super on ports 9131/9132/9133/9191
- `./agents_stop.sh`, `./agents_test.sh`

**Backend**
- `backend/main.py` — FastAPI app
- `backend/routes/chat.py` — `POST /chat` handler + logging

**Frontend**
- `frontend/src/components/Chat.tsx`, `ChatBubble.tsx`, `ChatInput.tsx`
- `frontend/src/utils/api.ts` — HTTP client
- `frontend/vite.config.ts` — dev proxy for `/chat`

---

## 🧯 Troubleshooting

**1) Vite “http proxy error: /chat ECONNREFUSED”**  
Cause: Backend isn’t running or wrong port.  
Fix:
```bash
uvicorn backend.main:app --reload --port 8000
# verify: curl -i http://127.0.0.1:8000/docs
```

**2) 500 from /chat – FileNotFoundError for `backend/logs/chat.log`**  
Cause: Directory missing on first run.  
Fix:
```bash
mkdir -p backend/logs
# restart uvicorn
```

**3) Unstructured errors (PPTX/DOCX/XLSX)**  
- `PackageNotFoundError` → file missing/misnamed in `raw/`.
- “not a ZIP archive” → re-save the DOCX in Word/LibreOffice.
- Install extras:  
  `pip install "unstructured[docx]" "unstructured[xlsx]" "unstructured[pptx]"`

**4) SSL errors when downloading models**  
Disable Cloudflare WARP / corp VPN temporarily or configure your CA bundle.

**5) CORS errors (in production without Vite proxy)**  
Expose the backend with proper CORS in `backend/main.py` or use a reverse proxy (Nginx/Caddy) to forward `/chat`.

---

## 🗒️ Cheatsheet

```bash
# One-time
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip wheel setuptools
pip install -r requirements.txt
pip install "unstructured[docx]" "unstructured[xlsx]" "unstructured[pptx]"
brew install imagemagick ghostscript poppler tesseract ffmpeg cmake
brew install --cask libreoffice

# Data → vectors
mkdir -p raw backend/logs
python -m scripts.pipeline all

# Backend
uvicorn backend.main:app --reload --port 8000

# Frontend
cd frontend
npm ci
npm run dev
```

---

If you hit a new edge case, open an issue with the failing command, full stack trace, and OS/Node/Python versions. Happy shipping! 🚀