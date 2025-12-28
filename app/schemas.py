from pydantic import BaseModel


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
