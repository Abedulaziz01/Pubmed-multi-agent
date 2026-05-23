import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
NCBI_EMAIL = os.getenv("NCBI_EMAIL")

LLM_MODEL = "llama-3.1-8b-instant"
MAX_PUBMED_RESULTS = 50
CHROMA_PERSIST_DIR = "./chroma_db"
DB_PATH = "./feedback.db"