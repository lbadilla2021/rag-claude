import os

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.db import SessionLocal
from app.models import DocumentVersion
from app.schemas import DocumentUpdate
from app.services.documents import (
    create_document_version,
    delete_document as remove_document,
    delete_document_version,
    get_document_detail,
    index_document,
    list_documents,
    update_document_metadata,
)

router = APIRouter()


@router.get("/documents")
def list_documents():
    db = SessionLocal()
    try:
        return list_documents(db)
    finally:
        db.close()


@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: str | None = Form(None),
    category: str | None = Form(None),
    owner_area: str | None = Form(None),
    owner: str | None = Form(None),
    department: str | None = Form(None),
    tags: str | None = Form(None),
    description: str | None = Form(None),
    public: str | None = Form(None),
    indexable: str | None = Form(None),
    version: str = Form("1.0"),
    change_summary: str | None = Form(None),
):
    db = SessionLocal()
    try:
        return await index_document(
            file=file,
            db=db,
            title=title,
            category=category,
            owner_area=owner_area,
            owner=owner,
            department=department,
            tags=tags,
            description=description,
            public=public,
            indexable=indexable,
            version=version,
            change_summary=change_summary,
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(500, str(exc))
    finally:
        db.close()


@router.get("/documents/{document_id}")
def document_detail(document_id: str):
    db = SessionLocal()
    try:
        return get_document_detail(document_id, db)
    finally:
        db.close()


@router.get("/documents/{document_id}/download")
def download_document(document_id: str):
    db = SessionLocal()
    try:
        document = get_document_detail(document_id, db)
        version = (
            db.query(DocumentVersion)
            .filter(
                DocumentVersion.document_id == document_id,
                DocumentVersion.is_current.is_(True),
                DocumentVersion.deleted.is_(False),
            )
            .first()
        )
        if not version or not version.file_path:
            raise HTTPException(404, "Archivo no encontrado")
        if not os.path.exists(version.file_path):
            raise HTTPException(404, "Archivo no encontrado")
        return FileResponse(
            version.file_path,
            filename=version.filename or document.get("filename") or "documento.pdf",
        )
    finally:
        db.close()


@router.put("/documents/{document_id}")
def update_document(document_id: str, payload: DocumentUpdate):
    db = SessionLocal()
    try:
        return update_document_metadata(document_id, payload, db)
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(500, str(exc))
    finally:
        db.close()


@router.post("/documents/{document_id}/versions")
async def add_document_version(
    document_id: str,
    file: UploadFile = File(...),
    version: str = Form(...),
    change_summary: str | None = Form(None),
):
    db = SessionLocal()
    try:
        return await create_document_version(
            document_id=document_id,
            file=file,
            db=db,
            version=version,
            change_summary=change_summary,
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(500, str(exc))
    finally:
        db.close()


@router.delete("/documents/{document_id}")
def delete_document(document_id: str):
    db = SessionLocal()
    try:
        return remove_document(document_id, db)
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(500, str(exc))
    finally:
        db.close()


@router.delete("/documents/{document_id}/versions/{version}")
def delete_version(document_id: str, version: str):
    db = SessionLocal()
    try:
        return delete_document_version(document_id, version, db)
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(500, str(exc))
    finally:
        db.close()
