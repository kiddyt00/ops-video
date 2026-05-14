"""
Tests for CharacterThreeViewService
"""
import sys
from pathlib import Path
from uuid import uuid4
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine, String, TypeDecorator
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

sys.path.insert(0, str(Path(__file__).parent.parent))

# Custom GUID type for SQLite compat
class GUID(TypeDecorator):
    impl = String(36)
    cache_ok = True
    def process_bind_param(self, value, dialect):
        if value is None: return value
        from uuid import UUID
        return str(value) if isinstance(value, UUID) else value
    def process_result_value(self, value, dialect):
        if value is None: return value
        from uuid import UUID
        return UUID(value) if not isinstance(value, UUID) else value

# Patch GUID types across all models
from app.models.declarative import Base
from app.models import project, task, file as file_model, user as user_model, character_card, storage_provider, story, chapter
from app.models.guid_type import GUID as ModelGUID

ALL_MODELS = [
    user_model.User, user_model.RefreshToken,
    project.Project, task.Task, task.TaskStatusLog,
    file_model.File, file_model.VariantGroup,
    character_card.CharacterCard,
    storage_provider.StorageProvider,
    story.Story, chapter.Chapter,
]

for model in ALL_MODELS:
    for col in model.__table__.columns:
        if isinstance(col.type, (PG_UUID, ModelGUID)):
            col.type = GUID()

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

pytestmark = pytest.mark.asyncio


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
    Base.metadata.drop_all(bind=engine)


class TestCharacterThreeViewService:

    async def test_sync_cards_from_story_creates_cards(self, db_session):
        """创建常规角色卡"""
        from app.services.character_three_view_service import CharacterThreeViewService
        from app.models.story import Story, StoryStatus

        pid = uuid4()
        db_session.add(Story(
            id=uuid4(), project_id=pid, status=StoryStatus.completed,
            characters=[
                {"name": "林羽", "role": "主角", "description": "17岁修仙少年"},
                {"name": "冰瑶", "role": "主角", "description": "冰系女修"},
                {"name": "路人甲", "role": "路人", "description": "无关角色"},
            ],
        ))
        db_session.commit()

        svc = CharacterThreeViewService(db_session)
        result = await svc.sync_cards_from_story(pid)

        assert result["created"] == 2
        assert result["skipped"] == 0
        from app.models.character_card import CharacterCard
        cards = db_session.query(CharacterCard).filter(CharacterCard.project_id == pid).all()
        assert len(cards) == 2
        names = {c.name for c in cards}
        assert "林羽" in names
        assert "冰瑶" in names

    async def test_sync_cards_from_story_skips_existing(self, db_session):
        """同名角色卡跳过"""
        from app.services.character_three_view_service import CharacterThreeViewService
        from app.models.character_card import CharacterCard
        from app.models.story import Story, StoryStatus

        pid = uuid4()
        db_session.add(CharacterCard(id=uuid4(), project_id=pid, name="林羽", description="已有卡"))
        db_session.add(Story(
            id=uuid4(), project_id=pid, status=StoryStatus.completed,
            characters=[
                {"name": "林羽", "role": "主角", "description": "已有角色"},
                {"name": "冰瑶", "role": "主角", "description": "新角色"},
            ],
        ))
        db_session.commit()

        svc = CharacterThreeViewService(db_session)
        result = await svc.sync_cards_from_story(pid)

        assert result["created"] == 1  # 冰瑶
        assert result["skipped"] == 1  # 林羽已存在

    async def test_sync_no_story_returns_zero(self, db_session):
        """无故事返回0"""
        from app.services.character_three_view_service import CharacterThreeViewService
        svc = CharacterThreeViewService(db_session)
        result = await svc.sync_cards_from_story(uuid4())
        assert result["created"] == 0
        assert result["skipped"] == 0

    async def test_role_filtering_excludes_extra(self, db_session):
        """路人跳过"""
        from app.services.character_three_view_service import CharacterThreeViewService
        from app.models.story import Story, StoryStatus

        pid = uuid4()
        db_session.add(Story(
            id=uuid4(), project_id=pid, status=StoryStatus.completed,
            characters=[
                {"name": "A", "role": "主角", "description": ""},
                {"name": "B", "role": "路人", "description": ""},
                {"name": "C", "role": "导师", "description": ""},
                {"name": "D", "role": "反派", "description": ""},
            ],
        ))
        db_session.commit()

        svc = CharacterThreeViewService(db_session)
        result = await svc.sync_cards_from_story(pid)
        assert result["created"] == 3  # 主角+导师+反派

    async def test_generate_three_view_calls_llm_and_image(self, db_session):
        """generate_three_view 调用LLM和图片provider"""
        from app.services.character_three_view_service import CharacterThreeViewService
        from app.models.character_card import CharacterCard

        pid = uuid4()
        card_id = uuid4()
        db_session.add(CharacterCard(id=card_id, project_id=pid, name="林羽",
                                     description="17岁修仙少年", traits={"role": "主角"}))
        db_session.commit()

        # Mock via patching imports in the service module
        from unittest.mock import patch, AsyncMock, MagicMock as MM

        mock_file = MM()
        mock_file.read_text.return_value = '{"front":"黑发剑眉","side":"鼻梁挺直","back":"道袍后摆"}'
        mock_result = MM(file_paths=[mock_file])

        mock_img_result = MM(file_paths=["/tmp/test_output.png"])
        mock_provider = MM()
        mock_provider.generate = AsyncMock(return_value=mock_img_result)

        mock_llm = MM()
        mock_llm.generate = AsyncMock(return_value=mock_result)

        with patch("app.providers.llm_provider.llm_provider", mock_llm):
            with patch("app.services.provider_router.ProviderRouter") as mock_router:
                mock_router.return_value.resolve.return_value = mock_provider

                svc = CharacterThreeViewService(db_session)
                result = await svc.generate_three_view(project_id=pid, card_id=card_id)

                assert result["card_id"] == str(card_id)
                assert result["card_name"] == "林羽"
                assert "front_view_url" in result
                assert mock_provider.generate.call_count == 3

    async def test_generate_all_three_views_batch(self, db_session):
        """批量生成处理所有卡"""
        from app.services.character_three_view_service import CharacterThreeViewService
        from app.models.character_card import CharacterCard
        from unittest.mock import patch, AsyncMock, MagicMock as MM

        pid = uuid4()
        db_session.add(CharacterCard(id=uuid4(), project_id=pid, name="A"))
        db_session.add(CharacterCard(id=uuid4(), project_id=pid, name="B"))
        db_session.commit()

        mock_file = MM()
        mock_file.read_text.return_value = '{"front":"f","side":"s","back":"b"}'
        mock_result = MM(file_paths=[mock_file])
        mock_img_result = MM(file_paths=["/tmp/test.png"])

        mock_llm = MM()
        mock_llm.generate = AsyncMock(return_value=mock_result)

        with patch("app.providers.llm_provider.llm_provider", mock_llm):
            with patch("app.services.provider_router.ProviderRouter") as mock_router:
                mock_provider = MM()
                mock_provider.generate = AsyncMock(return_value=mock_img_result)
                mock_router.return_value.resolve.return_value = mock_provider

                svc = CharacterThreeViewService(db_session)
                result = await svc.generate_all_three_views(pid)
                assert result["total"] == 2
                assert result["success"] == 2
