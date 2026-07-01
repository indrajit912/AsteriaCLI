# Migration script for AsteriaCLI Gemini schema
# This script backs up the existing SQLite database, creates a new schema where each GeminiPrompt
# has a single associated GeminiOutput (one‑to‑one), and migrates the data, keeping only the most recent
# output for each prompt.

import shutil
import logging
from pathlib import Path

from asteria.database import get_engine, get_session, init_db, drop_all_tables
from asteria.database.models.gemini import (
    GeminiWorkspace,
    GeminiProject,
    GeminiPrompt,
    GeminiOutput,
)

logger = logging.getLogger("asteria.migration")

def migrate_legacy_db():
    """Migrate existing Gemini data to the new one‑to‑one schema.

    Procedure:
    1. Backup the current DB file.
    2. Drop all tables and create the updated schema.
    3. Open a temporary engine to the backup DB and read the old data.
    4. Insert workspaces, projects, and prompts unchanged.
    5. For outputs, keep only the latest per prompt (based on created_at).
    """
    # ---------------------------------------------------------------------
    # 1. Backup current DB
    # ---------------------------------------------------------------------
    from asteria.constants import DB_PATH, APP_DIR
    backup_dir = APP_DIR / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"asteria_backup_{int(DB_PATH.stat().st_mtime)}.db"
    shutil.copy2(DB_PATH, backup_path)
    logger.info("Database backed up to %s", backup_path)

    # ---------------------------------------------------------------------
    # 2. Re‑initialize the new schema (drops old tables)
    # ---------------------------------------------------------------------
    drop_all_tables()
    init_db()
    logger.info("New schema initialized")

    # ---------------------------------------------------------------------
    # 3. Load data from the backup using a separate engine
    # ---------------------------------------------------------------------
    from sqlalchemy import create_engine, desc
    backup_engine = create_engine(f"sqlite:///{backup_path}", connect_args={"check_same_thread": False})
    from sqlalchemy.orm import sessionmaker
    BackupSession = sessionmaker(bind=backup_engine)

    # ---------------------------------------------------------------------
    # 4. Copy data into the new database
    # ---------------------------------------------------------------------
    with BackupSession() as old_sess, get_session() as new_sess:
        # Workspaces
        for ws in old_sess.query(GeminiWorkspace).all():
            new_ws = GeminiWorkspace(
                id=ws.id,
                path=ws.path,
                name=ws.name,
                description=ws.description,
                created_at=ws.created_at,
                updated_at=ws.updated_at,
            )
            new_sess.add(new_ws)
        new_sess.flush()

        # Projects
        for proj in old_sess.query(GeminiProject).all():
            new_proj = GeminiProject(
                id=proj.id,
                name=proj.name,
                description=proj.description,
                workspace_id=proj.workspace_id,
                created_at=proj.created_at,
                updated_at=proj.updated_at,
            )
            new_sess.add(new_proj)
        new_sess.flush()

        # Prompts
        for prm in old_sess.query(GeminiPrompt).all():
            new_prm = GeminiPrompt(
                id=prm.id,
                filename=prm.filename,
                filepath=prm.filepath,
                project_id=prm.project_id,
                _tags=prm._tags,
                notes=prm.notes,
                created_at=prm.created_at,
                updated_at=prm.updated_at,
            )
            new_sess.add(new_prm)
        new_sess.flush()

        # Outputs – keep only the most recent per prompt
        subquery = (
            old_sess.query(
                GeminiOutput.prompt_id,
                GeminiOutput.id,
                GeminiOutput.filename,
                GeminiOutput.filepath,
                GeminiOutput.created_at,
                GeminiOutput.updated_at,
            )
            .order_by(desc(GeminiOutput.created_at))
            .distinct(GeminiOutput.prompt_id)
        )
        for row in subquery:
            new_out = GeminiOutput(
                id=row.id,
                filename=row.filename,
                filepath=row.filepath,
                prompt_id=row.prompt_id,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            new_sess.add(new_out)
        new_sess.commit()
    logger.info("Migration completed successfully")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    migrate_legacy_db()
