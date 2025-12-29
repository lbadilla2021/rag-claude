import openai
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.config import OPENAI_API_KEY, logger
from app.db import Base, engine
from app.routes import ask as ask_routes
from app.routes import documents as document_routes
from app.routes import health as health_routes
from app.services.qdrant_service import init_qdrant
from app.state import state

app = FastAPI(title="Apex AI – RAG Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_routes.router, prefix="/api")
app.include_router(document_routes.router, prefix="/api")
app.include_router(ask_routes.router, prefix="/api")


@app.on_event("startup")
def startup():
    logger.info("🚀 Iniciando backend Apex RAG...")

    try:
        Base.metadata.create_all(bind=engine)
        with engine.begin() as connection:
            connection.execute(
                text("CREATE EXTENSION IF NOT EXISTS vector")
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS documents "
                    "ADD COLUMN IF NOT EXISTS filename VARCHAR NOT NULL DEFAULT ''"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS documents "
                    "ADD COLUMN IF NOT EXISTS document_id VARCHAR"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS documents "
                    "ALTER COLUMN filename SET DEFAULT ''"
                )
            )
            connection.execute(
                text(
                    "UPDATE documents "
                    "SET filename = COALESCE(filename, title, '') "
                    "WHERE filename IS NULL"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS documents "
                    "ADD COLUMN IF NOT EXISTS title VARCHAR NOT NULL DEFAULT ''"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS documents "
                    "ADD COLUMN IF NOT EXISTS category VARCHAR"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS documents "
                    "ADD COLUMN IF NOT EXISTS owner_area VARCHAR"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS documents "
                    "ADD COLUMN IF NOT EXISTS owner VARCHAR"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS documents "
                    "ADD COLUMN IF NOT EXISTS department VARCHAR"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS documents "
                    "ADD COLUMN IF NOT EXISTS tags TEXT"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS documents "
                    "ADD COLUMN IF NOT EXISTS description TEXT"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS documents "
                    "ADD COLUMN IF NOT EXISTS is_public BOOLEAN NOT NULL DEFAULT false"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS documents "
                    "ADD COLUMN IF NOT EXISTS is_indexable BOOLEAN NOT NULL DEFAULT true"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS documents "
                    "ADD COLUMN IF NOT EXISTS file_size INTEGER NOT NULL DEFAULT 0"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS documents "
                    "ADD COLUMN IF NOT EXISTS file_type VARCHAR"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS documents "
                    "ADD COLUMN IF NOT EXISTS file_path VARCHAR"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS documents "
                    "ADD COLUMN IF NOT EXISTS status VARCHAR NOT NULL DEFAULT 'active'"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS documents "
                    "ADD COLUMN IF NOT EXISTS created_at TIMESTAMP NOT NULL DEFAULT NOW()"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS documents "
                    "ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS documents "
                    "ADD COLUMN IF NOT EXISTS indexed_at TIMESTAMP"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS documents "
                    "ADD COLUMN IF NOT EXISTS chunk_count INTEGER NOT NULL DEFAULT 0"
                )
            )
            connection.execute(
                text(
                    "DO $$\n"
                    "DECLARE pk_name text;\n"
                    "BEGIN\n"
                    "  IF NOT EXISTS (\n"
                    "    SELECT 1 FROM information_schema.columns\n"
                    "    WHERE table_name = 'documents' AND column_name = 'id'\n"
                    "  ) THEN\n"
                    "    ALTER TABLE documents ADD COLUMN id BIGSERIAL;\n"
                    "  END IF;\n"
                    "  IF EXISTS (\n"
                    "    SELECT 1 FROM information_schema.columns\n"
                    "    WHERE table_name = 'documents' AND column_name = 'id'\n"
                    "  ) THEN\n"
                    "    IF EXISTS (\n"
                    "      SELECT 1 FROM information_schema.columns\n"
                    "      WHERE table_name = 'documents'\n"
                    "        AND column_name = 'id'\n"
                    "        AND data_type IN ('integer', 'bigint', 'smallint')\n"
                    "    ) THEN\n"
                    "      CREATE SEQUENCE IF NOT EXISTS documents_id_seq;\n"
                    "      ALTER SEQUENCE documents_id_seq OWNED BY documents.id;\n"
                    "      ALTER TABLE documents ALTER COLUMN id SET DEFAULT nextval('documents_id_seq');\n"
                    "      PERFORM setval('documents_id_seq', COALESCE((SELECT MAX(id) FROM documents), 0));\n"
                    "      UPDATE documents\n"
                    "      SET id = nextval('documents_id_seq')\n"
                    "      WHERE id IS NULL;\n"
                    "    ELSIF EXISTS (\n"
                    "      SELECT 1 FROM information_schema.columns\n"
                    "      WHERE table_name = 'documents'\n"
                    "        AND column_name = 'id'\n"
                    "        AND data_type = 'uuid'\n"
                    "    ) THEN\n"
                    "      CREATE EXTENSION IF NOT EXISTS pgcrypto;\n"
                    "      ALTER TABLE documents ALTER COLUMN id SET DEFAULT gen_random_uuid();\n"
                    "      UPDATE documents\n"
                    "      SET id = gen_random_uuid()\n"
                    "      WHERE id IS NULL;\n"
                    "    ELSE\n"
                    "      UPDATE documents\n"
                    "      SET document_id = COALESCE(NULLIF(document_id, ''), id::text)\n"
                    "      WHERE (document_id IS NULL OR document_id = '')\n"
                    "        AND id IS NOT NULL;\n"
                    "      SELECT conname INTO pk_name\n"
                    "      FROM pg_constraint\n"
                    "      WHERE conrelid = 'documents'::regclass AND contype = 'p'\n"
                    "      LIMIT 1;\n"
                    "      IF pk_name IS NOT NULL THEN\n"
                    "        EXECUTE format('ALTER TABLE documents DROP CONSTRAINT %I', pk_name);\n"
                    "      END IF;\n"
                    "      ALTER TABLE documents ADD COLUMN id_tmp BIGSERIAL;\n"
                    "      CREATE SEQUENCE IF NOT EXISTS documents_id_seq;\n"
                    "      ALTER SEQUENCE documents_id_seq OWNED BY documents.id_tmp;\n"
                    "      ALTER TABLE documents ALTER COLUMN id_tmp SET DEFAULT nextval('documents_id_seq');\n"
                    "      PERFORM setval('documents_id_seq', COALESCE((SELECT MAX(id_tmp) FROM documents), 0));\n"
                    "      UPDATE documents\n"
                    "      SET id_tmp = nextval('documents_id_seq')\n"
                    "      WHERE id_tmp IS NULL;\n"
                    "      ALTER TABLE documents DROP COLUMN id;\n"
                    "      ALTER TABLE documents RENAME COLUMN id_tmp TO id;\n"
                    "      ALTER SEQUENCE documents_id_seq OWNED BY documents.id;\n"
                    "      ALTER TABLE documents ALTER COLUMN id SET NOT NULL;\n"
                    "    END IF;\n"
                    "  END IF;\n"
                    "  IF NOT EXISTS (\n"
                    "    SELECT 1 FROM pg_constraint\n"
                    "    WHERE conrelid = 'documents'::regclass AND contype = 'p'\n"
                    "  ) THEN\n"
                    "    ALTER TABLE documents ADD PRIMARY KEY (id);\n"
                    "  END IF;\n"
                    "  IF EXISTS (\n"
                    "    SELECT 1 FROM information_schema.columns\n"
                    "    WHERE table_name = 'documents' AND column_name = 'id'\n"
                    "  ) THEN\n"
                    "    UPDATE documents\n"
                    "    SET document_id = COALESCE(document_id, id::text)\n"
                    "    WHERE document_id IS NULL OR document_id = '';\n"
                    "  END IF;\n"
                    "END $$;"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS document_versions "
                    "ADD COLUMN IF NOT EXISTS filename VARCHAR NOT NULL DEFAULT ''"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS document_versions "
                    "ADD COLUMN IF NOT EXISTS file_path VARCHAR"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS document_versions "
                    "ADD COLUMN IF NOT EXISTS file_size INTEGER NOT NULL DEFAULT 0"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS document_versions "
                    "ADD COLUMN IF NOT EXISTS file_type VARCHAR"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS document_versions "
                    "ALTER COLUMN filename SET DEFAULT ''"
                )
            )
            connection.execute(
                text(
                    "UPDATE document_versions "
                    "SET filename = COALESCE(filename, '') "
                    "WHERE filename IS NULL"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS document_versions "
                    "ADD COLUMN IF NOT EXISTS is_current BOOLEAN NOT NULL DEFAULT false"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS document_versions "
                    "ADD COLUMN IF NOT EXISTS deleted BOOLEAN NOT NULL DEFAULT false"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS document_versions "
                    "ADD COLUMN IF NOT EXISTS change_summary TEXT"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS document_versions "
                    "ADD COLUMN IF NOT EXISTS file_hash VARCHAR"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS document_versions "
                    "ADD COLUMN IF NOT EXISTS uploaded_at TIMESTAMP"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS document_versions "
                    "ADD COLUMN IF NOT EXISTS effective_from TIMESTAMP"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS document_versions "
                    "ADD COLUMN IF NOT EXISTS effective_to TIMESTAMP"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS document_chunks "
                    "ADD COLUMN IF NOT EXISTS is_current BOOLEAN NOT NULL DEFAULT false"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS document_chunks "
                    "ADD COLUMN IF NOT EXISTS deleted BOOLEAN NOT NULL DEFAULT false"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS document_chunks "
                    "ADD COLUMN IF NOT EXISTS content TEXT"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS document_chunks "
                    "ADD COLUMN IF NOT EXISTS embedding vector(1536)"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS document_chunks "
                    "ADD COLUMN IF NOT EXISTS chunk_index INTEGER NOT NULL DEFAULT 0"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS document_chunks "
                    "ADD COLUMN IF NOT EXISTS section VARCHAR"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS document_chunks "
                    "ADD COLUMN IF NOT EXISTS created_at TIMESTAMP"
                )
            )
        logger.info("✅ PostgreSQL listo")
    except OperationalError as exc:
        logger.error("❌ PostgreSQL no disponible", exc_info=exc)
        raise

    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY no configurada")

    openai.api_key = OPENAI_API_KEY
    logger.info("✅ OpenAI configurado (API clásica)")

    state.qdrant = init_qdrant()
