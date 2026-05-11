"""
Integration tests for Storage Providers CRUD API

Tests cover:
- Create, list, get, update, delete storage providers
- Activate storage provider
- Test connection (mocked)
- Duplicate name conflict
- Not found error handling
"""
import sys
from pathlib import Path
from uuid import uuid4
from unittest.mock import AsyncMock, patch

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

def create_storage_provider(
    name="Test Provider",
    provider_type="s3",
    access_key="test-access-key",
    secret_key="test-secret-key",
    bucket="test-bucket",
    endpoint=None,
    region=None,
    **kwargs,
):
    payload = {
        "name": name,
        "provider_type": provider_type,
        "access_key": access_key,
        "secret_key": secret_key,
        "bucket": bucket,
    }
    if endpoint is not None:
        payload["endpoint"] = endpoint
    if region is not None:
        payload["region"] = region
    if "path_prefix" in kwargs:
        payload["path_prefix"] = kwargs["path_prefix"]
    if "extra_config" in kwargs:
        payload["extra_config"] = kwargs["extra_config"]
    return client.post("/api/v1/storage-providers", json=payload)


# ─── Storage Provider CRUD ───────────────────────────────────────────

class TestStorageProviderCRUD:
    """Test storage provider CRUD operations via API"""

    def test_create_storage_provider(self):
        """Test creating a storage provider"""
        resp = create_storage_provider(
            name="My S3 Provider",
            provider_type="s3",
            access_key="AKIAIOSFODNN7EXAMPLE",
            secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            bucket="my-bucket",
            region="us-east-1",
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "My S3 Provider"
        assert data["provider_type"] == "s3"
        assert data["access_key"] == "AKIAIOSFODNN7EXAMPLE"
        assert data["bucket"] == "my-bucket"
        assert data["region"] == "us-east-1"
        assert data["is_active"] is False
        assert data["is_default"] is False
        assert "id" in data
        assert "created_at" in data

    def test_list_storage_providers(self):
        """Test listing all storage providers"""
        create_storage_provider(name="Provider A")
        create_storage_provider(name="Provider B")
        create_storage_provider(name="Provider C")

        resp = client.get("/api/v1/storage-providers")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        names = [p["name"] for p in data]
        assert "Provider A" in names
        assert "Provider B" in names
        assert "Provider C" in names

    def test_get_storage_provider(self):
        """Test getting a single storage provider by ID"""
        resp = create_storage_provider(name="Get Me Provider")
        provider_id = resp.json()["id"]

        resp = client.get(f"/api/v1/storage-providers/{provider_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == provider_id
        assert data["name"] == "Get Me Provider"

    def test_update_storage_provider(self):
        """Test updating a storage provider"""
        resp = create_storage_provider(name="Old Name", region="us-east-1")
        provider_id = resp.json()["id"]

        resp = client.put(
            f"/api/v1/storage-providers/{provider_id}",
            json={
                "name": "New Name",
                "region": "eu-west-1",
                "endpoint": "https://s3.eu-west-1.amazonaws.com",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "New Name"
        assert data["region"] == "eu-west-1"
        assert data["endpoint"] == "https://s3.eu-west-1.amazonaws.com"

        # Verify the update persisted
        resp = client.get(f"/api/v1/storage-providers/{provider_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Name"

    def test_delete_storage_provider(self):
        """Test deleting a storage provider"""
        resp = create_storage_provider(name="Delete Me")
        provider_id = resp.json()["id"]

        resp = client.delete(f"/api/v1/storage-providers/{provider_id}")
        assert resp.status_code == 204

        # Verify deletion
        resp = client.get(f"/api/v1/storage-providers/{provider_id}")
        assert resp.status_code == 404

    def test_activate_storage_provider(self):
        """Test activating a storage provider deactivates all others"""
        # Create three providers
        resp_a = create_storage_provider(name="Provider A")
        resp_b = create_storage_provider(name="Provider B")
        resp_c = create_storage_provider(name="Provider C")

        id_a = resp_a.json()["id"]
        id_b = resp_b.json()["id"]
        id_c = resp_c.json()["id"]

        # Initially none are active
        resp = client.get("/api/v1/storage-providers")
        for p in resp.json():
            assert p["is_active"] is False

        # Activate provider B
        resp = client.post(f"/api/v1/storage-providers/{id_b}/activate")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == id_b
        assert data["is_active"] is True

        # Verify B is active, A and C are not
        resp = client.get("/api/v1/storage-providers")
        providers = {p["id"]: p for p in resp.json()}
        assert providers[id_a]["is_active"] is False
        assert providers[id_b]["is_active"] is True
        assert providers[id_c]["is_active"] is False

        # Now activate C, B should be deactivated
        resp = client.post(f"/api/v1/storage-providers/{id_c}/activate")
        assert resp.status_code == 200
        assert resp.json()["is_active"] is True

        resp = client.get("/api/v1/storage-providers")
        providers = {p["id"]: p for p in resp.json()}
        assert providers[id_b]["is_active"] is False
        assert providers[id_c]["is_active"] is True

    def test_activate_nonexistent_provider(self):
        """Test activating a nonexistent provider returns 404"""
        fake_id = str(uuid4())
        resp = client.post(f"/api/v1/storage-providers/{fake_id}/activate")
        assert resp.status_code == 404

    def test_duplicate_name_conflict(self):
        """Test that creating a provider with duplicate name returns 409"""
        create_storage_provider(name="Unique Provider")
        resp = create_storage_provider(name="Unique Provider")
        assert resp.status_code == 409
        assert "already exists" in resp.json()["detail"]

    def test_get_nonexistent_provider(self):
        """Test getting a nonexistent storage provider returns 404"""
        fake_id = str(uuid4())
        resp = client.get(f"/api/v1/storage-providers/{fake_id}")
        assert resp.status_code == 404

    def test_update_nonexistent_provider(self):
        """Test updating a nonexistent storage provider returns 404"""
        fake_id = str(uuid4())
        resp = client.put(
            f"/api/v1/storage-providers/{fake_id}",
            json={"name": "New Name"},
        )
        assert resp.status_code == 404

    def test_delete_nonexistent_provider(self):
        """Test deleting a nonexistent storage provider returns 404"""
        fake_id = str(uuid4())
        resp = client.delete(f"/api/v1/storage-providers/{fake_id}")
        assert resp.status_code == 404

    def test_test_connection(self):
        """Test connection test endpoint (mocked to avoid real network calls)"""
        resp = create_storage_provider(
            name="Test Conn Provider",
            provider_type="s3",
            access_key="test-key",
            secret_key="test-secret",
            bucket="test-bucket",
            endpoint="https://s3.amazonaws.com",
            region="us-east-1",
        )
        provider_id = resp.json()["id"]

        # Mock the S3 connection test to avoid real network calls
        with patch(
            "app.api.routes.storage_providers._test_s3_connection",
            new_callable=AsyncMock,
            return_value="Connection successful (s3: test-bucket)",
        ):
            resp = client.post(f"/api/v1/storage-providers/{provider_id}/test")
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is True
            assert data["provider_name"] == "Test Conn Provider"
            assert data["bucket"] == "test-bucket"
            assert data["latency_ms"] is not None

    def test_test_connection_nonexistent_provider(self):
        """Test connection test for nonexistent provider returns 404"""
        fake_id = str(uuid4())
        resp = client.post(f"/api/v1/storage-providers/{fake_id}/test")
        assert resp.status_code == 404

    def test_test_connection_failure(self):
        """Test connection test endpoint when connection fails (mocked)"""
        resp = create_storage_provider(
            name="Failing Provider",
            provider_type="s3",
            access_key="bad-key",
            secret_key="bad-secret",
            bucket="bad-bucket",
        )
        provider_id = resp.json()["id"]

        with patch(
            "app.api.routes.storage_providers._test_s3_connection",
            new_callable=AsyncMock,
            side_effect=Exception("Access Denied"),
        ):
            resp = client.post(f"/api/v1/storage-providers/{provider_id}/test")
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is False
            assert "Access Denied" in data["message"]
