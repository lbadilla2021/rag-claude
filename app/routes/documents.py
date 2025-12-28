from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.db import SessionLocal
from app.services.documents import (
    archive_document,
    create_document_version,
    delete_document_version,
    get_document_detail,
    index_document,
    list_documents,
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
        return archive_document(document_id, db)
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
