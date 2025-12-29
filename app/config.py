import logging
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://apex_user:apex_password@postgres:5432/apex_rag",
)

QDRANT_HOST = os.getenv("QDRANT_HOST", "apex-qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "documents")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/app/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("apex-rag-backend")
