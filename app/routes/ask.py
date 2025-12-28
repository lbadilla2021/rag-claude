from fastapi import APIRouter

from app.config import logger
from app.schemas import AskRequest
from app.services.openai_service import route_intent
from app.services.rag import ask_rag, preview_rag_hits

router = APIRouter()


@router.post("/ask")
def ask(payload: AskRequest):
    decision = route_intent(payload.question)
    logger.info("🧭 Ruta detectada: %s (%s)", decision.route, decision.confidence)

    if decision.route == "rag":
        return ask_rag(payload)

    if preview_rag_hits(payload.question):
        logger.info("📚 Forzando RAG por evidencia documental")
        return ask_rag(payload)

    return {
        "answer": (
            f"Esta consulta fue clasificada como '{decision.route}'. "
            "La respuesta por agente especialista está en implementación."
        ),
        "sources": [],
    }
