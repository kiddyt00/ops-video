"""
Phase 15 tests: User project management

Tests:
- Creating a project with authenticated user sets user_id
- GET /api/v1/projects/me returns authenticated user's projects
- GET /api/v1/projects with user_id filter
- Anonymous users still work (backward compatibility)
- Multiple users have isolated project lists
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

# Custom GUID type for SQLite
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
from app.models import project, task, file as file_model, user as user_model, project_share
from app.models.guid_type import GUID as ModelGUID

for model in [user_model.User, user_model.RefreshToken, project.Project, task.Task, task.TaskStatusLog, file_model.File, file_model.VariantGroup, project_share.ProjectShare]:
    for col in model.__table__.columns:
        if isinstance(col.type, (PG_UUID, ModelGUID)):
            col.type = GUID()


# Use in-memory SQLite
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
    app.dependency_overrides[get_db] = override_get_db
    clear_test_db()
    yield
    if get_db in app.dependency_overrides:
        del app.dependency_overrides[get_db]


client = TestClient(app)


# ─── Auth helpers ────────────────────────────────────────────────────

def register_user(email="test@example.com", username="testuser", password="password123"):
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": password},
    )


def login_user(email="test@example.com", password="password123"):
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ─── Tests ───────────────────────────────────────────────────────────

class TestUserProjectManagement:
    """Test user-scoped project management"""

    def test_create_project_with_authenticated_user(self):
        """Creating a project while authenticated sets user_id"""
        register_user()
        login_resp = login_user()
        token = login_resp.json()["access_token"]

        resp = client.post(
            "/api/v1/projects",
            json={"name": "My Project", "description": "Test"},
            headers=auth_header(token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "My Project"
        assert data["user_id"] is not None

    def test_create_project_anonymous_user(self):
        """Anonymous users can still create projects (user_id is None)"""
        resp = client.post(
            "/api/v1/projects",
            json={"name": "Anonymous Project", "description": "Test"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["user_id"] is None

    def test_get_my_projects(self):
        """GET /api/v1/projects/me returns only authenticated user's projects"""
        register_user()
        login_resp = login_user()
        token = login_resp.json()["access_token"]

        # Create 2 projects as this user
        client.post("/api/v1/projects", json={"name": "Project A"}, headers=auth_header(token))
        client.post("/api/v1/projects", json={"name": "Project B"}, headers=auth_header(token))

        # Create another user and a project
        register_user(email="other@example.com", username="otheruser", password="password123")
        other_login = login_user(email="other@example.com", password="password123")
        other_token = other_login.json()["access_token"]
        client.post("/api/v1/projects", json={"name": "Other Project"}, headers=auth_header(other_token))

        # Check my projects
        resp = client.get("/api/v1/projects/me", headers=auth_header(token))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        names = {p["name"] for p in data}
        assert names == {"Project A", "Project B"}

    def test_get_my_projects_unauthenticated(self):
        """GET /api/v1/projects/me requires authentication"""
        resp = client.get("/api/v1/projects/me")
        assert resp.status_code in (401, 403)

    def test_list_projects_filters_by_authenticated_user(self):
        """GET /api/v1/projects without params filters by authenticated user"""
        register_user()
        login_resp = login_user()
        token = login_resp.json()["access_token"]

        client.post("/api/v1/projects", json={"name": "My Project"}, headers=auth_header(token))

        # Create anonymous project
        client.post("/api/v1/projects", json={"name": "Anonymous Project"})

        resp = client.get("/api/v1/projects", headers=auth_header(token))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "My Project"

    def test_list_projects_anonymous_shows_all(self):
        """Anonymous GET /api/v1/projects shows all projects (backward compat)"""
        client.post("/api/v1/projects", json={"name": "Project 1"})
        client.post("/api/v1/projects", json={"name": "Project 2"})

        resp = client.get("/api/v1/projects")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_list_projects_with_user_id_filter(self):
        """GET /api/v1/projects?user_id=X filters by specific user"""
        register_user()
        login_resp = login_user()
        token = login_resp.json()["access_token"]

        # Get user_id from /me
        me_resp = client.get("/api/v1/auth/me", headers=auth_header(token))
        user_id = me_resp.json()["id"]

        client.post("/api/v1/projects", json={"name": "My Project"}, headers=auth_header(token))
        client.post("/api/v1/projects", json={"name": "Anonymous Project"})

        resp = client.get(f"/api/v1/projects?user_id={user_id}", headers=auth_header(token))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "My Project"

    def test_project_response_includes_user_id(self):
        """Project response schema includes user_id field"""
        register_user()
        login_resp = login_user()
        token = login_resp.json()["access_token"]

        resp = client.post(
            "/api/v1/projects",
            json={"name": "Test", "description": "Test"},
            headers=auth_header(token),
        )
        data = resp.json()
        assert "user_id" in data
        assert data["user_id"] is not None

    def test_user_isolation(self):
        """Two users cannot see each other's projects via /me"""
        register_user(email="alice@example.com", username="alice", password="password123")
        register_user(email="bob@example.com", username="bob", password="password123")

        alice_login = login_user(email="alice@example.com", password="password123")
        bob_login = login_user(email="bob@example.com", password="password123")

        alice_token = alice_login.json()["access_token"]
        bob_token = bob_login.json()["access_token"]

        # Alice creates projects
        client.post("/api/v1/projects", json={"name": "Alice Project 1"}, headers=auth_header(alice_token))
        client.post("/api/v1/projects", json={"name": "Alice Project 2"}, headers=auth_header(alice_token))

        # Bob creates projects
        client.post("/api/v1/projects", json={"name": "Bob Project"}, headers=auth_header(bob_token))

        # Alice sees only her projects
        alice_projects = client.get("/api/v1/projects/me", headers=auth_header(alice_token))
        assert len(alice_projects.json()) == 2

        # Bob sees only his projects
        bob_projects = client.get("/api/v1/projects/me", headers=auth_header(bob_token))
        assert len(bob_projects.json()) == 1
        assert bob_projects.json()[0]["name"] == "Bob Project"


class TestProjectResponseSchema:
    """Test that project response correctly includes user_id"""

    def test_get_project_includes_user_id(self):
        """GET single project includes user_id"""
        register_user()
        login_resp = login_user()
        token = login_resp.json()["access_token"]

        create_resp = client.post(
            "/api/v1/projects",
            json={"name": "Get Test"},
            headers=auth_header(token),
        )
        project_id = create_resp.json()["id"]

        resp = client.get(f"/api/v1/projects/{project_id}", headers=auth_header(token))
        assert resp.status_code == 200
        assert "user_id" in resp.json()

    def test_update_project_response_includes_user_id(self):
        """PUT project response includes user_id"""
        register_user()
        login_resp = login_user()
        token = login_resp.json()["access_token"]

        create_resp = client.post(
            "/api/v1/projects",
            json={"name": "Update Test"},
            headers=auth_header(token),
        )
        project_id = create_resp.json()["id"]

        resp = client.put(
            f"/api/v1/projects/{project_id}",
            json={"name": "Updated"},
            headers=auth_header(token),
        )
        assert resp.status_code == 200
        assert "user_id" in resp.json()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


# ─── Project Sharing Tests ───────────────────────────────────────────

class TestProjectSharing:
    """Test project sharing and collaboration"""

    def _setup_users(self):
        """Register and login two users"""
        register_user(email="alice@example.com", username="alice", password="password123")
        register_user(email="bob@example.com", username="bob", password="password123")
        register_user(email="charlie@example.com", username="charlie", password="password123")

        alice = login_user(email="alice@example.com", password="password123")
        bob = login_user(email="bob@example.com", password="password123")
        charlie = login_user(email="charlie@example.com", password="password123")

        alice_token = alice.json()["access_token"]
        bob_token = bob.json()["access_token"]
        charlie_token = charlie.json()["access_token"]

        # Get user IDs from /me
        alice_id = client.get("/api/v1/auth/me", headers=auth_header(alice_token)).json()["id"]
        bob_id = client.get("/api/v1/auth/me", headers=auth_header(bob_token)).json()["id"]
        charlie_id = client.get("/api/v1/auth/me", headers=auth_header(charlie_token)).json()["id"]

        return alice_token, alice_id, bob_token, bob_id, charlie_token, charlie_id

    def test_share_project(self):
        """Owner can share project with another user"""
        alice_token, alice_id, bob_token, bob_id, _, _ = self._setup_users()

        # Alice creates a project
        resp = client.post("/api/v1/projects", json={"name": "Alice Project"}, headers=auth_header(alice_token))
        project_id = resp.json()["id"]

        # Alice shares with Bob
        resp = client.post(
            f"/api/v1/projects/{project_id}/share",
            json={"shared_with_user_id": bob_id, "permission": "view"},
            headers=auth_header(alice_token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["project_id"] == project_id
        assert data["shared_with_user_id"] == bob_id
        assert data["permission"] == "view"

    def test_cannot_share_as_non_owner(self):
        """Non-owner cannot share a project"""
        alice_token, alice_id, bob_token, bob_id, _, _ = self._setup_users()

        # Alice creates a project
        resp = client.post("/api/v1/projects", json={"name": "Alice Project"}, headers=auth_header(alice_token))
        project_id = resp.json()["id"]

        # Bob tries to share Alice's project
        resp = client.post(
            f"/api/v1/projects/{project_id}/share",
            json={"shared_with_user_id": bob_id, "permission": "view"},
            headers=auth_header(bob_token),
        )
        assert resp.status_code == 403

    def test_cannot_share_with_self(self):
        """Cannot share a project with yourself"""
        alice_token, alice_id, _, _, _, _ = self._setup_users()

        resp = client.post("/api/v1/projects", json={"name": "Alice Project"}, headers=auth_header(alice_token))
        project_id = resp.json()["id"]

        resp = client.post(
            f"/api/v1/projects/{project_id}/share",
            json={"shared_with_user_id": alice_id, "permission": "view"},
            headers=auth_header(alice_token),
        )
        assert resp.status_code == 400

    def test_cannot_share_twice(self):
        """Cannot share the same project with the same user twice"""
        alice_token, alice_id, bob_token, bob_id, _, _ = self._setup_users()

        resp = client.post("/api/v1/projects", json={"name": "Alice Project"}, headers=auth_header(alice_token))
        project_id = resp.json()["id"]

        # First share
        resp = client.post(
            f"/api/v1/projects/{project_id}/share",
            json={"shared_with_user_id": bob_id, "permission": "view"},
            headers=auth_header(alice_token),
        )
        assert resp.status_code == 201

        # Second share with same user
        resp = client.post(
            f"/api/v1/projects/{project_id}/share",
            json={"shared_with_user_id": bob_id, "permission": "edit"},
            headers=auth_header(alice_token),
        )
        assert resp.status_code == 409

    def test_list_project_shares(self):
        """Owner can list shares for their project"""
        alice_token, alice_id, bob_token, bob_id, charlie_token, charlie_id = self._setup_users()

        resp = client.post("/api/v1/projects", json={"name": "Alice Project"}, headers=auth_header(alice_token))
        project_id = resp.json()["id"]

        client.post(
            f"/api/v1/projects/{project_id}/share",
            json={"shared_with_user_id": bob_id, "permission": "view"},
            headers=auth_header(alice_token),
        )
        client.post(
            f"/api/v1/projects/{project_id}/share",
            json={"shared_with_user_id": charlie_id, "permission": "edit"},
            headers=auth_header(alice_token),
        )

        resp = client.get(f"/api/v1/projects/{project_id}/shares", headers=auth_header(alice_token))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_unshare_project(self):
        """Owner can remove a share"""
        alice_token, alice_id, bob_token, bob_id, _, _ = self._setup_users()

        resp = client.post("/api/v1/projects", json={"name": "Alice Project"}, headers=auth_header(alice_token))
        project_id = resp.json()["id"]

        client.post(
            f"/api/v1/projects/{project_id}/share",
            json={"shared_with_user_id": bob_id, "permission": "view"},
            headers=auth_header(alice_token),
        )

        resp = client.delete(f"/api/v1/projects/{project_id}/share/{bob_id}", headers=auth_header(alice_token))
        assert resp.status_code == 204

        # Verify share is gone
        resp = client.get(f"/api/v1/projects/{project_id}/shares", headers=auth_header(alice_token))
        assert len(resp.json()) == 0

    def test_update_share_permission(self):
        """Owner can update share permission"""
        alice_token, alice_id, bob_token, bob_id, _, _ = self._setup_users()

        resp = client.post("/api/v1/projects", json={"name": "Alice Project"}, headers=auth_header(alice_token))
        project_id = resp.json()["id"]

        client.post(
            f"/api/v1/projects/{project_id}/share",
            json={"shared_with_user_id": bob_id, "permission": "view"},
            headers=auth_header(alice_token),
        )

        resp = client.put(
            f"/api/v1/projects/{project_id}/share/{bob_id}",
            json={"shared_with_user_id": bob_id, "permission": "edit"},
            headers=auth_header(alice_token),
        )
        assert resp.status_code == 200
        assert resp.json()["permission"] == "edit"

    def test_share_with_nonexistent_user(self):
        """Cannot share with a user that doesn't exist"""
        alice_token, alice_id, _, _, _, _ = self._setup_users()

        resp = client.post("/api/v1/projects", json={"name": "Alice Project"}, headers=auth_header(alice_token))
        project_id = resp.json()["id"]

        resp = client.post(
            f"/api/v1/projects/{project_id}/share",
            json={"shared_with_user_id": str(uuid4()), "permission": "view"},
            headers=auth_header(alice_token),
        )
        assert resp.status_code == 404

    def test_list_shared_with_me(self):
        """User can see projects shared with them"""
        alice_token, alice_id, bob_token, bob_id, _, _ = self._setup_users()

        # Alice creates and shares with Bob
        resp = client.post("/api/v1/projects", json={"name": "Alice Project"}, headers=auth_header(alice_token))
        project_id = resp.json()["id"]
        client.post(
            f"/api/v1/projects/{project_id}/share",
            json={"shared_with_user_id": bob_id, "permission": "view"},
            headers=auth_header(alice_token),
        )

        # Bob checks his shared projects
        resp = client.get("/api/v1/projects/shared-with-me", headers=auth_header(bob_token))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "Alice Project"

    def test_list_shared_with_me_empty(self):
        """User with no shared projects gets empty list"""
        _, _, bob_token, _, _, _ = self._setup_users()

        resp = client.get("/api/v1/projects/shared-with-me", headers=auth_header(bob_token))
        assert resp.status_code == 200
        assert resp.json() == []

    def test_non_owner_cannot_list_shares(self):
        """Non-owner cannot list project shares"""
        alice_token, alice_id, bob_token, bob_id, _, _ = self._setup_users()

        resp = client.post("/api/v1/projects", json={"name": "Alice Project"}, headers=auth_header(alice_token))
        project_id = resp.json()["id"]

        resp = client.get(f"/api/v1/projects/{project_id}/shares", headers=auth_header(bob_token))
        assert resp.status_code == 403

    def test_non_owner_cannot_unshare(self):
        """Non-owner cannot unshare a project"""
        alice_token, alice_id, bob_token, bob_id, _, _ = self._setup_users()

        resp = client.post("/api/v1/projects", json={"name": "Alice Project"}, headers=auth_header(alice_token))
        project_id = resp.json()["id"]

        resp = client.delete(f"/api/v1/projects/{project_id}/share/{bob_id}", headers=auth_header(bob_token))
        assert resp.status_code == 403

    def test_non_owner_cannot_update_permission(self):
        """Non-owner cannot update share permission"""
        alice_token, alice_id, bob_token, bob_id, _, _ = self._setup_users()

        resp = client.post("/api/v1/projects", json={"name": "Alice Project"}, headers=auth_header(alice_token))
        project_id = resp.json()["id"]

        resp = client.put(
            f"/api/v1/projects/{project_id}/share/{bob_id}",
            json={"shared_with_user_id": bob_id, "permission": "edit"},
            headers=auth_header(bob_token),
        )
        assert resp.status_code == 403

    def test_delete_project_cascade_shares(self):
        """Deleting a project removes associated shares"""
        alice_token, alice_id, bob_token, bob_id, _, _ = self._setup_users()

        resp = client.post("/api/v1/projects", json={"name": "Alice Project"}, headers=auth_header(alice_token))
        project_id = resp.json()["id"]

        client.post(
            f"/api/v1/projects/{project_id}/share",
            json={"shared_with_user_id": bob_id, "permission": "view"},
            headers=auth_header(alice_token),
        )

        resp = client.delete(f"/api/v1/projects/{project_id}", headers=auth_header(alice_token))
        assert resp.status_code == 204
