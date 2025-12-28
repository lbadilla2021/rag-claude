import os
import uuid
import logging
import json

from datetime import datetime
from typing import List

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import OperationalError

from PyPDF2 import PdfReader

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

from langchain_text_splitters import RecursiveCharacterTextSplitter

import openai

from pydantic import BaseModel


# =========================================================
# CONFIGURACIÓN
# =========================================================

DATABASE_URL = os.getenv("DATABASE_URL")

QDRANT_HOST = os.getenv("QDRANT_HOST", "apex-qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "documents")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/app/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("apex-rag-backend")


# ========================================================= 
# MODELOS Pydantic
# =========================================================

class AskRequest(BaseModel):
    question: str
    top_k: int = 5

class RouteDecision(BaseModel):
    route: str
    confidence: float

class AskSource(BaseModel):
    document_id: str | None
    filename: str | None
    chunk_index: int | None
    score: float

class AskResponse(BaseModel):
    answer: str
    sources: list[AskSource]


# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(title="Apex AI – RAG Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# DATABASE
# =========================================================

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    indexed_at = Column(DateTime)
    chunk_count = Column(Integer, default=0)


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String, primary_key=True)
    document_id = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False)


# =========================================================
# SERVICIOS
# =========================================================

qdrant: QdrantClient | None = None

splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100
)

# =========================================================
# FUNCIONES ASK
# =========================================================

def embed_query(text: str) -> list[float]:
    response = openai.Embedding.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response["data"][0]["embedding"]


def generate_answer(question: str, context: str) -> str:
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres un sistema RAG estricto.\n"
                        "REGLAS OBLIGATORIAS:\n"
                        "- Usa EXCLUSIVAMENTE el contenido del contexto.\n"
                        "- Cada afirmación relevante DEBE incluir una cita explícita.\n"
                        "- Usa el formato (FUENTE X).\n"
                        "- NO uses conocimiento previo.\n"
                        "- NO inventes información.\n"
                        "- Si el contexto no contiene la respuesta, responde EXACTAMENTE:\n"
                        "  'No hay información suficiente en los documentos cargados.'\n"
                        "- Responde en español formal.\n"
                        "- Está PROHIBIDO escribir afirmaciones sin '(FUENTE X)'.\n"
                        "- Si no puedes respaldar una afirmación con una FUENTE, no la incluyas.\n"
                    )
                },
                {
                    "role": "user",
                    "content": (
                        "CONTEXTO DOCUMENTAL:\n"
                        f"{context}\n\n"
                        "PREGUNTA DEL USUARIO:\n"
                        f"{question}\n\n"
                        "INSTRUCCIONES DE RESPUESTA:\n"
                        "- Responde SOLO con base en el contexto.\n"
                        "- Cuando cites texto literal del contexto, encierra la frase entre comillas.\n"
                        "- Incluye la referencia correspondiente en formato (FUENTE X).\n"
                    )
                }
            ],
            temperature=0.2,
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error("❌ Error generando respuesta", exc_info=e)
        raise HTTPException(status_code=500, detail="Error generando respuesta IA")


def route_intent(question: str) -> RouteDecision:
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres un clasificador de intención.\n"
                    "Tu única tarea es clasificar la pregunta en UNA sola ruta.\n\n"
                    "Rutas posibles:\n"
                    "- rag → preguntas que deben responderse usando documentos cargados\n"
                    "- hr → recursos humanos, ética, legislación laboral\n"
                    "- legal → cumplimiento normativo, contratos, leyes\n"
                    "- technical → tecnología, sistemas, soporte TI\n"
                    "- training → capacitación, cursos, formación\n\n"
                    "Responde SOLO en JSON válido, sin texto adicional.\n"
                    "Formato EXACTO:\n"
                    "{ \"route\": \"rag|hr|legal|technical|training\", \"confidence\": 0.0 }"
                )
            },
            {
                "role": "user",
                "content": question
            }
        ],
        temperature=0
    )

    content = response["choices"][0]["message"]["content"]

    return RouteDecision(**json.loads(content))

def preview_rag_hits(question: str, score_threshold: float = 0.25) -> bool:
    query_vector = embed_query(question)

    results = qdrant.search(
        collection_name=QDRANT_COLLECTION,
        query_vector=query_vector,
        limit=1
    )

    if not results:
        return False

    return results[0].score >= score_threshold

def answer_with_agent(question: str, agent: str):
    return {
        "answer": f"Esta consulta fue derivada al agente {agent}. Implementación en progreso.",
        "sources": []
    }

# =========================================================
# STARTUP
# =========================================================

@app.on_event("startup")
def startup():
    global qdrant

    logger.info("🚀 Iniciando backend Apex RAG...")

    # DB
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ PostgreSQL listo")
    except OperationalError as e:
        logger.error("❌ PostgreSQL no disponible", exc_info=e)
        raise

    # OpenAI clásica
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY no configurada")

    openai.api_key = OPENAI_API_KEY
    logger.info("✅ OpenAI configurado (API clásica)")

    # Qdrant
    qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    collections = [c.name for c in qdrant.get_collections().collections]
    if QDRANT_COLLECTION not in collections:
        qdrant.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(
                size=1536,
                distance=Distance.COSINE
            ),
        )
        logger.info("📦 Colección Qdrant creada")
    else:
        logger.info("📦 Colección Qdrant existente")

# =========================================================
# ENDPOINTS
# =========================================================

@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/documents")
def list_documents():
    db = SessionLocal()
    try:
        docs = db.query(Document).order_by(Document.created_at.desc()).all()
        return [
            {
                "id": d.id,
                "filename": d.filename,
                "status": d.status,
                "chunks": d.chunk_count,
                "createdAt": d.created_at.isoformat(),
                "indexedAt": d.indexed_at.isoformat() if d.indexed_at else None,
                "size": 0,
                "type": "PDF",
                "category": "General",
            }
            for d in docs
        ]
    finally:
        db.close()



@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Solo se aceptan PDF")

    db = SessionLocal()
    doc_id = str(uuid.uuid4())
    filepath = os.path.join(UPLOAD_DIR, file.filename)

    try:
        with open(filepath, "wb") as f:
            f.write(await file.read())

        document = Document(
            id=doc_id,
            filename=file.filename,
            status="uploaded",
            created_at=datetime.utcnow()
        )
        db.add(document)
        db.commit()

        reader = PdfReader(filepath)
        text = "\n".join(p.extract_text() or "" for p in reader.pages)

        if not text.strip():
            raise HTTPException(400, "El PDF no contiene texto")

        chunks = splitter.split_text(text)

        for i, chunk in enumerate(chunks):
            db.add(DocumentChunk(
                id=str(uuid.uuid4()),
                document_id=doc_id,
                content=chunk,
                chunk_index=i,
                created_at=datetime.utcnow()
            ))

        document.chunk_count = len(chunks)
        document.status = "chunked"
        db.commit()

        points: List[PointStruct] = []

        for i, chunk in enumerate(chunks):
            response = openai.Embedding.create(
                model=EMBEDDING_MODEL,
                input=chunk
            )
            emb = response["data"][0]["embedding"]

            points.append(PointStruct(
                id=str(uuid.uuid4()),
                vector=emb,
                payload={
                    "document_id": doc_id,
                    "chunk_index": i,
                    "filename": file.filename,
                    "content": chunk   # 🔴 CLAVE
                }
            ))

        qdrant.upsert(
            collection_name=QDRANT_COLLECTION,
            points=points
        )

        document.status = "indexed"
        document.indexed_at = datetime.utcnow()
        db.commit()

        logger.info(f"✅ Documento {file.filename} indexado")

        return {
            "id": doc_id,
            "filename": file.filename,
            "chunks": len(chunks),
            "status": "indexed"
        }

    except Exception as e:
        db.rollback()
        logger.error("❌ Error procesando documento", exc_info=e)
        raise HTTPException(500, str(e))

    finally:
        db.close()

@app.post("/api/ask")
def ask(payload: AskRequest):

    # 1. Router de intención
    decision = route_intent(payload.question)
    logger.info(f"🧭 Ruta detectada: {decision.route} ({decision.confidence})")

    # 2. Regla dura: RAG siempre primero si corresponde
    if decision.route == "rag":
        return ask_rag(payload)

    # 3. Si NO es RAG, pero RAG tiene contexto relevante → usar RAG
    if preview_rag_hits(payload.question):
        logger.info("📚 Forzando RAG por evidencia documental")
        return ask_rag(payload)

    # 4. Derivar a agente (stub por ahora)
    return {
        "answer": (
            f"Esta consulta fue clasificada como '{decision.route}'. "
            "La respuesta por agente especialista está en implementación."
        ),
        "sources": []
    }

def ask_rag(payload: AskRequest) -> AskResponse:

    # 1. Embedding de la pregunta
    query_vector = embed_query(payload.question)

    # 2. Búsqueda semántica
    search_results = qdrant.search(
        collection_name=QDRANT_COLLECTION,
        query_vector=query_vector,
        limit=payload.top_k
    )

    # ==============================
    # ETAPA 3.A — Umbral mínimo
    # ==============================
    MIN_SCORE = 0.25
    search_results = [
        hit for hit in search_results
        if hit.score >= MIN_SCORE
    ]

    if not search_results:
        return {
            "answer": "No hay información suficiente en los documentos cargados.",
            "sources": []
        }

    # ==============================
    # ETAPA 3.B — Deduplicación
    # ==============================
    seen = set()
    filtered_hits = []

    for hit in search_results:
        key = (
            hit.payload.get("document_id"),
            hit.payload.get("chunk_index")
        )
        if key not in seen:
            seen.add(key)
            filtered_hits.append(hit)

    # ==============================
    # ETAPA 3.C — Limitar contexto
    # ==============================
    filtered_hits = sorted(
        filtered_hits,
        key=lambda h: h.score,
        reverse=True
    )[:5]

    # ==============================
    # Construcción del contexto (con fuentes)
    # ==============================
    context_chunks = []
    sources = []

    for idx, hit in enumerate(filtered_hits, start=1):
        payload_data = hit.payload or {}
        content = payload_data.get("content", "").strip()

        context_chunks.append(
            f"[FUENTE {idx}] Documento: {payload_data.get('filename')} | Chunk: {payload_data.get('chunk_index')}\n"
            f"{content}"
        )

        sources.append({
            "source_id": idx,
            "document_id": payload_data.get("document_id"),
            "filename": payload_data.get("filename"),
            "chunk_index": payload_data.get("chunk_index"),
            "score": round(hit.score, 4),
        })

    context = "\n\n".join(context_chunks)
    
    # ==============================
    # Generar respuesta con citas
    # ==============================
    answer = generate_answer(
        question=payload.question,
        context=context
    )

    return {
        "answer": answer,
        "sources": sources
    }


# =========================================================