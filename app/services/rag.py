from qdrant_client.models import FieldCondition, Filter, MatchValue

from app.config import QDRANT_COLLECTION
from app.schemas import AskRequest, AskResponse
from app.services.openai_service import embed_query, generate_answer
from app.state import state


def preview_rag_hits(question: str, score_threshold: float = 0.25) -> bool:
    query_vector = embed_query(question)

    results = state.qdrant.search(
        collection_name=QDRANT_COLLECTION,
        query_vector=query_vector,
        query_filter=Filter(
            must=[
                FieldCondition(
                    key="is_current",
                    match=MatchValue(value=True),
                ),
                FieldCondition(
                    key="deleted",
                    match=MatchValue(value=False),
                ),
            ]
        ),
        limit=1,
    )

    if not results:
        return False

    return results[0].score >= score_threshold


def ask_rag(payload: AskRequest) -> AskResponse:
    query_vector = embed_query(payload.question)

    search_results = state.qdrant.search(
        collection_name=QDRANT_COLLECTION,
        query_vector=query_vector,
        query_filter=Filter(
            must=[
                FieldCondition(
                    key="is_current",
                    match=MatchValue(value=True),
                ),
                FieldCondition(
                    key="deleted",
                    match=MatchValue(value=False),
                ),
            ]
        ),
        limit=payload.top_k,
    )

    min_score = 0.25
    search_results = [
        hit for hit in search_results
        if hit.score >= min_score
    ]

    if not search_results:
        return {
            "answer": "No hay información suficiente en los documentos cargados.",
            "sources": [],
        }

    seen = set()
    filtered_hits = []

    for hit in search_results:
        key = (
            hit.payload.get("document_id"),
            hit.payload.get("chunk_index"),
        )
        if key not in seen:
            seen.add(key)
            filtered_hits.append(hit)

    filtered_hits = sorted(
        filtered_hits,
        key=lambda h: h.score,
        reverse=True,
    )[:5]

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

    answer = generate_answer(
        question=payload.question,
        context=context,
    )

    return {
        "answer": answer,
        "sources": sources,
    }
