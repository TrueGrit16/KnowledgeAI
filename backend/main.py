from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import chat      

app = FastAPI()

# --- CORS ---------------------------------------------------------------
origins = [
    "http://localhost:5173",      # Vite dev
    "http://127.0.0.1:5173",
    # add prod URL here later
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # or ["*"] while developing
    allow_credentials=True,
    allow_methods=["*"],          # POST / GET / OPTIONS / …
    allow_headers=["*"],
)
# -----------------------------------------------------------------------

app.include_router(chat.router)