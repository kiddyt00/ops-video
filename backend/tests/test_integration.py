"""
Integration tests for full API workflows

Tests cover:
- End-to-end workflow (create project -> advance stages -> variant selection)
- CRUD operations for all resources
- Error handling and edge cases
"""
import sys
from pathlib import Path
from uuid import uuid4, UUID
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, String, TypeDecorator, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.compiler import compiles

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# Custom GUID type that works with both PostgreSQL and SQLite
class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type, otherwise uses
    CHAR(32), storing as stringified hex values.
    """
    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, UUID):
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, UUID):
            return UUID(value)
        return value


# Patch all PostgreSQL UUID columns and GUID columns to use test-compatible GUID
from app.models.declarative import Base
from app.models import project, task, file as file_model, user as user_model
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.models.guid_type import GUID as ModelGUID

for model in [user_model.User, user_model.RefreshToken, project.Project, task.Task, task.TaskStatusLog, file_model.File, file_model.VariantGroup]:
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
    # Set dependency override in fixture to avoid cross-module pollution
    app.dependency_overrides[get_db] = override_get_db
    """Clear database before each test"""
    clear_test_db()
    yield
    # Clean up override after test
    if get_db in app.dependency_overrides:
        del app.dependency_overrides[get_db]


client = TestClient(app)


# ─── Helper factories ────────────────────────────────────────────────

def create_project(name="Test Project", description="Test description"):
    return client.post(
        "/api/v1/projects",
        json={"name": name, "description": description},
    )


def create_task(project_id, stage="script", generator_type="script", parameters=None, parent_task_ids=None):
    return client.post(
        "/api/v1/tasks",
        json={
            "project_id": project_id,
            "stage": stage,
            "generator_type": generator_type,
            "parameters": parameters or {},
            "parent_task_ids": parent_task_ids or [],
        },
    )


def create_file(project_id, task_id, variant_group_id=None, file_type="script", file_path="test.txt"):
    return client.post(
        "/api/v1/files",
        json={
            "project_id": project_id,
            "task_id": task_id,
            "variant_group_id": variant_group_id,
            "file_type": file_type,
            "file_path": file_path,
        },
    )


def create_variant_group(project_id, task_id, stage="script", parameters=None):
    return client.post(
        "/api/v1/variants",
        json={
            "project_id": project_id,
            "task_id": task_id,
            "stage": stage,
            "parameters": parameters or {},
        },
    )


# ─── Project CRUD ────────────────────────────────────────────────────

class TestProjectCRUD:
    """Test project CRUD operations via API"""

    def test_create_project(self):
        resp = create_project("My Project", "A test project")
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "My Project"
        assert data["description"] == "A test project"
        assert "id" in data
        assert "created_at" in data

    def test_list_projects(self):
        create_project("Project 1")
        create_project("Project 2")
        resp = client.get("/api/v1/projects")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_get_project(self):
        resp = create_project("Get Me")
        project_id = resp.json()["id"]
        resp = client.get(f"/api/v1/projects/{project_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Get Me"

    def test_update_project(self):
        resp = create_project("Old Name")
        project_id = resp.json()["id"]
        resp = client.put(f"/api/v1/projects/{project_id}", json={"name": "New Name"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Name"

    def test_delete_project(self):
        resp = create_project("Delete Me")
        project_id = resp.json()["id"]
        resp = client.delete(f"/api/v1/projects/{project_id}")
        assert resp.status_code == 204
        resp = client.get(f"/api/v1/projects/{project_id}")
        assert resp.status_code == 404

    def test_get_nonexistent_project(self):
        resp = client.get(f"/api/v1/projects/{uuid4()}")
        assert resp.status_code == 404


# ─── Task CRUD ───────────────────────────────────────────────────────

class TestTaskCRUD:
    """Test task CRUD operations via API"""

    def test_create_task(self):
        project_resp = create_project()
        project_id = project_resp.json()["id"]
        resp = create_task(project_id)
        assert resp.status_code == 201
        data = resp.json()
        assert data["stage"] == "script"
        assert data["status"] == "pending"
        assert data["generator_type"] == "script"

    def test_list_tasks(self):
        project_resp = create_project()
        project_id = project_resp.json()["id"]
        create_task(project_id, "script")
        create_task(project_id, "storyboard")
        resp = client.get(f"/api/v1/tasks?project_id={project_id}")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_get_task(self):
        project_resp = create_project()
        task_resp = create_task(project_resp.json()["id"])
        task_id = task_resp.json()["id"]
        resp = client.get(f"/api/v1/tasks/{task_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == task_id

    def test_delete_task(self):
        project_resp = create_project()
        task_resp = create_task(project_resp.json()["id"])
        task_id = task_resp.json()["id"]
        resp = client.delete(f"/api/v1/tasks/{task_id}")
        assert resp.status_code == 204

    def test_create_task_for_nonexistent_project(self):
        resp = create_task(str(uuid4()))
        assert resp.status_code == 404

    def test_run_task(self):
        project_resp = create_project()
        task_resp = create_task(project_resp.json()["id"])
        task_id = task_resp.json()["id"]
        resp = client.post(f"/api/v1/tasks/{task_id}/run")
        assert resp.status_code == 200
        assert resp.json()["status"] == "running"

    def test_update_task_status(self):
        project_resp = create_project()
        task_resp = create_task(project_resp.json()["id"])
        task_id = task_resp.json()["id"]
        resp = client.put(
            f"/api/v1/tasks/{task_id}/status",
            json={"status": "completed", "reason": "Test complete"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"

    def test_get_task_logs(self):
        project_resp = create_project()
        task_resp = create_task(project_resp.json()["id"])
        task_id = task_resp.json()["id"]
        resp = client.get(f"/api/v1/tasks/{task_id}/logs")
        assert resp.status_code == 200
        logs = resp.json()
        assert len(logs) >= 1  # At least initial status log
        assert logs[0]["to_status"] == "pending"


# ─── Variant Group & File CRUD ───────────────────────────────────────

class TestVariantAndFileCRUD:
    """Test variant group and file operations"""

    def test_create_variant_group(self):
        project_resp = create_project()
        project_id = project_resp.json()["id"]
        task_resp = create_task(project_id)
        task_id = task_resp.json()["id"]
        resp = create_variant_group(project_id, task_id)
        assert resp.status_code == 201
        data = resp.json()
        assert data["stage"] == "script"
        assert data["project_id"] == project_id
        assert data["task_id"] == task_id

    def test_list_variant_groups(self):
        project_resp = create_project()
        project_id = project_resp.json()["id"]
        task_resp = create_task(project_id)
        task_id = task_resp.json()["id"]
        create_variant_group(project_id, task_id, "script")
        create_variant_group(project_id, task_id, "storyboard")
        resp = client.get(f"/api/v1/variants?project_id={project_id}")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_create_file(self):
        project_resp = create_project()
        project_id = project_resp.json()["id"]
        task_resp = create_task(project_id)
        task_id = task_resp.json()["id"]
        vg_resp = create_variant_group(project_id, task_id)
        vg_id = vg_resp.json()["id"]
        resp = create_file(project_id, task_id, vg_id, "script", "scripts/test.txt")
        assert resp.status_code == 201
        data = resp.json()
        assert data["file_path"] == "scripts/test.txt"
        assert data["file_type"] == "script"

    def test_select_variant(self):
        project_resp = create_project()
        project_id = project_resp.json()["id"]
        task_resp = create_task(project_id)
        task_id = task_resp.json()["id"]
        vg_resp = create_variant_group(project_id, task_id)
        vg_id = vg_resp.json()["id"]
        file_resp = create_file(project_id, task_id, vg_id, "script", "scripts/v1.txt")
        file_id = file_resp.json()["id"]
        resp = client.post(f"/api/v1/variants/{vg_id}/select", json={"file_id": file_id})
        assert resp.status_code == 200
        assert resp.json()["selected_file_id"] == file_id

    def test_get_file(self):
        project_resp = create_project()
        project_id = project_resp.json()["id"]
        task_resp = create_task(project_id)
        task_id = task_resp.json()["id"]
        file_resp = create_file(project_id, task_id, file_path="test.txt")
        file_id = file_resp.json()["id"]
        resp = client.get(f"/api/v1/files/{file_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == file_id

    def test_delete_file(self):
        project_resp = create_project()
        project_id = project_resp.json()["id"]
        task_resp = create_task(project_id)
        task_id = task_resp.json()["id"]
        file_resp = create_file(project_id, task_id, file_path="test.txt")
        file_id = file_resp.json()["id"]
        resp = client.delete(f"/api/v1/files/{file_id}")
        assert resp.status_code == 204


# ─── End-to-End Workflow ─────────────────────────────────────────────

class TestEndToEndWorkflow:
    """Test complete workflow from project creation to final stage"""

    def _complete_stage(self, project_id, stage, generator_type, parameters=None):
        """Helper: create task, mark as completed, create variant group and file"""
        body = {"parameters": parameters or {}, "execute": False}
        task_resp = client.post(
            f"/api/v1/workflow/{project_id}/advance/{stage}",
            json=body,
        )
        assert task_resp.status_code == 200, f"Failed to advance to {stage}: {task_resp.text}"
        task_id = task_resp.json()["id"]

        # Mark task as completed
        resp = client.put(
            f"/api/v1/tasks/{task_id}/status",
            json={"status": "completed", "reason": "Generated"},
        )
        assert resp.status_code == 200

        # Create variant group
        vg_resp = create_variant_group(project_id, task_id, stage, parameters)
        vg_id = vg_resp.json()["id"]

        # Create file
        file_resp = create_file(project_id, task_id, vg_id, stage, f"{stage}/output.txt")
        file_id = file_resp.json()["id"]

        # Select variant
        resp = client.post(f"/api/v1/variants/{vg_id}/select", json={"file_id": file_id})
        assert resp.status_code == 200

        return task_id, vg_id, file_id

    def test_full_workflow(self):
        """Test complete 8-stage workflow: inspiration -> story -> ... -> video"""
        # 1. Create project
        project_resp = create_project("Full Workflow Test")
        project_id = project_resp.json()["id"]

        # 2. Advance through all 8 stages
        stages = ["inspiration", "story", "chapter_outline", "script", "storyboard", "image", "audio", "video"]
        created_tasks = []

        for stage in stages:
            task_id, vg_id, file_id = self._complete_stage(project_id, stage, stage)
            created_tasks.append((task_id, vg_id, file_id))

        # 3. Verify workflow status
        resp = client.get(f"/api/v1/workflow/{project_id}/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["project_id"] == project_id
        assert len(data["stages"]) == 8

        # 4. Verify workflow history
        resp = client.get(f"/api/v1/workflow/{project_id}/history")
        assert resp.status_code == 200
        history = resp.json()["history"]
        assert len(history) == 8

    def test_workflow_advancement_without_prerequisites(self):
        """Test that advancing without completing prerequisites fails"""
        project_resp = create_project()
        project_id = project_resp.json()["id"]

        # Try to advance to storyboard without completing any prerequisites
        resp = client.post(f"/api/v1/workflow/{project_id}/advance/storyboard")
        assert resp.status_code == 400

        # Try to advance directly to script without inspiration/story/chapter_outline
        resp = client.post(f"/api/v1/workflow/{project_id}/advance/script")
        assert resp.status_code == 400

    def test_workflow_first_stage(self):
        """Test advancing to first stage (inspiration)"""
        project_resp = create_project()
        project_id = project_resp.json()["id"]
        resp = client.post(
            f"/api/v1/workflow/{project_id}/advance/inspiration",
            json={"execute": False},
        )
        assert resp.status_code == 200
        assert resp.json()["stage"] == "inspiration"
        assert resp.json()["status"] in ("pending", "failed")

    def test_workflow_history_empty_project(self):
        """Test workflow history for project with no tasks"""
        project_resp = create_project()
        project_id = project_resp.json()["id"]
        resp = client.get(f"/api/v1/workflow/{project_id}/history")
        assert resp.status_code == 200
        assert resp.json()["history"] == []

    def test_rollback_to_stage(self):
        """Test rolling back to a previous stage"""
        project_resp = create_project()
        project_id = project_resp.json()["id"]

        # Complete all prerequisite stages (inspiration → story → chapter_outline → script)
        for pre in ["inspiration", "story", "chapter_outline", "script"]:
            self._complete_stage(project_id, pre, pre)

        # Complete storyboard stage
        self._complete_stage(project_id, "storyboard", "storyboard")

        # Rollback to script
        resp = client.post(f"/api/v1/workflow/{project_id}/rollback/script")
        assert resp.status_code == 200
        assert resp.json()["stage"] == "script"

    def test_nonexistent_project_workflow(self):
        """Test workflow operations on nonexistent project"""
        fake_id = str(uuid4())
        resp = client.get(f"/api/v1/workflow/{fake_id}/status")
        assert resp.status_code == 200  # Returns empty stages
        resp = client.post(f"/api/v1/workflow/{fake_id}/advance/script")
        assert resp.status_code == 400


# ─── Traceability ────────────────────────────────────────────────────

class TestTraceability:
    """Test file lineage, version comparison, and file versions"""

    def test_file_lineage(self):
        """Test getting generation lineage for a file"""
        project_resp = create_project()
        project_id = project_resp.json()["id"]
        task_resp = create_task(project_id)
        task_id = task_resp.json()["id"]
        file_resp = create_file(project_id, task_id, file_path="scripts/v1.txt")
        file_id = file_resp.json()["id"]

        resp = client.get(f"/api/v1/workflow/files/{file_id}/lineage")
        assert resp.status_code == 200
        data = resp.json()
        assert data["file_id"] == file_id
        assert len(data["lineage"]) >= 1

    def test_file_versions(self):
        """Test getting file versions"""
        project_resp = create_project()
        project_id = project_resp.json()["id"]
        task_resp = create_task(project_id)
        task_id = task_resp.json()["id"]
        file_resp = create_file(project_id, task_id, file_path="scripts/v1.txt")
        file_id = file_resp.json()["id"]

        resp = client.get(f"/api/v1/workflow/files/{file_id}/versions")
        assert resp.status_code == 200
        data = resp.json()
        assert data["file_id"] == file_id

    def test_compare_files(self):
        """Test comparing two files in the same variant group"""
        project_resp = create_project()
        project_id = project_resp.json()["id"]
        task_resp = create_task(project_id)
        task_id = task_resp.json()["id"]
        vg_resp = create_variant_group(project_id, task_id, "script")
        vg_id = vg_resp.json()["id"]

        file1_resp = create_file(project_id, task_id, vg_id, "script", "scripts/v1.txt")
        file1_id = file1_resp.json()["id"]

        file2_resp = create_file(project_id, task_id, vg_id, "script", "scripts/v2.txt")
        file2_id = file2_resp.json()["id"]

        resp = client.post(f"/api/v1/workflow/variants/{vg_id}/files/{file1_id}/compare")
        assert resp.status_code == 200
        data = resp.json()
        assert "file_1" in data
        assert "file_2" in data

    def test_variant_comparison(self):
        """Test variant group comparison endpoint"""
        project_resp = create_project()
        project_id = project_resp.json()["id"]
        task_resp = create_task(project_id)
        task_id = task_resp.json()["id"]
        vg_resp = create_variant_group(project_id, task_id, "script")
        vg_id = vg_resp.json()["id"]

        create_file(project_id, task_id, vg_id, "script", "scripts/v1.txt")
        create_file(project_id, task_id, vg_id, "script", "scripts/v2.txt")

        resp = client.get(f"/api/v1/workflow/variants/{vg_id}/compare")
        assert resp.status_code == 200
        data = resp.json()
        assert data["variant_group_id"] == vg_id
        assert len(data["variants"]) == 2

    def test_nonexistent_file_lineage(self):
        """Test lineage for nonexistent file"""
        resp = client.get(f"/api/v1/workflow/files/{uuid4()}/lineage")
        assert resp.status_code == 200
        data = resp.json()
        assert data["lineage"] == []


# ─── Generator API ───────────────────────────────────────────────────

class TestGeneratorAPI:
    """Test generator listing and info endpoints"""

    def test_list_generators(self):
        resp = client.get("/api/v1/generators")
        assert resp.status_code == 200
        assert len(resp.json()) == 6  # script, storyboard, image, tts, bgm, video_composer

    def test_get_generator(self):
        resp = client.get("/api/v1/generators/script")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Script Generator"

    def test_get_nonexistent_generator(self):
        resp = client.get("/api/v1/generators/nonexistent")
        assert resp.status_code == 404


# ─── Health & Root ───────────────────────────────────────────────────

class TestHealthAndRoot:
    """Test health check and root endpoints"""

    def test_health(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "checks" in data
        assert data["checks"]["database"]["status"] == "healthy"

    def test_root(self):
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Ops-Video"
        assert resp.json()["status"] == "running"


# ─── Edge Cases ──────────────────────────────────────────────────────

class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_create_project_empty_name(self):
        resp = client.post("/api/v1/projects", json={"name": ""})
        # Name has min_length=1 validation
        assert resp.status_code == 422

    def test_update_nonexistent_task(self):
        resp = client.put(
            f"/api/v1/tasks/{uuid4()}/status",
            json={"status": "completed"},
        )
        assert resp.status_code == 404

    def test_delete_nonexistent_file(self):
        resp = client.delete(f"/api/v1/files/{uuid4()}")
        assert resp.status_code == 404

    def test_select_variant_nonexistent_group(self):
        resp = client.post(
            f"/api/v1/variants/{uuid4()}/select",
            json={"file_id": str(uuid4())},
        )
        assert resp.status_code == 404

    def test_workflow_advance_invalid_stage(self):
        project_resp = create_project()
        project_id = project_resp.json()["id"]
        resp = client.post(f"/api/v1/workflow/{project_id}/advance/invalid_stage")
        assert resp.status_code == 400

    def test_rollback_invalid_stage(self):
        project_resp = create_project()
        project_id = project_resp.json()["id"]
        resp = client.post(f"/api/v1/workflow/{project_id}/rollback/invalid_stage")
        assert resp.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
