import hashlib
import json
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


def _extract_text(file_bytes: bytes, filename: str) -> str:
    extension = os.path.splitext(filename or "")[1].lower()
    if extension == ".pdf":
        return _extract_pdf_text(file_bytes)
    if extension == ".txt":
        return file_bytes.decode("utf-8", errors="ignore")
    raise HTTPException(400, "Solo se aceptan PDF o TXT")


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
    metadata: dict | None = None,
) -> None:
    # Persistimos embeddings para retrieval sin mezclar versiones.
    points: List[PointStruct] = []
    for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        payload = {
            "document_id": document_id,
            "version": version,
            "chunk_index": idx,
            "filename": filename,
            "content": chunk,
            "is_current": True,
            "deleted": False,
        }
        if metadata:
            payload.update(metadata)
        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=emb,
            payload=payload,
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


def _process_chunks(file_bytes: bytes, filename: str) -> Tuple[List[str], List[List[float]]]:
    # Chunking + embeddings para la nueva versión.
    text = _extract_text(file_bytes, filename)
    if not text.strip():
        raise HTTPException(400, "El documento no contiene texto")
    chunks = splitter.split_text(text)
    embeddings = _build_embeddings(chunks)
    return chunks, embeddings


def _serialize_tags(tags: List[str] | None) -> str | None:
    if tags is None:
        return None
    return json.dumps(tags, ensure_ascii=False)


def _deserialize_tags(raw_tags: str | None) -> List[str]:
    if not raw_tags:
        return []
    try:
        tags = json.loads(raw_tags)
        if isinstance(tags, list):
            return [str(tag) for tag in tags]
    except json.JSONDecodeError:
        pass
    return [tag.strip() for tag in raw_tags.split(",") if tag.strip()]


def _parse_tags(raw_tags: str | None) -> List[str]:
    if not raw_tags:
        return []
    return [tag.strip() for tag in raw_tags.split(",") if tag.strip()]


def _parse_bool(value) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "on"}


def _safe_filename(filename: str | None, fallback: str = "documento.pdf") -> str:
    return os.path.basename(filename or fallback)


def _build_storage_path(document_id: str, version_id: str, filename: str) -> str:
    safe_name = _safe_filename(filename)
    return os.path.join(UPLOAD_DIR, f"{document_id}_{version_id}_{safe_name}")


def _build_metadata_payload(document) -> dict:
    return {
        "title": document.title,
        "category": document.category,
        "owner": document.owner or document.owner_area,
        "department": document.department,
        "tags": _deserialize_tags(document.tags),
        "description": document.description,
        "public": document.is_public,
        "indexable": document.is_indexable,
    }


async def index_document(
    file: UploadFile,
    db,
    title: str | None = None,
    category: str | None = None,
    owner_area: str | None = None,
    owner: str | None = None,
    department: str | None = None,
    tags: str | None = None,
    description: str | None = None,
    public: str | None = None,
    indexable: str | None = None,
    version: str = "1.0",
    change_summary: str | None = None,
) -> dict:
    if not file.filename:
        raise HTTPException(400, "Nombre de archivo inválido")
    if not file.filename.lower().endswith((".pdf", ".txt")):
        raise HTTPException(400, "Solo se aceptan PDF o TXT")

    doc_id = str(uuid.uuid4())
    version_id = str(uuid.uuid4())
    safe_filename = _safe_filename(file.filename)
    filepath = _build_storage_path(doc_id, version_id, safe_filename)
    qdrant_upserted = False

    try:
        file_bytes = await file.read()
        with open(filepath, "wb") as handle:
            handle.write(file_bytes)

        chunks, embeddings = _process_chunks(file_bytes, safe_filename)
        now = datetime.utcnow()
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        file_size = len(file_bytes)
        file_type = os.path.splitext(safe_filename)[1].lstrip(".").lower()
        tag_list = _parse_tags(tags)

        document = Document(
            document_id=doc_id,
            title=title or safe_filename,
            filename=safe_filename,
            category=category,
            owner_area=owner_area,
            owner=owner,
            department=department,
            tags=_serialize_tags(tag_list),
            description=description,
            is_public=_parse_bool(public) or False,
            is_indexable=_parse_bool(indexable) if indexable is not None else True,
            file_size=file_size,
            file_type=file_type,
            file_path=filepath,
            status="active",
            created_at=now,
            updated_at=now,
        )
        db.add(document)

        db.add(DocumentVersion(
            version_id=version_id,
            document_id=doc_id,
            version=version,
            filename=safe_filename,
            file_path=filepath,
            file_size=file_size,
            file_type=file_type,
            effective_from=now,
            effective_to=None,
            is_current=True,
            change_summary=change_summary,
            file_hash=file_hash,
            uploaded_at=now,
            deleted=False,
        ))

        for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            db.add(DocumentChunk(
                chunk_id=str(uuid.uuid4()),
                document_id=doc_id,
                version_id=version_id,
                content=chunk,
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
            filename=safe_filename,
            chunks=chunks,
            embeddings=embeddings,
            metadata=_build_metadata_payload(document),
        )
        qdrant_upserted = True

        document.status = "indexed"
        document.indexed_at = datetime.utcnow()
        _store_audit(db, "CREATE_VERSION", doc_id, version)
        db.commit()

        logger.info("✅ Documento %s indexado", file.filename)

        return {
            "id": doc_id,
            "filename": safe_filename,
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
    if not file.filename:
        raise HTTPException(400, "Nombre de archivo inválido")
    if not file.filename.lower().endswith((".pdf", ".txt")):
        raise HTTPException(400, "Solo se aceptan PDF o TXT")

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
        safe_filename = _safe_filename(file.filename)
        filepath = _build_storage_path(document_id, version_id, safe_filename)
        with open(filepath, "wb") as handle:
            handle.write(file_bytes)

        file_size = len(file_bytes)
        file_type = os.path.splitext(safe_filename)[1].lstrip(".").lower()

        chunks, embeddings = _process_chunks(file_bytes, safe_filename)
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
            filename=safe_filename,
            file_path=filepath,
            file_size=file_size,
            file_type=file_type,
            effective_from=now,
            effective_to=None,
            is_current=True,
            change_summary=change_summary,
            file_hash=file_hash,
            uploaded_at=now,
            deleted=False,
        ))

        for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            db.add(DocumentChunk(
                chunk_id=str(uuid.uuid4()),
                document_id=document_id,
                version_id=version_id,
                content=chunk,
                chunk_index=idx,
                section=None,
                is_current=True,
                deleted=False,
                created_at=now,
            ))

        document.chunk_count = len(chunks)
        document.indexed_at = now
        document.filename = safe_filename
        document.file_path = filepath
        document.file_size = file_size
        document.file_type = file_type
        document.updated_at = now

        _upsert_qdrant_points(
            document_id=document_id,
            version=version,
            filename=safe_filename,
            chunks=chunks,
            embeddings=embeddings,
            metadata=_build_metadata_payload(document),
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
        if "filepath" in locals() and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError as cleanup_exc:
                logger.warning(
                    "No se pudo eliminar el archivo %s: %s",
                    filepath,
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
        .order_by(Document.created_at.desc())
        .all()
    )
    response = []
    for document, version in records:
        tags = _deserialize_tags(document.tags)
        file_type = document.file_type
        if not file_type and document.filename:
            file_type = os.path.splitext(document.filename)[1].lstrip(".").lower()
        updated_at = document.updated_at
        if not updated_at:
            updated_at = version.uploaded_at if version else document.created_at
        response.append({
            "document_id": document.document_id,
            "title": document.title,
            "filename": document.filename,
            "category": document.category,
            "status": document.status,
            "owner": document.owner or document.owner_area,
            "department": document.department,
            "tags": tags,
            "description": document.description,
            "public": document.is_public,
            "indexable": document.is_indexable,
            "size": document.file_size,
            "type": file_type,
            "chunks_count": document.chunk_count,
            "embedding_status": "completed" if document.status == "indexed" else document.status,
            "version": version.version if version else None,
            "effective_from": version.effective_from.isoformat() if version else None,
            "created_at": document.created_at.isoformat(),
            "updated_at": updated_at.isoformat(),
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
        "filename": document.filename,
        "category": document.category,
        "status": document.status,
        "versions": version_payload,
    }


def archive_document(document_id: str, db) -> dict:
    document = db.query(Document).filter(Document.document_id == document_id).first()
    if not document:
        raise HTTPException(404, "Documento no encontrado")

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
    return {"document_id": document_id, "status": "archived"}


def update_document_metadata(document_id: str, payload, db) -> dict:
    document = db.query(Document).filter(Document.document_id == document_id).first()
    if not document:
        raise HTTPException(404, "Documento no encontrado")

    if payload.title is not None:
        document.title = payload.title
    if payload.filename is not None:
        document.filename = payload.filename
    if payload.category is not None:
        document.category = payload.category
    if payload.status is not None:
        document.status = payload.status
    if payload.owner is not None:
        document.owner = payload.owner
    if payload.owner_area is not None:
        document.owner_area = payload.owner_area
    if payload.department is not None:
        document.department = payload.department
    if payload.tags is not None:
        document.tags = _serialize_tags(payload.tags)
    if payload.description is not None:
        document.description = payload.description
    if payload.public is not None:
        document.is_public = payload.public
    if payload.indexable is not None:
        document.is_indexable = payload.indexable

    document.updated_at = datetime.utcnow()

    _update_qdrant_payload(document_id, None, _build_metadata_payload(document))
    _store_audit(db, "UPDATE_METADATA", document_id, None)
    db.commit()

    return {"document_id": document_id, "status": "updated"}


def delete_document(document_id: str, db) -> dict:
    document = db.query(Document).filter(Document.document_id == document_id).first()
    if not document:
        raise HTTPException(404, "Documento no encontrado")

    versions = (
        db.query(DocumentVersion)
        .filter(DocumentVersion.document_id == document_id)
        .all()
    )

    for version in versions:
        if version.file_path and os.path.exists(version.file_path):
            try:
                os.remove(version.file_path)
            except OSError as cleanup_exc:
                logger.warning(
                    "No se pudo eliminar el archivo %s: %s",
                    version.file_path,
                    cleanup_exc,
                )

    try:
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
    except Exception as exc:
        logger.warning("No se pudo eliminar en Qdrant %s: %s", document_id, exc)

    (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .delete(synchronize_session=False)
    )
    (
        db.query(DocumentVersion)
        .filter(DocumentVersion.document_id == document_id)
        .delete(synchronize_session=False)
    )
    (
        db.query(DocumentAudit)
        .filter(DocumentAudit.document_id == document_id)
        .delete(synchronize_session=False)
    )
    (
        db.query(Document)
        .filter(Document.document_id == document_id)
        .delete(synchronize_session=False)
    )
    db.commit()

    return {"document_id": document_id, "status": "deleted"}


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
