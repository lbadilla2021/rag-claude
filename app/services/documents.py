import hashlib
import os
import uuid
from datetime import datetime
from io import BytesIO
from typing import Iterable, List, Tuple

import openai
from fastapi import HTTPException, UploadFile
from PyPDF2 import PdfReader
from qdrant_client.models import FieldCondition, Filter, MatchValue, PointStruct

from app.config import EMBEDDING_MODEL, QDRANT_COLLECTION, UPLOAD_DIR, logger
from app.models import Document, DocumentAudit, DocumentChunk, DocumentVersion
from app.services.text_splitter import splitter
from app.state import state


def _compare_versions(left: str, right: str) -> int:
    # Comparación simple de versiones tipo "1.0", "2.0".
    left_parts = [int(p) for p in left.split(".") if p.isdigit()]
    right_parts = [int(p) for p in right.split(".") if p.isdigit()]
    max_len = max(len(left_parts), len(right_parts))
    left_parts += [0] * (max_len - len(left_parts))
    right_parts += [0] * (max_len - len(right_parts))
    if left_parts == right_parts:
        return 0
    return 1 if left_parts > right_parts else -1


def _extract_pdf_text(file_bytes: bytes) -> str:
    # Extrae texto del PDF sin alterar el pipeline actual.
    reader = PdfReader(BytesIO(file_bytes))
    return "\n".join(p.extract_text() or "" for p in reader.pages)


def _build_embeddings(chunks: Iterable[str]) -> List[List[float]]:
    # Reutiliza la generación de embeddings existente.
    embeddings: List[List[float]] = []
    for chunk in chunks:
        response = openai.Embedding.create(
            model=EMBEDDING_MODEL,
            input=chunk,
        )
        embeddings.append(response["data"][0]["embedding"])
    return embeddings


def _store_audit(db, action: str, document_id: str, version: str | None = None) -> None:
    # Auditoría obligatoria para cambios sensibles.
    db.add(DocumentAudit(
        audit_id=str(uuid.uuid4()),
        action=action,
        document_id=document_id,
        version=version,
        created_at=datetime.utcnow(),
    ))


def _upsert_qdrant_points(
    document_id: str,
    version: str,
    filename: str,
    chunks: List[str],
    embeddings: List[List[float]],
) -> None:
    # Persistimos embeddings para retrieval sin mezclar versiones.
    points: List[PointStruct] = []
    for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=emb,
            payload={
                "document_id": document_id,
                "version": version,
                "chunk_index": idx,
                "filename": filename,
                "content": chunk,
                "is_current": True,
                "deleted": False,
            },
        ))
    state.qdrant.upsert(
        collection_name=QDRANT_COLLECTION,
        points=points,
    )


def _update_qdrant_payload(document_id: str, version: str | None, payload: dict) -> None:
    # Sincroniza flags de versionado en Qdrant.
    filters = [
        FieldCondition(
            key="document_id",
            match=MatchValue(value=document_id),
        )
    ]
    if version is not None:
        filters.append(FieldCondition(
            key="version",
            match=MatchValue(value=version),
        ))
    state.qdrant.set_payload(
        collection_name=QDRANT_COLLECTION,
        payload=payload,
        points_selector=Filter(must=filters),
    )


def _process_chunks(file_bytes: bytes) -> Tuple[List[str], List[List[float]]]:
    # Chunking + embeddings para la nueva versión.
    text = _extract_pdf_text(file_bytes)
    if not text.strip():
        raise HTTPException(400, "El PDF no contiene texto")
    chunks = splitter.split_text(text)
    embeddings = _build_embeddings(chunks)
    return chunks, embeddings


def _delete_local_files(filenames: Iterable[str]) -> None:
    for filename in filenames:
        if not filename:
            continue
        filepath = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError as exc:
                logger.warning("No se pudo eliminar el archivo %s: %s", filepath, exc)


def delete_document(document_id: str, db) -> dict:
    document = db.query(Document).filter(Document.document_id == document_id).first()
    if not document:
        raise HTTPException(404, "Documento no encontrado")

    state.qdrant.delete(
        collection_name=QDRANT_COLLECTION,
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id),
                )
            ]
        ),
    )

    db.query(DocumentChunk).filter(
        DocumentChunk.document_id == document_id
    ).delete(synchronize_session=False)
    db.query(DocumentVersion).filter(
        DocumentVersion.document_id == document_id
    ).delete(synchronize_session=False)
    db.query(DocumentAudit).filter(
        DocumentAudit.document_id == document_id
    ).delete(synchronize_session=False)
    db.query(Document).filter(
        Document.document_id == document_id
    ).delete(synchronize_session=False)

    db.commit()
    return {"document_id": document_id, "status": "deleted"}


async def index_document(
    file: UploadFile,
    db,
    title: str | None = None,
    category: str | None = None,
    owner_area: str | None = None,
    version: str = "1.0",
    change_summary: str | None = None,
) -> dict:
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Solo se aceptan PDF")

    doc_id = str(uuid.uuid4())
    version_id = str(uuid.uuid4())
    filepath = os.path.join(UPLOAD_DIR, file.filename)
    qdrant_upserted = False

    try:
        file_bytes = await file.read()
        with open(filepath, "wb") as handle:
            handle.write(file_bytes)

        chunks, embeddings = _process_chunks(file_bytes)
        now = datetime.utcnow()
        file_hash = hashlib.sha256(file_bytes).hexdigest()

        document = Document(
            document_id=doc_id,
            title=title or file.filename,
            category=category,
            owner_area=owner_area,
            filename=file.filename,
            status="active",
            created_at=now,
        )
        db.add(document)

        db.add(DocumentVersion(
            version_id=version_id,
            document_id=doc_id,
            version=version,
            effective_from=now,
            effective_to=None,
            is_current=True,
            change_summary=change_summary,
            file_hash=file_hash,
            filename=file.filename,
            uploaded_at=now,
            deleted=False,
        ))

        for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            db.add(DocumentChunk(
                chunk_id=str(uuid.uuid4()),
                document_id=doc_id,
                version_id=version_id,
                content=chunk,
                embedding=emb,
                chunk_index=idx,
                section=None,
                is_current=True,
                deleted=False,
                created_at=now,
            ))

        document.chunk_count = len(chunks)
        document.status = "chunked"

        _upsert_qdrant_points(
            document_id=doc_id,
            version=version,
            filename=file.filename,
            chunks=chunks,
            embeddings=embeddings,
        )
        qdrant_upserted = True

        document.status = "indexed"
        document.indexed_at = datetime.utcnow()
        _store_audit(db, "CREATE_VERSION", doc_id, version)
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


async def create_document_version(
    document_id: str,
    file: UploadFile,
    db,
    version: str,
    change_summary: str | None = None,
) -> dict:
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Solo se aceptan PDF")

    document = db.query(Document).filter(Document.document_id == document_id).first()
    if not document:
        raise HTTPException(404, "Documento no encontrado")
    if document.status == "archived":
        raise HTTPException(400, "El documento está archivado")

    current_versions = (
        db.query(DocumentVersion)
        .filter(
            DocumentVersion.document_id == document_id,
            DocumentVersion.is_current.is_(True),
            DocumentVersion.deleted.is_(False),
        )
        .all()
    )
    if len(current_versions) > 1:
        raise HTTPException(400, "Existe más de una versión vigente")
    current_version = current_versions[0] if current_versions else None
    if current_version and _compare_versions(version, current_version.version) <= 0:
        raise HTTPException(400, "La versión debe ser mayor a la vigente")

    file_bytes = await file.read()
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    duplicate_hash = (
        db.query(DocumentVersion)
        .filter(
            DocumentVersion.document_id == document_id,
            DocumentVersion.file_hash == file_hash,
        )
        .first()
    )
    if duplicate_hash:
        raise HTTPException(400, "El archivo ya fue cargado previamente")

    version_exists = (
        db.query(DocumentVersion)
        .filter(
            DocumentVersion.document_id == document_id,
            DocumentVersion.version == version,
        )
        .first()
    )
    if version_exists:
        raise HTTPException(400, "La versión ya existe")

    version_id = str(uuid.uuid4())
    qdrant_upserted = False

    try:
        chunks, embeddings = _process_chunks(file_bytes)
        now = datetime.utcnow()

        if current_version:
            current_version.is_current = False
            current_version.effective_to = now
            _update_qdrant_payload(document_id, current_version.version, {
                "is_current": False,
            })
            (
                db.query(DocumentChunk)
                .filter(
                    DocumentChunk.document_id == document_id,
                    DocumentChunk.is_current.is_(True),
                )
                .update({DocumentChunk.is_current: False})
            )

        db.add(DocumentVersion(
            version_id=version_id,
            document_id=document_id,
            version=version,
            effective_from=now,
            effective_to=None,
            is_current=True,
            change_summary=change_summary,
            file_hash=file_hash,
            filename=file.filename,
            uploaded_at=now,
            deleted=False,
        ))

        for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            db.add(DocumentChunk(
                chunk_id=str(uuid.uuid4()),
                document_id=document_id,
                version_id=version_id,
                content=chunk,
                embedding=emb,
                chunk_index=idx,
                section=None,
                is_current=True,
                deleted=False,
                created_at=now,
            ))

        document.chunk_count = len(chunks)
        document.indexed_at = now

        _upsert_qdrant_points(
            document_id=document_id,
            version=version,
            filename=file.filename,
            chunks=chunks,
            embeddings=embeddings,
        )
        qdrant_upserted = True
        _store_audit(db, "CREATE_VERSION", document_id, version)
        db.commit()

        return {
            "document_id": document_id,
            "version": version,
            "chunks": len(chunks),
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
                                match=MatchValue(value=document_id),
                            ),
                            FieldCondition(
                                key="version",
                                match=MatchValue(value=version),
                            ),
                        ]
                    ),
                )
            except Exception as cleanup_exc:
                logger.warning(
                    "No se pudo limpiar Qdrant para %s: %s",
                    document_id,
                    cleanup_exc,
                )
        raise


def list_documents(db) -> List[dict]:
    records = (
        db.query(Document, DocumentVersion)
        .outerjoin(
            DocumentVersion,
            (Document.document_id == DocumentVersion.document_id)
            & (DocumentVersion.is_current.is_(True))
            & (DocumentVersion.deleted.is_(False)),
        )
        .filter(Document.status != "archived")
        .order_by(Document.created_at.desc())
        .all()
    )
    response = []
    for document, version in records:
        response.append({
            "document_id": document.document_id,
            "title": document.title,
            "category": document.category,
            "status": document.status,
            "version": version.version if version else None,
            "effective_from": version.effective_from.isoformat() if version else None,
            "updated_at": (
                version.uploaded_at.isoformat() if version else document.created_at.isoformat()
            ),
        })
    return response


def get_document_detail(document_id: str, db) -> dict:
    document = db.query(Document).filter(Document.document_id == document_id).first()
    if not document:
        raise HTTPException(404, "Documento no encontrado")

    versions = (
        db.query(DocumentVersion)
        .filter(DocumentVersion.document_id == document_id)
        .order_by(DocumentVersion.effective_from.desc())
        .all()
    )
    version_payload = []
    for version in versions:
        item = {
            "version": version.version,
            "is_current": version.is_current,
            "effective_from": version.effective_from.isoformat(),
            "uploaded_at": version.uploaded_at.isoformat(),
        }
        if version.effective_to:
            item["effective_to"] = version.effective_to.isoformat()
        version_payload.append(item)

    return {
        "document_id": document.document_id,
        "title": document.title,
        "category": document.category,
        "status": document.status,
        "versions": version_payload,
    }


def archive_document(document_id: str, db) -> dict:
    document = db.query(Document).filter(Document.document_id == document_id).first()
    if not document:
        raise HTTPException(404, "Documento no encontrado")

    versions = (
        db.query(DocumentVersion)
        .filter(DocumentVersion.document_id == document_id)
        .all()
    )

    now = datetime.utcnow()
    document.status = "archived"

    (
        db.query(DocumentVersion)
        .filter(DocumentVersion.document_id == document_id, DocumentVersion.is_current.is_(True))
        .update({
            DocumentVersion.is_current: False,
            DocumentVersion.effective_to: now,
        })
    )
    (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .update({
            DocumentChunk.deleted: True,
            DocumentChunk.is_current: False,
        })
    )
    _update_qdrant_payload(document_id, None, {
        "deleted": True,
        "is_current": False,
    })
    _store_audit(db, "ARCHIVE_DOCUMENT", document_id, None)
    db.commit()
    _delete_local_files({version.filename for version in versions})
    return {"document_id": document_id, "status": "archived"}


def delete_document_version(document_id: str, version: str, db) -> dict:
    version_record = (
        db.query(DocumentVersion)
        .filter(
            DocumentVersion.document_id == document_id,
            DocumentVersion.version == version,
        )
        .first()
    )
    if not version_record:
        raise HTTPException(404, "Versión no encontrada")
    if version_record.is_current:
        raise HTTPException(400, "No se puede eliminar la versión vigente")

    version_record.deleted = True
    version_record.is_current = False
    version_record.effective_to = version_record.effective_to or datetime.utcnow()

    (
        db.query(DocumentChunk)
        .filter(
            DocumentChunk.document_id == document_id,
            DocumentChunk.version_id == version_record.version_id,
        )
        .update({
            DocumentChunk.deleted: True,
            DocumentChunk.is_current: False,
        })
    )
    _update_qdrant_payload(document_id, version, {
        "deleted": True,
        "is_current": False,
    })
    _store_audit(db, "DELETE_VERSION", document_id, version)
    db.commit()
    return {"document_id": document_id, "version": version, "status": "deleted"}
