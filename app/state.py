from dataclasses import dataclass

from qdrant_client import QdrantClient


@dataclass
class AppState:
    qdrant: QdrantClient | None = None


state = AppState()
