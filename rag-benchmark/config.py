import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY  = os.getenv("GEMINI_API_KEY")
EMBEDDING_MODEL = "models/gemini-embedding-001"
GEMINI_MODEL    = "gemini-3.1-flash"
CHUNK_SIZE      = 512
CHUNK_OVERLAP   = 50
TOP_K           = 5