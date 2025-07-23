from pathlib import Path
import os
from openai import OpenAI
from langchain_community.vectorstores import Chroma

BASE = Path(__file__).resolve().parent.parent.parent
VECTOR_DIR = BASE / "vector_store"

vectordb = Chroma(
    persist_directory=str(VECTOR_DIR),
    collection_name="knowledge_base"
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
