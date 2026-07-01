# populate_agy_from_backup.py
"""Populate AGY conversations from a backup SQLite database into the current
Asteria database.

Only the `agy_conversations` table is copied; Gemini tables remain untouched.
"""

import logging
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from asteria.constants import DB_PATH
from asteria.database import get_session, init_db
from asteria.database.models.agy import AgyConversation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("asteria.populate_agy")


def populate_agy_conversations(backup_path: Path):
    """Copy AgyConversation records from the backup DB to the current DB.

    Args:
        backup_path: Path to the SQLite backup file.
    """
    if not backup_path.is_file():
        logger.error("Backup file %s does not exist", backup_path)
        return

    # Ensure target DB schema exists.
    init_db()

    # Engine for the backup DB.
    backup_engine = create_engine(
        f"sqlite:///{backup_path}", connect_args={"check_same_thread": False}
    )
    BackupSession = sessionmaker(bind=backup_engine)

    with BackupSession() as backup_sess, get_session() as target_sess:
        logger.info("Copying AGY conversations")
        for conv in backup_sess.query(AgyConversation).all():
            target_sess.add(
                AgyConversation(
                    id=conv.id,
                    title=conv.title,
                    description=conv.description,
                    category=conv.category,
                    conversation_id=conv.conversation_id,
                    _tags=conv._tags,
                    notes=conv.notes,
                    created_at=conv.created_at,
                    updated_at=conv.updated_at,
                )
            )
        target_sess.commit()
        logger.info("AGY conversation import complete.")


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python populate_agy_from_backup.py <path-to-backup-db>")
        sys.exit(1)
    backup_file = Path(sys.argv[1]).expanduser().resolve()
    logger.info("Importing AGY conversations from: %s", backup_file)
    populate_agy_conversations(backup_file)
