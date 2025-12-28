import openai
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
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
        with engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS documents "
                    "ADD COLUMN IF NOT EXISTS title VARCHAR NOT NULL DEFAULT ''"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS documents "
                    "ADD COLUMN IF NOT EXISTS category VARCHAR"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS documents "
                    "ADD COLUMN IF NOT EXISTS owner_area VARCHAR"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS documents "
                    "ADD COLUMN IF NOT EXISTS status VARCHAR NOT NULL DEFAULT 'active'"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS documents "
                    "ADD COLUMN IF NOT EXISTS created_at TIMESTAMP NOT NULL DEFAULT NOW()"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS documents "
                    "ADD COLUMN IF NOT EXISTS indexed_at TIMESTAMP"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS documents "
                    "ADD COLUMN IF NOT EXISTS chunk_count INTEGER NOT NULL DEFAULT 0"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS document_versions "
                    "ADD COLUMN IF NOT EXISTS filename VARCHAR NOT NULL DEFAULT ''"
                )
            )
        logger.info("✅ PostgreSQL listo")
    except OperationalError as exc:
        logger.error("❌ PostgreSQL no disponible", exc_info=exc)
        raise

    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY no configurada")

    openai.api_key = OPENAI_API_KEY
    logger.info("✅ OpenAI configurado (API clásica)")

    state.qdrant = init_qdrant()
