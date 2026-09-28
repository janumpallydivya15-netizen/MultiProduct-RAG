import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# Secret Key & Debug settings
SECRET_KEY = os.getenv("SECRET_KEY", "multimodal-rag-secret-key-2026")
DEBUG = os.getenv("FLASK_DEBUG", "True").lower() in ["true", "1"]

# Storage Paths
DATA_DIR = BASE_DIR / "data"
UPLOAD_FOLDER = DATA_DIR / "uploads"
CHROMADB_DIR = DATA_DIR / "chromadb"

# Ensure directories exist
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
CHROMADB_DIR.mkdir(parents=True, exist_ok=True)

# Allowed file extensions
ALLOWED_DOC_EXTENSIONS = {"pdf", "txt", "md"}
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32 MB

# AI & Embedding Models
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
GEMINI_RAG_MODEL = os.getenv("GEMINI_RAG_MODEL", "gemini-3.5-flash-lite")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")

# RAG & Chunking Settings
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K_RESULTS = 4
