import openai
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError

from app.config import OPENAI_API_KEY, logger
from app.db import Base, engine
from app.routes import ask as ask_routes
from app.routes import documents as document_routes
from app.routes import health as health_routes
from app.services.qdrant_service import init_qdrant
from app.state import state

app = FastAPI(title="Apex AI – RAG Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_routes.router, prefix="/api")
app.include_router(document_routes.router, prefix="/api")
app.include_router(ask_routes.router, prefix="/api")


@app.on_event("startup")
def startup():
    logger.info("🚀 Iniciando backend Apex RAG...")

    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ PostgreSQL listo")
    except OperationalError as exc:
        logger.error("❌ PostgreSQL no disponible", exc_info=exc)
        raise

    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY no configurada")

    openai.api_key = OPENAI_API_KEY
    logger.info("✅ OpenAI configurado (API clásica)")

    state.qdrant = init_qdrant()
