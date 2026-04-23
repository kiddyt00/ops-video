"""
Phase 15 Task 3 tests: Parameter presets

Tests:
- CRUD operations for presets
- User isolation (users only see their own presets)
- Filter by generator type
- Authentication required
"""
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, String, TypeDecorator
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

sys.path.insert(0, str(Path(__file__).parent.parent))


class GUID(TypeDecorator):
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


# Patch models for SQLite compatibility
from app.models.declarative import Base
from app.models import project, task, file as file_model, user as user_model, project_share, parameter_preset
from app.models.guid_type import GUID as ModelGUID

for model in [user_model.User, user_model.RefreshToken, project.Project, task.Task, task.TaskStatusLog, file_model.File, file_model.VariantGroup, project_share.ProjectShare, parameter_preset.ParameterPreset]:
    for col in model.__table__.columns:
        if isinstance(col.type, (PG_UUID, ModelGUID)):
            col.type = GUID()


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


from app.main import app
from app.db.session import get_db


@pytest.fixture(autouse=True)
def setup_db():
    app.dependency_overrides[get_db] = override_get_db
    clear_test_db()
    yield
    if get_db in app.dependency_overrides:
        del app.dependency_overrides[get_db]


client = TestClient(app)


# ─── Helpers ───────────────────────────────────────────────────────────

def register_user(email="test@example.com", username="testuser", password="password123"):
    return client.post("/api/v1/auth/register", json={"email": email, "username": username, "password": password})


def login_user(email="test@example.com", password="password123"):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ─── Tests ───────────────────────────────────────────────────────────

class TestParameterPresets:
    """Test parameter preset CRUD"""

    def _login(self, email="test@example.com", username="testuser", password="password123"):
        register_user(email=email, username=username, password=password)
        resp = login_user(email=email, password=password)
        return resp.json()["access_token"]

    def test_create_preset(self):
        token = self._login()
        resp = client.post(
            "/api/v1/presets",
            json={
                "name": "Fast TTS",
                "generator_type": "tts",
                "description": "Fast TTS with male voice",
                "parameters": {"voice": "male", "rate": "1.5x"},
            },
            headers=auth_header(token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Fast TTS"
        assert data["generator_type"] == "tts"
        assert data["parameters"] == {"voice": "male", "rate": "1.5x"}
        assert data["user_id"] is not None

    def test_create_preset_unauthenticated(self):
        resp = client.post(
            "/api/v1/presets",
            json={"name": "Test", "generator_type": "image"},
        )
        assert resp.status_code in (401, 403)

    def test_list_presets(self):
        token = self._login()
        client.post("/api/v1/presets", json={"name": "Preset 1", "generator_type": "tts"}, headers=auth_header(token))
        client.post("/api/v1/presets", json={"name": "Preset 2", "generator_type": "bgm"}, headers=auth_header(token))

        resp = client.get("/api/v1/presets", headers=auth_header(token))
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_filter_by_generator_type(self):
        token = self._login()
        client.post("/api/v1/presets", json={"name": "TTS 1", "generator_type": "tts"}, headers=auth_header(token))
        client.post("/api/v1/presets", json={"name": "TTS 2", "generator_type": "tts"}, headers=auth_header(token))
        client.post("/api/v1/presets", json={"name": "BGM 1", "generator_type": "bgm"}, headers=auth_header(token))

        resp = client.get("/api/v1/presets?generator_type=tts", headers=auth_header(token))
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_user_isolation(self):
        alice = self._login(email="alice@example.com", username="alice")
        bob = self._login(email="bob@example.com", username="bob")

        client.post("/api/v1/presets", json={"name": "Alice Preset", "generator_type": "image"}, headers=auth_header(alice))
        client.post("/api/v1/presets", json={"name": "Bob Preset", "generator_type": "image"}, headers=auth_header(bob))

        # Alice only sees her presets
        resp = client.get("/api/v1/presets", headers=auth_header(alice))
        assert len(resp.json()) == 1
        assert resp.json()[0]["name"] == "Alice Preset"

    def test_get_preset(self):
        token = self._login()
        create_resp = client.post(
            "/api/v1/presets",
            json={"name": "Get Test", "generator_type": "image", "parameters": {"width": 512}},
            headers=auth_header(token),
        )
        preset_id = create_resp.json()["id"]

        resp = client.get(f"/api/v1/presets/{preset_id}", headers=auth_header(token))
        assert resp.status_code == 200
        assert resp.json()["name"] == "Get Test"

    def test_get_nonexistent_preset(self):
        token = self._login()
        resp = client.get(f"/api/v1/presets/00000000-0000-0000-0000-000000000000", headers=auth_header(token))
        assert resp.status_code == 404

    def test_update_preset(self):
        token = self._login()
        create_resp = client.post(
            "/api/v1/presets",
            json={"name": "Old Name", "generator_type": "tts"},
            headers=auth_header(token),
        )
        preset_id = create_resp.json()["id"]

        resp = client.put(
            f"/api/v1/presets/{preset_id}",
            json={"name": "New Name", "parameters": {"voice": "female"}},
            headers=auth_header(token),
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Name"
        assert resp.json()["parameters"] == {"voice": "female"}

    def test_update_other_user_preset(self):
        alice = self._login(email="alice@example.com", username="alice")
        bob = self._login(email="bob@example.com", username="bob")

        create_resp = client.post(
            "/api/v1/presets",
            json={"name": "Alice Preset", "generator_type": "tts"},
            headers=auth_header(alice),
        )
        preset_id = create_resp.json()["id"]

        resp = client.put(
            f"/api/v1/presets/{preset_id}",
            json={"name": "Hacked"},
            headers=auth_header(bob),
        )
        assert resp.status_code == 403

    def test_delete_preset(self):
        token = self._login()
        create_resp = client.post(
            "/api/v1/presets",
            json={"name": "Delete Me", "generator_type": "image"},
            headers=auth_header(token),
        )
        preset_id = create_resp.json()["id"]

        resp = client.delete(f"/api/v1/presets/{preset_id}", headers=auth_header(token))
        assert resp.status_code == 204

        resp = client.get(f"/api/v1/presets/{preset_id}", headers=auth_header(token))
        assert resp.status_code == 404

    def test_delete_other_user_preset(self):
        alice = self._login(email="alice@example.com", username="alice")
        bob = self._login(email="bob@example.com", username="bob")

        create_resp = client.post(
            "/api/v1/presets",
            json={"name": "Alice Preset", "generator_type": "tts"},
            headers=auth_header(alice),
        )
        preset_id = create_resp.json()["id"]

        resp = client.delete(f"/api/v1/presets/{preset_id}", headers=auth_header(bob))
        assert resp.status_code == 403


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
