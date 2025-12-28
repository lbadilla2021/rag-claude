from fastapi import APIRouter, File, HTTPException, UploadFile

from app.db import SessionLocal
from app.models import Document
from app.services.documents import index_document

router = APIRouter()


@router.get("/documents")
def list_documents():
    db = SessionLocal()
    try:
        docs = db.query(Document).order_by(Document.created_at.desc()).all()
        return [
            {
                "id": d.id,
                "filename": d.filename,
                "status": d.status,
                "chunks": d.chunk_count,
                "createdAt": d.created_at.isoformat(),
                "indexedAt": d.indexed_at.isoformat() if d.indexed_at else None,
                "size": 0,
                "type": "PDF",
                "category": "General",
            }
            for d in docs
        ]
    finally:
        db.close()


@router.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    db = SessionLocal()
    try:
        return await index_document(file, db)
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(500, str(exc))
    finally:
        db.close()
