import os
import uuid
from datetime import datetime
from typing import List

import openai
from fastapi import HTTPException, UploadFile
from PyPDF2 import PdfReader
from qdrant_client.models import FieldCondition, Filter, MatchValue, PointStruct

from app.config import EMBEDDING_MODEL, QDRANT_COLLECTION, UPLOAD_DIR, logger
from app.models import Document, DocumentChunk
from app.services.text_splitter import splitter
from app.state import state


async def index_document(file: UploadFile, db) -> dict:
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Solo se aceptan PDF")

    doc_id = str(uuid.uuid4())
    filepath = os.path.join(UPLOAD_DIR, file.filename)
    qdrant_upserted = False

    try:
        with open(filepath, "wb") as handle:
            handle.write(await file.read())

        reader = PdfReader(filepath)
        text = "\n".join(p.extract_text() or "" for p in reader.pages)

        if not text.strip():
            raise HTTPException(400, "El PDF no contiene texto")

        chunks = splitter.split_text(text)

        document = Document(
            id=doc_id,
            filename=file.filename,
            status="uploaded",
            created_at=datetime.utcnow(),
        )
        db.add(document)

        for i, chunk in enumerate(chunks):
            db.add(DocumentChunk(
                id=str(uuid.uuid4()),
                document_id=doc_id,
                content=chunk,
                chunk_index=i,
                created_at=datetime.utcnow(),
            ))

        document.chunk_count = len(chunks)
        document.status = "chunked"

        points: List[PointStruct] = []

        for i, chunk in enumerate(chunks):
            response = openai.Embedding.create(
                model=EMBEDDING_MODEL,
                input=chunk,
            )
            emb = response["data"][0]["embedding"]

            points.append(PointStruct(
                id=str(uuid.uuid4()),
                vector=emb,
                payload={
                    "document_id": doc_id,
                    "chunk_index": i,
                    "filename": file.filename,
                    "content": chunk,
                },
            ))

        state.qdrant.upsert(
            collection_name=QDRANT_COLLECTION,
            points=points,
        )
        qdrant_upserted = True

        document.status = "indexed"
        document.indexed_at = datetime.utcnow()
        db.commit()

        logger.info("✅ Documento %s indexado", file.filename)

        return {
            "id": doc_id,
            "filename": file.filename,
            "chunks": len(chunks),
            "status": "indexed",
        }
    except Exception:
        if qdrant_upserted:
            try:
                state.qdrant.delete(
                    collection_name=QDRANT_COLLECTION,
                    points_selector=Filter(
                        must=[
                            FieldCondition(
                                key="document_id",
                                match=MatchValue(value=doc_id),
                            )
                        ]
                    ),
                )
            except Exception as cleanup_exc:
                logger.warning(
                    "No se pudo limpiar Qdrant para %s: %s",
                    file.filename,
                    cleanup_exc,
                )

        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError as cleanup_exc:
                logger.warning(
                    "No se pudo eliminar el archivo %s: %s",
                    filepath,
                    cleanup_exc,
                )
        raise
