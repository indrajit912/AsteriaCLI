"""
Agy conversation repository for AsteriaCLI.

Copyright (c) 2026-Present Indrajit Ghosh. All Rights Reserved.
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from asteria.database.models.agy import AgyConversation
from asteria.exceptions import DuplicateRecordError, RecordNotFoundError

logger = logging.getLogger("asteria.modules.agy.repository")


class AgyRepository:
    """Data-access layer for AgyConversation records.

    All methods operate within the provided SQLAlchemy Session.

    Attributes:
        session: The active database session.
    """

    def __init__(self, session: Session) -> None:
        """Initialize with an active database session.

        Args:
            session: Active SQLAlchemy Session.
        """
        self.session = session

    def create(
        self,
        title: str,
        conversation_id: str,
        category: str = "General",
        description: Optional[str] = None,
        tags: Optional[list[str]] = None,
        notes: Optional[str] = None,
    ) -> AgyConversation:
        """Create a new conversation record.

        Args:
            title: Conversation title.
            conversation_id: Antigravity CLI conversation UUID.
            category: Category label.
            description: Optional description.
            tags: Optional list of tags.
            notes: Optional notes.

        Returns:
            Newly created AgyConversation instance.

        Raises:
            DuplicateRecordError: If conversation_id already exists.
        """
        existing = self.get_by_conversation_id(conversation_id)
        if existing:
            raise DuplicateRecordError("AgyConversation", conversation_id)

        conv = AgyConversation(
            title=title,
            conversation_id=conversation_id,
            category=category,
            description=description,
            notes=notes,
        )
        conv.tags = tags or []
        self.session.add(conv)
        self.session.flush()
        logger.info("Created conversation: %s (%s)", title, conv.id)
        return conv

    def get_by_id(self, record_id: str) -> Optional[AgyConversation]:
        """Fetch a conversation by its UUID primary key.

        Args:
            record_id: UUID string.

        Returns:
            AgyConversation or None.
        """
        return self.session.get(AgyConversation, record_id)

    def get_by_conversation_id(
        self, conversation_id: str
    ) -> Optional[AgyConversation]:
        """Fetch a conversation by its Antigravity conversation ID.

        Args:
            conversation_id: Antigravity CLI conversation identifier.

        Returns:
            AgyConversation or None.
        """
        return (
            self.session.query(AgyConversation)
            .filter(AgyConversation.conversation_id == conversation_id)
            .first()
        )

    def get_or_raise(self, record_id: str) -> AgyConversation:
        """Fetch a conversation by UUID, raising if not found.

        Args:
            record_id: UUID string.

        Returns:
            AgyConversation instance.

        Raises:
            RecordNotFoundError: If no record with the given ID exists.
        """
        conv = self.get_by_id(record_id)
        if conv is None:
            raise RecordNotFoundError("AgyConversation", record_id)
        return conv

    def list_all(
        self,
        category: Optional[str] = None,
        order_by: str = "created_at",
        descending: bool = True,
    ) -> list[AgyConversation]:
        """Return all conversations, optionally filtered by category.

        Args:
            category: Optional category filter.
            order_by: Column to sort by.
            descending: Sort direction.

        Returns:
            List of AgyConversation instances.
        """
        query = self.session.query(AgyConversation)
        if category:
            query = query.filter(
                AgyConversation.category.ilike(f"%{category}%")
            )
        col = getattr(AgyConversation, order_by, AgyConversation.created_at)
        query = query.order_by(col.desc() if descending else col.asc())
        return query.all()

    def search(self, query: str) -> list[AgyConversation]:
        """Search conversations by title, description, or conversation_id.

        Args:
            query: Search string.

        Returns:
            List of matching AgyConversation instances.
        """
        pattern = f"%{query}%"
        return (
            self.session.query(AgyConversation)
            .filter(
                AgyConversation.title.ilike(pattern)
                | AgyConversation.description.ilike(pattern)
                | AgyConversation.conversation_id.ilike(pattern)
                | AgyConversation._tags.ilike(pattern)
            )
            .order_by(AgyConversation.updated_at.desc())
            .all()
        )

    def update(
        self,
        record_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        conversation_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
        notes: Optional[str] = None,
    ) -> AgyConversation:
        """Update an existing conversation record.

        Only non-None arguments are applied.

        Args:
            record_id: UUID of the record to update.
            title: New title.
            description: New description.
            category: New category.
            conversation_id: New conversation ID.
            tags: New tags list.
            notes: New notes.

        Returns:
            Updated AgyConversation instance.

        Raises:
            RecordNotFoundError: If record does not exist.
        """
        conv = self.get_or_raise(record_id)
        if title is not None:
            conv.title = title
        if description is not None:
            conv.description = description
        if category is not None:
            conv.category = category
        if conversation_id is not None:
            conv.conversation_id = conversation_id
        if tags is not None:
            conv.tags = tags
        if notes is not None:
            conv.notes = notes
        self.session.flush()
        logger.info("Updated conversation: %s", record_id)
        return conv

    def delete(self, record_id: str) -> None:
        """Delete a conversation record.

        Args:
            record_id: UUID of the record to delete.

        Raises:
            RecordNotFoundError: If record does not exist.
        """
        conv = self.get_or_raise(record_id)
        self.session.delete(conv)
        self.session.flush()
        logger.info("Deleted conversation: %s", record_id)

    def count(self, category: Optional[str] = None) -> int:
        """Count conversations, optionally filtered by category.

        Args:
            category: Optional category filter.

        Returns:
            Record count.
        """
        query = self.session.query(AgyConversation)
        if category:
            query = query.filter(AgyConversation.category.ilike(f"%{category}%"))
        return query.count()

    def categories(self) -> list[str]:
        """Return a sorted list of all distinct category values.

        Returns:
            List of category strings.
        """
        rows = (
            self.session.query(AgyConversation.category)
            .distinct()
            .order_by(AgyConversation.category)
            .all()
        )
        return [row[0] for row in rows]
