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


class DocumentUpdate(BaseModel):
    title: str | None = None
    filename: str | None = None
    category: str | None = None
    status: str | None = None
    owner: str | None = None
    owner_area: str | None = None
    department: str | None = None
    tags: list[str] | None = None
    description: str | None = None
    public: bool | None = None
    indexable: bool | None = None
