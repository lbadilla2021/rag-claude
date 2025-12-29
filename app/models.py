from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String, Text

from app.db import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String, nullable=False, unique=True)
    title = Column(String, nullable=False)
    filename = Column(String, nullable=False, default="")
    category = Column(String, nullable=True)
    owner_area = Column(String, nullable=True)
    owner = Column(String, nullable=True)
    department = Column(String, nullable=True)
    tags = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, nullable=False, default=False)
    is_indexable = Column(Boolean, nullable=False, default=True)
    file_size = Column(Integer, nullable=False, default=0)
    file_type = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)
    indexed_at = Column(DateTime)
    chunk_count = Column(Integer, default=0)


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    version_id = Column(String, primary_key=True)
    document_id = Column(String, nullable=False)
    version = Column(String, nullable=False)
    filename = Column(String, nullable=False, default="")
    file_path = Column(String, nullable=True)
    file_size = Column(Integer, nullable=False, default=0)
    file_type = Column(String, nullable=True)
    effective_from = Column(DateTime, nullable=False)
    effective_to = Column(DateTime)
    is_current = Column(Boolean, nullable=False, default=False)
    change_summary = Column(Text)
    file_hash = Column(String, nullable=False)
    uploaded_at = Column(DateTime, nullable=False)
    deleted = Column(Boolean, nullable=False, default=False)


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    chunk_id = Column(String, primary_key=True)
    document_id = Column(String, nullable=False)
    version_id = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(JSON)
    chunk_index = Column(Integer, nullable=False)
    section = Column(String)
    is_current = Column(Boolean, nullable=False, default=False)
    deleted = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False)


class DocumentAudit(Base):
    __tablename__ = "document_audits"

    audit_id = Column(String, primary_key=True)
    action = Column(String, nullable=False)
    document_id = Column(String, nullable=False)
    version = Column(String)
    user = Column(String)
    created_at = Column(DateTime, nullable=False)
