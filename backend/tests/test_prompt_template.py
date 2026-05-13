"""Tests for Prompt CRUD and template rendering."""
import pytest
from app.db.prompt_crud import PromptCRUD
from app.services.prompt_service import render_prompt, seed_default_prompts


class TestPromptCRUD:
    @pytest.fixture(autouse=True)
    def setup(self, db_session):
        self.db = db_session
        self.crud = PromptCRUD()

    def test_create_prompt(self):
        p = self.crud.create(self.db, name="test", template="hello $name")
        assert p.name == "test"
        assert p.version == 1

    def test_create_duplicate_fails(self):
        self.crud.create(self.db, name="unique", template="t")
        with pytest.raises(ValueError):
            self.crud.create(self.db, name="unique", template="t2")

    def test_get_by_name(self):
        self.crud.create(self.db, name="my-prompt", template="content")
        p = self.crud.get_by_name(self.db, "my-prompt")
        assert p is not None
        assert p.template == "content"

    def test_update_increments_version(self):
        p = self.crud.create(self.db, name="ver-test", template="v1")
        updated = self.crud.update(self.db, p.id, template="v2")
        assert updated.version == 2
        assert updated.template == "v2"


class TestPromptRendering:
    @pytest.fixture(autouse=True)
    def setup(self, db_session):
        self.db = db_session
    def test_render_simple_variables(self):
        result = render_prompt("你好 $name，欢迎来到 $place", {"name": "张三", "place": "青云城"})
        assert result == "你好 张三，欢迎来到 青云城"

    def test_render_missing_variable_raises(self):
        with pytest.raises(ValueError, match="缺少变量"):
            render_prompt("$missing_var", {})

    def test_seed_default_prompts(self):
        count = seed_default_prompts(self.db)
        assert count == 2
        story_prompt = PromptCRUD().get_by_name(self.db, "story-generation")
        assert story_prompt is not None
        assert "$inspiration" in story_prompt.template
        assert "@KB{name=story-structures}" in story_prompt.template
        chapter_prompt = PromptCRUD().get_by_name(self.db, "chapter-outline")
        assert chapter_prompt is not None
        assert "$chapter_count" in chapter_prompt.template

    def test_seed_prompts_idempotent(self):
        seed_default_prompts(self.db)
        count2 = seed_default_prompts(self.db)
        assert count2 == 0
