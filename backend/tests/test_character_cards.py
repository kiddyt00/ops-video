"""
Integration tests for Character Cards CRUD API

Tests cover:
- Create, list, get, update, delete character cards
- Not found error handling
- Project-scoped access control
"""
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, String, TypeDecorator
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# Custom GUID type that works with SQLite
class GUID(TypeDecorator):
    """Platform-independent GUID type for testing."""
    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        from uuid import UUID
        if isinstance(value, UUID):
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        from uuid import UUID
        if not isinstance(value, UUID):
            return UUID(value)
        return value


# Patch all PostgreSQL UUID columns and GUID columns to use test-compatible GUID
from app.models.declarative import Base
from app.models import project, task, file as file_model, user as user_model, character_card, storage_provider
from app.models.guid_type import GUID as ModelGUID

ALL_MODELS = [
    user_model.User, user_model.RefreshToken,
    project.Project,
    task.Task, task.TaskStatusLog,
    file_model.File, file_model.VariantGroup,
    character_card.CharacterCard,
    storage_provider.StorageProvider,
]

for model in ALL_MODELS:
    for col in model.__table__.columns:
        if isinstance(col.type, (PG_UUID, ModelGUID)):
            col.type = GUID()


# Use in-memory SQLite for tests
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def clear_test_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


# Create app with test database
from app.main import app
from app.db.session import get_db


@pytest.fixture(autouse=True)
def setup_db():
    """Clear database before each test"""
    app.dependency_overrides[get_db] = override_get_db
    clear_test_db()
    yield
    if get_db in app.dependency_overrides:
        del app.dependency_overrides[get_db]


client = TestClient(app)


# ─── Helpers ─────────────────────────────────────────────────────────

def create_project(name="Test Project", description="Test description"):
    return client.post(
        "/api/v1/projects",
        json={"name": name, "description": description},
    )


def create_character_card(project_id, name="Test Character", **kwargs):
    payload = {
        "name": name,
        "description": kwargs.get("description", "A test character"),
    }
    if "front_view_url" in kwargs:
        payload["front_view_url"] = kwargs["front_view_url"]
    if "side_view_url" in kwargs:
        payload["side_view_url"] = kwargs["side_view_url"]
    if "back_view_url" in kwargs:
        payload["back_view_url"] = kwargs["back_view_url"]
    if "reference_images" in kwargs:
        payload["reference_images"] = kwargs["reference_images"]
    if "traits" in kwargs:
        payload["traits"] = kwargs["traits"]
    if "is_active" in kwargs:
        payload["is_active"] = kwargs["is_active"]
    return client.post(
        f"/api/v1/projects/{project_id}/character-cards",
        json=payload,
    )


# ─── Character Card CRUD ─────────────────────────────────────────────

class TestCharacterCardCRUD:
    """Test character card CRUD operations via API"""

    def test_create_character_card(self):
        """Test creating a character card for a project"""
        project_resp = create_project("Character Test Project")
        assert project_resp.status_code == 201
        project_id = project_resp.json()["id"]

        resp = create_character_card(
            project_id,
            name="小橘",
            description="一只勇敢的橘猫",
            front_view_url="https://example.com/front.png",
            side_view_url="https://example.com/side.png",
            back_view_url="https://example.com/back.png",
            traits={"color": "orange", "personality": "brave"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "小橘"
        assert data["description"] == "一只勇敢的橘猫"
        assert data["front_view_url"] == "https://example.com/front.png"
        assert data["side_view_url"] == "https://example.com/side.png"
        assert data["back_view_url"] == "https://example.com/back.png"
        assert data["traits"] == {"color": "orange", "personality": "brave"}
        assert data["project_id"] == project_id
        assert data["usage_count"] == 0
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    def test_list_character_cards_by_project(self):
        """Test listing character cards filtered by project"""
        project_resp = create_project("List Test Project")
        project_id = project_resp.json()["id"]

        # Create cards for this project
        create_character_card(project_id, name="小橘")
        create_character_card(project_id, name="小白")

        # Create cards for another project
        other_project_resp = create_project("Other Project")
        other_project_id = other_project_resp.json()["id"]
        create_character_card(other_project_id, name="小黑")

        # List cards for first project
        resp = client.get(
            f"/api/v1/projects/{project_id}/character-cards",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        names = [c["name"] for c in data]
        assert "小橘" in names
        assert "小白" in names
        assert "小黑" not in names

    def test_get_character_card(self):
        """Test getting a single character card by ID"""
        project_resp = create_project("Get Test Project")
        project_id = project_resp.json()["id"]

        card_resp = create_character_card(project_id, name="小橘", description="勇敢的橘猫")
        card_id = card_resp.json()["id"]

        resp = client.get(
            f"/api/v1/projects/{project_id}/character-cards/{card_id}",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == card_id
        assert data["name"] == "小橘"
        assert data["description"] == "勇敢的橘猫"

    def test_update_character_card(self):
        """Test updating a character card"""
        project_resp = create_project("Update Test Project")
        project_id = project_resp.json()["id"]

        card_resp = create_character_card(project_id, name="Old Name")
        card_id = card_resp.json()["id"]

        resp = client.put(
            f"/api/v1/projects/{project_id}/character-cards/{card_id}",
            json={
                "name": "New Name",
                "description": "Updated description",
                "traits": {"color": "blue"},
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "New Name"
        assert data["description"] == "Updated description"
        assert data["traits"] == {"color": "blue"}

        # Verify the update persisted
        resp = client.get(
            f"/api/v1/projects/{project_id}/character-cards/{card_id}",
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Name"

    def test_delete_character_card(self):
        """Test deleting a character card"""
        project_resp = create_project("Delete Test Project")
        project_id = project_resp.json()["id"]

        card_resp = create_character_card(project_id, name="Delete Me")
        card_id = card_resp.json()["id"]

        resp = client.delete(
            f"/api/v1/projects/{project_id}/character-cards/{card_id}",
        )
        assert resp.status_code == 204

        # Verify deletion
        resp = client.get(
            f"/api/v1/projects/{project_id}/character-cards/{card_id}",
        )
        assert resp.status_code == 404

    def test_character_card_not_found(self):
        """Test 404 responses for nonexistent character cards"""
        project_resp = create_project("NotFound Test Project")
        project_id = project_resp.json()["id"]
        fake_id = str(uuid4())

        # Get nonexistent card
        resp = client.get(
            f"/api/v1/projects/{project_id}/character-cards/{fake_id}",
        )
        assert resp.status_code == 404

        # Update nonexistent card
        resp = client.put(
            f"/api/v1/projects/{project_id}/character-cards/{fake_id}",
            json={"name": "Test"},
        )
        assert resp.status_code == 404

        # Delete nonexistent card
        resp = client.delete(
            f"/api/v1/projects/{project_id}/character-cards/{fake_id}",
        )
        assert resp.status_code == 404

    def test_character_card_wrong_project(self):
        """Test that a card from another project returns 404"""
        project_resp_1 = create_project("Project A")
        project_id_1 = project_resp_1.json()["id"]

        project_resp_2 = create_project("Project B")
        project_id_2 = project_resp_2.json()["id"]

        # Create card in project A
        card_resp = create_character_card(project_id_1, name="跨项目测试")
        card_id = card_resp.json()["id"]

        # Try to access via project B
        resp = client.get(
            f"/api/v1/projects/{project_id_2}/character-cards/{card_id}",
        )
        assert resp.status_code == 404
