"""Tests for Relation and CharacterState models."""
import pytest
from app.db.relation_crud import RelationCRUD
from app.db.character_state_crud import CharacterStateCRUD
from app.services.knowledge_service import inject_knowledge, build_continuity_context
from app.db.knowledge_crud import knowledge_crud


class TestRelationCRUD:
    @pytest.fixture(autouse=True)
    def setup(self, db_session):
        self.db = db_session
        self.crud = RelationCRUD()

    def test_create_relation(self):
        r = self.crud.create(self.db, project_id="p1", source_type="character",
                             source_name="张三", relation_type="mentor_of",
                             target_type="character", target_name="李四")
        assert r.id is not None
        assert r.relation_type == "mentor_of"

    def test_list_by_project(self):
        self.crud.create(self.db, project_id="p1", source_type="character",
                         source_name="A", relation_type="friend_of",
                         target_type="character", target_name="B")
        self.crud.create(self.db, project_id="p1", source_type="character",
                         source_name="A", relation_type="rival_of",
                         target_type="character", target_name="C")
        self.crud.create(self.db, project_id="p2", source_type="character",
                         source_name="D", relation_type="friend_of",
                         target_type="character", target_name="E")
        rels = self.crud.list_by_project(self.db, "p1")
        assert len(rels) == 2

    def test_list_by_character(self):
        self.crud.create(self.db, project_id="p1", source_type="character",
                         source_name="张三", relation_type="friend_of",
                         target_type="character", target_name="李四")
        rels = self.crud.list_by_character(self.db, "p1", "张三")
        assert len(rels) == 1


class TestCharacterStateCRUD:
    @pytest.fixture(autouse=True)
    def setup(self, db_session):
        self.db = db_session
        self.crud = CharacterStateCRUD()

    def test_create_state(self):
        s = self.crud.create(self.db, project_id="p1", character_name="张三",
                             chapter_number=1, status="alive", location="青云城")
        assert s.status == "alive"
        assert s.chapter_number == 1

    def test_get_latest_for_character(self):
        self.crud.create(self.db, project_id="p1", character_name="张三",
                         chapter_number=1, status="alive", location="青云城")
        self.crud.create(self.db, project_id="p1", character_name="张三",
                         chapter_number=2, status="injured", location="黑水渊")
        self.crud.create(self.db, project_id="p1", character_name="李四",
                         chapter_number=1, status="alive", location="紫霞城")
        latest = self.crud.get_latest(self.db, "p1", "张三")
        assert latest.chapter_number == 2
        assert latest.status == "injured"

    def test_get_all_latest_states(self):
        self.crud.create(self.db, project_id="p1", character_name="张三",
                         chapter_number=1, status="alive", location="A城")
        self.crud.create(self.db, project_id="p1", character_name="张三",
                         chapter_number=2, status="dead", location="A城")
        self.crud.create(self.db, project_id="p1", character_name="李四",
                         chapter_number=1, status="alive", location="B城")
        states = self.crud.get_all_latest(self.db, "p1")
        assert len(states) == 2
        dead_char = [s for s in states if s.character_name == "张三"][0]
        assert dead_char.status == "dead"


class TestKnowledgeInjection:
    @pytest.fixture(autouse=True)
    def setup(self, db_session):
        self.db = db_session

    def test_inject_knowledge_by_name(self):
        knowledge_crud.create(self.db, name="test-kb", category="test",
                              content="知识库内容ABC", built_in=True)
        template = "开头@KB{name=test-kb}结尾"
        result = inject_knowledge(self.db, template)
        assert "知识库内容ABC" in result
        assert "@KB{name=test-kb}" not in result

    def test_inject_knowledge_not_found(self):
        result = inject_knowledge(self.db, "hello @KB{name=nonexistent} world")
        assert "知识库未找到" in result

    def test_build_continuity_context(self):
        RelationCRUD().create(self.db, project_id="p1", source_type="character",
                              source_name="张三", relation_type="mentor_of",
                              target_type="character", target_name="李四")
        CharacterStateCRUD().create(self.db, project_id="p1", character_name="张三",
                                    chapter_number=1, status="alive", location="青云城")
        CharacterStateCRUD().create(self.db, project_id="p1", character_name="李四",
                                    chapter_number=1, status="alive", location="青云城",
                                    faction="青云宗")
        context = build_continuity_context(self.db, "p1")
        assert "张三" in context
        assert "alive" in context
        assert "李四" in context
