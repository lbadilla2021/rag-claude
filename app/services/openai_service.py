import json

import openai
from fastapi import HTTPException

from app.config import EMBEDDING_MODEL, logger
from app.schemas import RouteDecision


def embed_query(text: str) -> list[float]:
    response = openai.Embedding.create(
        model=EMBEDDING_MODEL,
        input=text,
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
                    ),
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
                    ),
                },
            ],
            temperature=0.2,
        )
        return response["choices"][0]["message"]["content"]
    except Exception as exc:
        logger.error("❌ Error generando respuesta", exc_info=exc)
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
                    '{ "route": "rag|hr|legal|technical|training", "confidence": 0.0 }'
                ),
            },
            {
                "role": "user",
                "content": question,
            },
        ],
        temperature=0,
    )

    content = response["choices"][0]["message"]["content"]

    return RouteDecision(**json.loads(content))
