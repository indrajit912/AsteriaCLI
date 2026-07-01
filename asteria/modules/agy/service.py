"""
Agy service layer for AsteriaCLI.

Copyright (c) 2026-Present Indrajit Ghosh. All Rights Reserved.
"""

import json
import logging
from pathlib import Path
from typing import Any, Optional

from asteria.database.connection import get_session
from asteria.database.models.agy import AgyConversation
from asteria.exceptions import AgyError, ExportError
from asteria.modules.agy.repository import AgyRepository
from asteria.utils.formatting import (
    parse_tags,
    records_to_csv,
    records_to_json,
    write_export_file,
)
from asteria.utils.fuzzy import exact_or_fuzzy_match

logger = logging.getLogger("asteria.modules.agy.service")


class AgyService:
    """Business logic for the Agy conversation module.

    This service orchestrates repository calls and applies
    cross-cutting concerns (validation, fuzzy search, export).
    """

    # ─── CRUD ────────────────────────────────────────────────────────────────

    @staticmethod
    def add_conversation(
        title: str,
        conversation_id: str,
        category: str = "General",
        description: Optional[str] = None,
        tags: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> AgyConversation:
        """Add a new Agy conversation to the database.

        Args:
            title: Conversation title.
            conversation_id: Antigravity CLI conversation ID.
            category: Category label.
            description: Optional description.
            tags: Comma-separated tag string.
            notes: Optional notes.

        Returns:
            Created AgyConversation instance.
        """
        tag_list = parse_tags(tags or "")
        with get_session() as session:
            repo = AgyRepository(session)
            conv = repo.create(
                title=title,
                conversation_id=conversation_id,
                category=category,
                description=description,
                tags=tag_list,
                notes=notes,
            )
            session.commit()
            session.refresh(conv)
            return conv

    @staticmethod
    def edit_conversation(
        record_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        conversation_id: Optional[str] = None,
        tags: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> AgyConversation:
        """Edit an existing Agy conversation.

        Args:
            record_id: UUID of the record to edit.
            title: New title (or None to keep existing).
            description: New description.
            category: New category.
            conversation_id: New conversation ID.
            tags: New comma-separated tags.
            notes: New notes.

        Returns:
            Updated AgyConversation instance.
        """
        tag_list = parse_tags(tags) if tags is not None else None
        with get_session() as session:
            repo = AgyRepository(session)
            conv = repo.update(
                record_id=record_id,
                title=title,
                description=description,
                category=category,
                conversation_id=conversation_id,
                tags=tag_list,
                notes=notes,
            )
            session.commit()
            session.refresh(conv)
            return conv

    @staticmethod
    def delete_conversation(record_id: str) -> None:
        """Delete an Agy conversation.

        Args:
            record_id: UUID of the record to delete.
        """
        with get_session() as session:
            repo = AgyRepository(session)
            repo.delete(record_id)

    @staticmethod
    def get_conversation(record_id: str) -> AgyConversation:
        """Retrieve a single conversation by ID.

        Args:
            record_id: UUID string.

        Returns:
            AgyConversation instance.
        """
        with get_session() as session:
            repo = AgyRepository(session)
            return repo.get_or_raise(record_id)

    @staticmethod
    def list_conversations(
        category: Optional[str] = None,
        order_by: str = "created_at",
        descending: bool = True,
    ) -> list[AgyConversation]:
        """List all conversations.

        Args:
            category: Optional category filter.
            order_by: Sort column.
            descending: Sort direction.

        Returns:
            List of AgyConversation instances.
        """
        with get_session() as session:
            repo = AgyRepository(session)
            return repo.list_all(
                category=category,
                order_by=order_by,
                descending=descending,
            )

    @staticmethod
    def search_conversations(
        query: str,
        fuzzy: bool = True,
    ) -> list[AgyConversation]:
        """Search conversations by query string.

        Performs a database LIKE search, then optionally applies
        fuzzy ranking for more forgiving matches.

        Args:
            query: Search query.
            fuzzy: Whether to apply fuzzy matching.

        Returns:
            Matching conversations.
        """
        with get_session() as session:
            repo = AgyRepository(session)
            db_results = repo.search(query)

            if fuzzy and not db_results:
                # Fallback to fuzzy search over all records
                all_convs = repo.list_all()
                db_results = exact_or_fuzzy_match(
                    query,
                    all_convs,
                    key=lambda c: f"{c.title} {c.description or ''} {c.tags_display}",
                )
            return db_results

    # ─── Export ───────────────────────────────────────────────────────────────

    @staticmethod
    def export_conversations(
        output_path: Path,
        fmt: str = "json",
        category: Optional[str] = None,
        overwrite: bool = False,
    ) -> Path:
        """Export conversations to JSON or CSV.

        Args:
            output_path: Destination file path.
            fmt: 'json' or 'csv'.
            category: Optional category filter.
            overwrite: Whether to overwrite an existing file.

        Returns:
            Path to the written file.

        Raises:
            ExportError: If export fails.
        """
        conversations = AgyService.list_conversations(category=category)
        records = [c.to_dict() for c in conversations]

        if fmt == "json":
            content = records_to_json(records)
        elif fmt == "csv":
            content = records_to_csv(records)
        else:
            raise ExportError(f"Unsupported format: {fmt}")

        return write_export_file(content, output_path, overwrite=overwrite)

    # ─── Import ───────────────────────────────────────────────────────────────

    @staticmethod
    def import_conversations(source_path: Path) -> tuple[int, int]:
        """Import conversations from a JSON file.

        Args:
            source_path: Path to the JSON import file.

        Returns:
            Tuple of (imported_count, skipped_count).

        Raises:
            AgyError: If the file cannot be parsed.
        """
        try:
            data = json.loads(source_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise AgyError(f"Invalid JSON in import file: {exc}") from exc

        if not isinstance(data, list):
            raise AgyError("Import file must contain a JSON array of conversations.")

        imported = 0
        skipped = 0
        with get_session() as session:
            repo = AgyRepository(session)
            for record in data:
                try:
                    conv_id = record.get("conversation_id", "")
                    if repo.get_by_conversation_id(conv_id):
                        skipped += 1
                        continue
                    conv = repo.create(
                        title=record.get("title", "Untitled"),
                        conversation_id=conv_id,
                        category=record.get("category", "General"),
                        description=record.get("description"),
                        tags=record.get("tags", []),
                        notes=record.get("notes"),
                    )
                    imported += 1
                except Exception as exc:
                    logger.warning("Skipping record due to error: %s", exc)
                    skipped += 1

        return imported, skipped

    # ─── Statistics ───────────────────────────────────────────────────────────

    @staticmethod
    def statistics() -> dict[str, Any]:
        """Return statistics about Agy conversations.

        Returns:
            Dictionary of statistics.
        """
        with get_session() as session:
            repo = AgyRepository(session)
            total = repo.count()
            categories = repo.categories()
            category_counts = {
                cat: repo.count(category=cat) for cat in categories
            }
            return {
                "total": total,
                "categories": len(categories),
                "by_category": category_counts,
            }
