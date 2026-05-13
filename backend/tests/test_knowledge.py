"""Tests for Knowledge CRUD and seed data."""
import pytest
from app.db.knowledge_crud import KnowledgeCRUD
from app.db.seed_data.knowledge_seeds import SEED_KNOWLEDGE, seed_knowledge


class TestKnowledgeCRUD:
    @pytest.fixture(autouse=True)
    def setup(self, db_session):
        self.db = db_session
        self.crud = KnowledgeCRUD()

    def test_create_knowledge(self):
        kb = self.crud.create(self.db, name="test-kb", category="name", content="张,李,王")
        assert kb.id is not None
        assert kb.name == "test-kb"
        assert kb.built_in is False

    def test_create_duplicate_name_fails(self):
        self.crud.create(self.db, name="unique", category="name", content="test")
        with pytest.raises(ValueError):
            self.crud.create(self.db, name="unique", category="name", content="test2")

    def test_get_by_name(self):
        self.crud.create(self.db, name="my-kb", category="world", content="content")
        kb = self.crud.get_by_name(self.db, "my-kb")
        assert kb is not None
        assert kb.content == "content"

    def test_get_by_name_not_found(self):
        kb = self.crud.get_by_name(self.db, "nonexistent")
        assert kb is None

    def test_list_by_category(self):
        self.crud.create(self.db, name="kb1", category="name", content="a")
        self.crud.create(self.db, name="kb2", category="name", content="b")
        self.crud.create(self.db, name="kb3", category="world", content="c")
        names = self.crud.list(self.db, category="name")
        assert len(names) == 2

    def test_delete_built_in_fails(self):
        kb = self.crud.create(self.db, name="system-kb", category="name", content="x", built_in=True)
        with pytest.raises(ValueError, match="系统内置知识库不可删除"):
            self.crud.delete(self.db, kb.id)

    def test_update_knowledge(self):
        kb = self.crud.create(self.db, name="updatable", category="name", content="v1")
        updated = self.crud.update(self.db, kb.id, content="v2")
        assert updated.content == "v2"

    def test_seed_knowledge_count(self):
        count = seed_knowledge(self.db)
        assert count == 6

    def test_seed_knowledge_idempotent(self):
        seed_knowledge(self.db)
        count2 = seed_knowledge(self.db)
        assert count2 == 0


class TestKnowledgeSeeds:
    def test_all_seeds_have_required_fields(self):
        for item in SEED_KNOWLEDGE:
            assert item["name"]
            assert item["category"]
            assert item["content"]
