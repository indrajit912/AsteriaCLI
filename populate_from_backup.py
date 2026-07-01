# populate_from_backup.py
"""Populate the current Asteria SQLite database with data from a backup file.

This script copies all Gemini tables *except* GeminiOutput from the supplied
backup database into the active database located at `asteria.constants.DB_PATH`.
It preserves primary keys and relationships, so workspaces, projects, and
prompts are restored in the correct order.
"""

import logging
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import the current project's utilities and models
from asteria.constants import DB_PATH, APP_DIR
from asteria.database import get_session, init_db, drop_all_tables
from asteria.database.models.gemini import GeminiWorkspace, GeminiProject, GeminiPrompt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("asteria.populate_backup")


def populate_from_backup(backup_path: Path):
    """Copy GeminiWorkspace, GeminiProject, and GeminiPrompt records.

    Args:
        backup_path: Path to the SQLite backup file.
    """
    if not backup_path.is_file():
        logger.error("Backup file %s does not exist", backup_path)
        return

    # Ensure target DB exists with correct schema.
    init_db()

    # Temporary engine for backup DB.
    backup_engine = create_engine(
        f"sqlite:///{backup_path}", connect_args={"check_same_thread": False}
    )
    BackupSession = sessionmaker(bind=backup_engine)

    with BackupSession() as backup_sess, get_session() as target_sess:
        # Workspaces
        logger.info("Copying workspaces")
        for ws in backup_sess.query(GeminiWorkspace).all():
            target_sess.add(
                GeminiWorkspace(
                    id=ws.id,
                    path=ws.path,
                    name=ws.name,
                    description=ws.description,
                    created_at=ws.created_at,
                    updated_at=ws.updated_at,
                )
            )
        target_sess.flush()

        # Projects
        logger.info("Copying projects")
        for proj in backup_sess.query(GeminiProject).all():
            target_sess.add(
                GeminiProject(
                    id=proj.id,
                    name=proj.name,
                    description=proj.description,
                    workspace_id=proj.workspace_id,
                    created_at=proj.created_at,
                    updated_at=proj.updated_at,
                )
            )
        target_sess.flush()

        # Prompts
        logger.info("Copying prompts")
        for prm in backup_sess.query(GeminiPrompt).all():
            target_sess.add(
                GeminiPrompt(
                    id=prm.id,
                    filename=prm.filename,
                    filepath=prm.filepath,
                    project_id=prm.project_id,
                    _tags=prm._tags,
                    notes=prm.notes,
                    created_at=prm.created_at,
                    updated_at=prm.updated_at,
                )
            )
        target_sess.commit()
        logger.info("Backup data populated successfully.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python populate_from_backup.py <path-to-backup-db>")
        sys.exit(1)
    backup_file = Path(sys.argv[1]).expanduser().resolve()
    logger.info("Populating database from backup: %s", backup_file)
    populate_from_backup(backup_file)
