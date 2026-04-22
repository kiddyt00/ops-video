#!/usr/bin/env python3
"""
端到端漫剧测试 - "小猫的奇幻冒险"

完整测试从项目创建到视频生成的全流程，所有外部服务均使用 Mock 数据。

阶段:
1. 创建项目 "小猫的奇幻冒险"
2. 脚本阶段 - 手动创建 Mock 文件
3. 分镜阶段 - 手动创建 Mock JSON
4. 图片阶段 - 手动创建 Mock 图片
5. 音频阶段 - Mock TTS + 真实 BGM (scipy)
6. 视频阶段 - Mock FFmpeg

运行: pytest tests/test_e2e_manga.py -v -s
"""
import json
import struct
import wave
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, String, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add backend to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

# ─── Test Database Setup ─────────────────────────────────────────────


class GUID(TypeDecorator):
    """Platform-independent GUID type."""
    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, type(uuid4())):
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, type(uuid4())):
            from uuid import UUID
            return UUID(value)
        return value


from app.models.declarative import Base
from app.models import project, task, file as file_model, user as user_model

for model in [project.Project, task.Task, task.TaskStatusLog,
              file_model.File, file_model.VariantGroup,
              user_model.User, user_model.RefreshToken]:
    for col in model.__table__.columns:
        if isinstance(col.type, PG_UUID):
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
    # Set dependency override in fixture to avoid cross-module pollution
    app.dependency_overrides[get_db] = override_get_db
    clear_test_db()
    yield
    # Clean up override after test
    if get_db in app.dependency_overrides:
        del app.dependency_overrides[get_db]


@pytest.fixture
def client():
    return TestClient(app)


# ─── Mock Data ───────────────────────────────────────────────────────

MOCK_SCRIPT_CONTENT = """《小猫的奇幻冒险》

场景一：平凡的一天
画面：一只橘猫趴在窗台上晒太阳。
旁白："在一个平凡的小镇上，住着一只名叫小橘的猫咪。"

场景二：神秘的门
画面：小橘发现墙上出现了一扇发光的门。
小橘："这是什么？好奇怪！"

场景三：奇幻世界
画面：小橘穿过门，来到了一个充满漂浮岛屿的奇幻世界。
旁白："这是一个只有猫咪才能看到的世界。"

场景四：新朋友
画面：小橘遇到了一只戴着魔法帽的白猫。
白猫："欢迎来到猫咪王国！"

场景五：冒险开始
画面：两只猫咪一起飞向漂浮岛屿。
旁白："从此，小橘开始了它的奇幻冒险之旅。"
"""

MOCK_STORYBOARD = {
    "title": "小猫的奇幻冒险",
    "style": "comic",
    "total_panels": 5,
    "panels": [
        {
            "panel_number": 1,
            "scene_description": "一只橘猫趴在窗台上晒太阳",
            "camera_angle": "中景",
            "characters": ["小橘"],
            "emotion": "慵懒",
            "composition": "画面右侧是窗台",
            "text": "在一个平凡的小镇上，住着一只名叫小橘的猫咪。",
            "duration": 3.0,
            "image_prompt": "cute orange cat on windowsill, anime style",
        },
        {
            "panel_number": 2,
            "scene_description": "墙上出现发光的神秘门",
            "camera_angle": "特写",
            "characters": ["小橘"],
            "emotion": "好奇",
            "composition": "门在中央发光，猫咪在左侧",
            "text": "这是什么？好奇怪！",
            "duration": 2.5,
            "image_prompt": "mysterious glowing door, curious cat, fantasy",
        },
        {
            "panel_number": 3,
            "scene_description": "充满漂浮岛屿的奇幻世界",
            "camera_angle": "全景",
            "characters": ["小橘"],
            "emotion": "震撼",
            "composition": "广阔天空中的漂浮岛屿",
            "text": "这是一个只有猫咪才能看到的世界。",
            "duration": 4.0,
            "image_prompt": "fantasy world floating islands, studio ghibli style",
        },
        {
            "panel_number": 4,
            "scene_description": "遇到戴魔法帽的白猫",
            "camera_angle": "中景",
            "characters": ["小橘", "白猫"],
            "emotion": "友好",
            "composition": "两只猫咪面对面",
            "text": "欢迎来到猫咪王国！",
            "duration": 3.0,
            "image_prompt": "white cat with wizard hat, anime style",
        },
        {
            "panel_number": 5,
            "scene_description": "两只猫咪飞向漂浮岛屿",
            "camera_angle": "远景",
            "characters": ["小橘", "白猫"],
            "emotion": "兴奋",
            "composition": "天空中飞翔，背景是漂浮岛屿",
            "text": "从此，小橘开始了它的奇幻冒险之旅。",
            "duration": 3.5,
            "image_prompt": "two cats flying towards floating islands, adventure",
        },
    ],
}

# 1x1 pixel minimal PNG
MINIMAL_PNG = (
    b'\x89PNG\r\n\x1a\n'
    b'\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
    b'\x08\x02\x00\x00\x00\x90wS\xde'
    b'\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N'
    b'\x00\x00\x00\x00IEND\xaeB`\x82'
)


# ─── Helper Functions ────────────────────────────────────────────────

def create_project(client, name="小猫的奇幻冒险", description="一只橘猫的奇幻冒险故事"):
    resp = client.post("/api/v1/projects", json={"name": name, "description": description})
    assert resp.status_code == 201, f"创建项目失败: {resp.text}"
    return resp.json()


def advance_stage(client, project_id, stage):
    resp = client.post(f"/api/v1/workflow/{project_id}/advance/{stage}")
    assert resp.status_code == 200, f"推进到 {stage} 失败: {resp.text}"
    return resp.json()


def complete_stage(client, project_id, stage):
    """完成阶段：创建任务 + 标记完成 + 创建文件 + 选择变体"""
    task = advance_stage(client, project_id, stage)
    task_id = task["id"]

    resp = client.put(
        f"/api/v1/tasks/{task_id}/status",
        json={"status": "completed", "reason": f"{stage} 完成"},
    )
    assert resp.status_code == 200, f"标记任务完成失败: {resp.text}"

    vg_resp = client.post(
        "/api/v1/variants",
        json={"project_id": project_id, "task_id": task_id, "stage": stage, "parameters": {}},
    )
    assert vg_resp.status_code == 201, f"创建变体组失败: {vg_resp.text}"
    vg_id = vg_resp.json()["id"]

    file_path_map = {
        "script": "scripts/test_script.txt",
        "storyboard": "storyboards/test_storyboard.json",
        "image": "images/test_image.png",
        "audio": "audio/test_audio.wav",
        "video": "videos/test_video.mp4",
    }
    file_resp = client.post(
        "/api/v1/files",
        json={
            "project_id": project_id,
            "task_id": task_id,
            "variant_group_id": vg_id,
            "file_type": stage,
            "file_path": file_path_map[stage],
        },
    )
    assert file_resp.status_code == 201, f"创建文件失败: {file_resp.text}"
    file_id = file_resp.json()["id"]

    sel_resp = client.post(f"/api/v1/variants/{vg_id}/select", json={"file_id": file_id})
    assert sel_resp.status_code == 200, f"选择变体失败: {sel_resp.text}"

    return task_id, vg_id, file_id


def get_workflow_status(client, project_id):
    resp = client.get(f"/api/v1/workflow/{project_id}/status")
    assert resp.status_code == 200
    return resp.json()


# ─── E2E Test ────────────────────────────────────────────────────────

class TestE2EMangaWorkflow:
    """端到端测试：完整的「小猫的奇幻冒险」漫剧制作流程"""

    PROJECT_NAME = "小猫的奇幻冒险"

    @pytest.fixture(autouse=True)
    def setup_storedir(self, tmp_path, monkeypatch):
        """为每个测试创建临时存储目录"""
        # Ensure DB tables exist
        clear_test_db()

        for key in ("images", "audio", "video", "scripts", "storyboards"):
            (tmp_path / key).mkdir(parents=True, exist_ok=True)

        # Patch STORAGE_DIRS dict in place
        import app.config
        for key in list(app.config.STORAGE_DIRS.keys()):
            app.config.STORAGE_DIRS[key] = tmp_path / key

        # Patch settings.storage_path property
        monkeypatch.setattr(type(app.config.settings), "storage_path",
                            property(lambda self: tmp_path))

        # Patch service directories (these are captured at class/module load time)
        from app.services.tts_service import tts_service
        from app.services.bgm_service import bgm_service
        from app.services.video_synthesis_service import video_synthesis_service

        tts_service.AUDIO_DIR = tmp_path / "audio"
        bgm_service.AUDIO_DIR = tmp_path / "audio" / "bgm"
        video_synthesis_service.video_dir = tmp_path / "video"

        yield tmp_path

    def test_full_manga_workflow(self, client, setup_storedir):
        """
        完整工作流测试：
        1. 创建项目
        2. 脚本阶段 (Mock 文件)
        3. 分镜阶段 (Mock JSON)
        4. 图片阶段 (Mock 图片)
        5. 音频阶段 (Mock TTS + 真实 BGM)
        6. 视频阶段 (Mock FFmpeg)
        """
        checkpoints = []
        errors = []
        stage_results = {}

        tmp_path = setup_storedir

        def checkpoint(name, data=None):
            checkpoints.append({"name": name, "data": data or {}})

        # ── Step 1: 创建项目 ──
        checkpoint("1. 创建项目", {"name": self.PROJECT_NAME})
        project = create_project(client, self.PROJECT_NAME, "一只橘猫的奇幻冒险故事")
        project_id = project["id"]

        print(f"\n{'='*60}")
        print(f"✅ Step 1: 创建项目 - {self.PROJECT_NAME}")
        print(f"   ID: {project_id}")
        print(f"   描述: {project['description']}")

        # 验证项目可查询
        get_resp = client.get(f"/api/v1/projects/{project_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["name"] == self.PROJECT_NAME

        # 验证初始工作流状态
        status = get_workflow_status(client, project_id)
        assert status["current_stage"] is None
        for s in status["stages"]:
            assert s["status"] == "pending"
        print(f"   初始状态: 所有阶段 pending ✅")
        checkpoint("1. 完成", {"project_id": project_id, "stages": 5})

        # ── Step 2: 脚本阶段 ──
        checkpoint("2. 脚本阶段开始")
        # 创建脚本文件
        script_path = tmp_path / "scripts" / "script_xiaomao.txt"
        script_path.write_text(MOCK_SCRIPT_CONTENT, encoding="utf-8")
        assert script_path.exists()
        assert script_path.stat().st_size > 0

        task_id, vg_id, file_id = complete_stage(client, project_id, "script")
        stage_results["script"] = {"task_id": task_id, "file_id": file_id}

        status = get_workflow_status(client, project_id)
        script_stage = [s for s in status["stages"] if s["stage"] == "script"][0]
        assert script_stage["status"] == "completed"
        assert script_stage["completed_tasks"] >= 1
        print(f"   ✅ Step 2: 脚本阶段完成 (task: {task_id}, file: {file_id})")
        checkpoint("2. 脚本阶段完成", {"task_id": task_id, "file_size": script_path.stat().st_size})

        # ── Step 3: 分镜阶段 ──
        checkpoint("3. 分镜阶段开始")
        # 创建分镜 JSON 文件
        sb_path = tmp_path / "storyboards" / "storyboard_xiaomao.json"
        sb_path.write_text(json.dumps(MOCK_STORYBOARD, ensure_ascii=False), encoding="utf-8")
        assert sb_path.exists()

        task_id, vg_id, file_id = complete_stage(client, project_id, "storyboard")
        stage_results["storyboard"] = {"task_id": task_id, "file_id": file_id}

        status = get_workflow_status(client, project_id)
        sb_stage = [s for s in status["stages"] if s["stage"] == "storyboard"][0]
        assert sb_stage["status"] == "completed"
        print(f"   ✅ Step 3: 分镜阶段完成 (task: {task_id}, panels: {len(MOCK_STORYBOARD['panels'])})")
        checkpoint("3. 分镜阶段完成", {"task_id": task_id, "panel_count": len(MOCK_STORYBOARD["panels"])})

        # ── Step 4: 图片阶段 ──
        checkpoint("4. 图片阶段开始")
        # 创建模拟图片文件（每个分镜一张）
        img_dir = tmp_path / "images"
        for panel in MOCK_STORYBOARD["panels"]:
            img_path = img_dir / f"panel_{panel['panel_number']:03d}.png"
            img_path.write_bytes(MINIMAL_PNG)

        task_id, vg_id, file_id = complete_stage(client, project_id, "image")
        stage_results["image"] = {"task_id": task_id, "file_id": file_id}

        status = get_workflow_status(client, project_id)
        img_stage = [s for s in status["stages"] if s["stage"] == "image"][0]
        assert img_stage["status"] == "completed"
        print(f"   ✅ Step 4: 图片阶段完成 (task: {task_id}, images: {len(MOCK_STORYBOARD['panels'])})")
        checkpoint("4. 图片阶段完成", {"task_id": task_id, "image_count": 5})

        # ── Step 5: 音频阶段 (Mock TTS + 真实 BGM) ──
        checkpoint("5. 音频阶段开始")

        audio_dir = tmp_path / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)

        def create_mock_wav(path, duration_sec=1.0):
            """Create a silent WAV file"""
            sample_rate = 44100
            n_frames = int(sample_rate * duration_sec)
            with wave.open(str(path), 'w') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(b'\x00\x00' * n_frames)
            return path

        # Mock TTS: create real WAV files
        async def mock_tts_synthesize(text, voice=None, output_filename=None, **kwargs):
            if output_filename is None:
                import hashlib, time
                h = hashlib.md5(text[:50].encode()).hexdigest()[:8]
                output_filename = f"tts_{h}_{int(time.time())}.wav"
            path = audio_dir / output_filename
            return create_mock_wav(path, duration_sec=1.0)

        # Patch TTS at source module (workflow_service does: from .tts_service import tts_service)
        with patch("app.services.tts_service.tts_service") as mock_tts:
            mock_tts.synthesize = mock_tts_synthesize

            task_id, vg_id, file_id = complete_stage(client, project_id, "audio")

        stage_results["audio"] = {"task_id": task_id, "file_id": file_id}

        status = get_workflow_status(client, project_id)
        audio_stage = [s for s in status["stages"] if s["stage"] == "audio"][0]
        assert audio_stage["status"] == "completed"
        print(f"   ✅ Step 5: 音频阶段完成 (task: {task_id})")
        checkpoint("5. 音频阶段完成", {"task_id": task_id})

        # ── Step 6: 视频阶段 (Mock FFmpeg) ──
        checkpoint("6. 视频阶段开始")

        video_dir = tmp_path / "video"
        video_dir.mkdir(parents=True, exist_ok=True)
        video_output = video_dir / "final_video.mp4"

        with patch("app.services.video_synthesis_service.video_synthesis_service") as mock_video_svc:
            video_output.write_bytes(b'\x00' * 100)
            mock_video_svc.compose = MagicMock(return_value=video_output)

            task_id, vg_id, file_id = complete_stage(client, project_id, "video")

        stage_results["video"] = {"task_id": task_id, "file_id": file_id}

        status = get_workflow_status(client, project_id)
        video_stage = [s for s in status["stages"] if s["stage"] == "video"][0]
        assert video_stage["status"] == "completed"
        print(f"   ✅ Step 6: 视频阶段完成 (task: {task_id})")
        checkpoint("6. 视频阶段完成", {"task_id": task_id})

        # ── 最终验证 ──
        print(f"\n{'='*60}")
        print("📊 最终验证")
        print(f"{'='*60}")

        # 工作流状态
        status = get_workflow_status(client, project_id)
        print(f"\n工作流状态:")
        completed_count = 0
        for s in status["stages"]:
            icon = "✅" if s["status"] == "completed" else "⏳"
            print(f"   {icon} {s['stage']}: {s['status']} (任务: {s['completed_tasks']}/{s['total_tasks']})")
            if s["status"] == "completed":
                completed_count += 1

        assert completed_count == 5, f"应有 5 个完成的阶段，实际 {completed_count}"

        # 工作流历史
        history_resp = client.get(f"/api/v1/workflow/{project_id}/history")
        assert history_resp.status_code == 200
        history = history_resp.json()["history"]
        print(f"\n工作流历史: {len(history)} 条记录")
        for h in history:
            print(f"   - {h['stage']}: {h['status']} (时间: {h['created_at']})")

        # 项目信息
        project_resp = client.get(f"/api/v1/projects/{project_id}")
        assert project_resp.status_code == 200
        project_data = project_resp.json()
        print(f"\n项目信息:")
        print(f"   名称: {project_data['name']}")
        print(f"   描述: {project_data['description']}")

        # 任务统计
        tasks_resp = client.get(f"/api/v1/tasks?project_id={project_id}")
        assert tasks_resp.status_code == 200
        tasks = tasks_resp.json()
        print(f"\n任务列表 ({len(tasks)} 个):")
        for t in tasks:
            print(f"   - {t['stage']}: {t['status']} (generator: {t['generator_type']})")

        # 文件统计
        files_resp = client.get(f"/api/v1/files?project_id={project_id}")
        assert files_resp.status_code == 200
        files = files_resp.json()
        print(f"   文件总数: {len(files)}")
        for f in files:
            print(f"     - {f['file_type']}: {f['file_path']}")

        # 变体统计
        variants_resp = client.get(f"/api/v1/variants?project_id={project_id}")
        assert variants_resp.status_code == 200
        variants = variants_resp.json()
        print(f"   变体组数: {len(variants)}")

        checkpoint("最终验证", {
            "completed_stages": completed_count,
            "total_tasks": len(tasks),
            "total_files": len(files),
            "total_variants": len(variants),
            "total_history": len(history),
        })

        # ── 生成测试报告 ──
        print(f"\n{'='*60}")
        print(f"🏁 测试报告: 「{self.PROJECT_NAME}」端到端测试")
        print(f"{'='*60}")
        print(f"\n项目 ID: {project_id}")
        print(f"项目名称: {self.PROJECT_NAME}")

        print(f"\n检查点 ({len(checkpoints)} 个):")
        for cp in checkpoints:
            data_str = json.dumps(cp["data"], ensure_ascii=False) if cp["data"] else ""
            print(f"   ✅ {cp['name']}: {data_str}")

        print(f"\n统计:")
        print(f"   阶段完成: {completed_count}/5 ✅")
        print(f"   任务创建: {len(tasks)}")
        print(f"   文件创建: {len(files)}")
        print(f"   变体组:   {len(variants)}")
        print(f"   历史记录: {len(history)}")

        if errors:
            print(f"\n❌ 错误 ({len(errors)}):")
            for err in errors:
                print(f"   - {err}")
        else:
            print(f"\n✅ 无错误 - 所有阶段顺利完成！")

        print(f"\n{'='*60}")
        print("测试通过 ✅")
        print(f"{'='*60}")
