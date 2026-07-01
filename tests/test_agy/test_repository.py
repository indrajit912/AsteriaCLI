"""
Unit tests for the Agy module.

Copyright (c) 2026-Present Indrajit Ghosh. All Rights Reserved.
"""

import pytest

from asteria.database.models.agy import AgyConversation
from asteria.modules.agy.repository import AgyRepository
from asteria.exceptions import DuplicateRecordError, RecordNotFoundError


class TestAgyRepository:
    """Tests for AgyRepository CRUD operations."""

    def test_create_conversation(self, db_session):
        """Should create a conversation and return it."""
        repo = AgyRepository(db_session)
        conv = repo.create(
            title="Test Conv",
            conversation_id="conv-abc-123",
            category="Coding",
            description="A test conversation",
            tags=["python", "testing"],
        )
        db_session.commit()
        assert conv.id is not None
        assert conv.title == "Test Conv"
        assert conv.category == "Coding"
        assert "python" in conv.tags

    def test_create_duplicate_raises(self, db_session):
        """Should raise DuplicateRecordError for same conversation_id."""
        repo = AgyRepository(db_session)
        repo.create(title="First", conversation_id="dup-id")
        db_session.commit()
        with pytest.raises(DuplicateRecordError):
            repo.create(title="Second", conversation_id="dup-id")

    def test_get_by_id(self, db_session):
        """Should retrieve a conversation by its UUID."""
        repo = AgyRepository(db_session)
        conv = repo.create(title="Get Test", conversation_id="get-123")
        db_session.commit()
        fetched = repo.get_by_id(conv.id)
        assert fetched is not None
        assert fetched.title == "Get Test"

    def test_get_by_id_not_found(self, db_session):
        """Should return None for unknown UUID."""
        repo = AgyRepository(db_session)
        result = repo.get_by_id("nonexistent-uuid")
        assert result is None

    def test_get_or_raise_not_found(self, db_session):
        """Should raise RecordNotFoundError for unknown UUID."""
        repo = AgyRepository(db_session)
        with pytest.raises(RecordNotFoundError):
            repo.get_or_raise("bad-id")

    def test_list_all(self, db_session):
        """Should return all conversations."""
        repo = AgyRepository(db_session)
        repo.create(title="Conv A", conversation_id="a-111")
        repo.create(title="Conv B", conversation_id="b-222")
        db_session.commit()
        convs = repo.list_all()
        assert len(convs) == 2

    def test_list_all_with_category_filter(self, db_session):
        """Should filter conversations by category."""
        repo = AgyRepository(db_session)
        repo.create(title="Coding Conv", conversation_id="c-1", category="Coding")
        repo.create(title="Research Conv", conversation_id="r-1", category="Research")
        db_session.commit()
        coding = repo.list_all(category="Coding")
        assert len(coding) == 1
        assert coding[0].category == "Coding"

    def test_update_conversation(self, db_session):
        """Should update conversation fields."""
        repo = AgyRepository(db_session)
        conv = repo.create(title="Old Title", conversation_id="upd-1")
        db_session.commit()
        updated = repo.update(conv.id, title="New Title", category="Research")
        assert updated.title == "New Title"
        assert updated.category == "Research"

    def test_delete_conversation(self, db_session):
        """Should delete a conversation."""
        repo = AgyRepository(db_session)
        conv = repo.create(title="To Delete", conversation_id="del-1")
        db_session.commit()
        repo.delete(conv.id)
        db_session.commit()
        assert repo.get_by_id(conv.id) is None

    def test_delete_not_found(self, db_session):
        """Should raise RecordNotFoundError when deleting unknown ID."""
        repo = AgyRepository(db_session)
        with pytest.raises(RecordNotFoundError):
            repo.delete("no-such-id")

    def test_search(self, db_session):
        """Should find conversations matching the query."""
        repo = AgyRepository(db_session)
        repo.create(title="Python Tutorial", conversation_id="py-1", description="Learn Python")
        repo.create(title="JavaScript Basics", conversation_id="js-1")
        db_session.commit()
        results = repo.search("Python")
        assert len(results) == 1
        assert results[0].title == "Python Tutorial"

    def test_count(self, db_session):
        """Should count conversations correctly."""
        repo = AgyRepository(db_session)
        assert repo.count() == 0
        repo.create(title="C1", conversation_id="c1")
        repo.create(title="C2", conversation_id="c2")
        db_session.commit()
        assert repo.count() == 2

    def test_tags_serialisation(self, db_session):
        """Should round-trip tags through JSON storage."""
        repo = AgyRepository(db_session)
        conv = repo.create(
            title="Tagged", conversation_id="tag-1", tags=["ai", "python", "llm"]
        )
        db_session.commit()
        fetched = repo.get_by_id(conv.id)
        assert fetched.tags == ["ai", "python", "llm"]

    def test_categories(self, db_session):
        """Should return distinct categories."""
        repo = AgyRepository(db_session)
        repo.create(title="A", conversation_id="a1", category="Coding")
        repo.create(title="B", conversation_id="b1", category="Research")
        repo.create(title="C", conversation_id="c1", category="Coding")
        db_session.commit()
        cats = repo.categories()
        assert set(cats) == {"Coding", "Research"}
