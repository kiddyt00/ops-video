#!/usr/bin/env python3
"""真实 API 全链路视频生成 — 小猫的奇幻冒险"""
import sys, json, time, os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Use SQLite for standalone run
os.environ["DATABASE_URL"] = "sqlite:///./ops_video_pipeline.db"

# Before importing app, create tables
from app.models.declarative import Base
from app.db.session import engine
Base.metadata.create_all(bind=engine)

from app.config import settings
from app.db.session import get_db, SessionLocal
from app.main import app
from fastapi.testclient import TestClient

# Override storage to persist
settings.STORAGE_PATH = str(Path(__file__).parent / "storage")
for k, v in {
    "images": settings.storage_path / "images",
    "audio": settings.storage_path / "audio",
    "video": settings.storage_path / "video",
    "scripts": settings.storage_path / "scripts",
    "storyboards": settings.storage_path / "storyboards",
}.items():
    v.mkdir(parents=True, exist_ok=True)
    import app.config as cfg
    cfg.STORAGE_DIRS[k] = v

# Patch service dirs
from app.services.tts_service import tts_service
from app.services.bgm_service import bgm_service
from app.services.video_synthesis_service import video_synthesis_service
tts_service.AUDIO_DIR = settings.storage_path / "audio"
bgm_service.AUDIO_DIR = settings.storage_path / "audio" / "bgm"
video_synthesis_service.video_dir = settings.storage_path / "video"
bgm_service.AUDIO_DIR.mkdir(parents=True, exist_ok=True)

client = TestClient(app)

print("=" * 60)
print("🎬 小猫的奇幻冒险 — 全链路真实生成")
print(f"   LLM: {settings.LLM_MODEL}")
print(f"   Image: {settings.DASHSCOPE_MODEL}")
print(f"   Storage: {settings.storage_path}")
print("=" * 60)

# ─── Step 1: Create Project ───
print("\n📝 Step 1: 创建项目...")
resp = client.post("/api/v1/projects", json={
    "name": "小猫的奇幻冒险",
    "description": "一只橘猫的魔法森林冒险故事 — 全API生成"
})
assert resp.status_code == 201, f"Create project failed: {resp.text}"
project_id = resp.json()["id"]
print(f"   ✅ 项目 ID: {project_id}")

# ─── Step 2: Script Generation (LLM) ───
print("\n📜 Step 2: 生成脚本 (LLM)...")
resp = client.post(
    f"/api/v1/workflow/{project_id}/advance/script",
    params={"topic": "一只橘猫在魔法森林中的冒险故事，遇到会说话的兔子和发光的蘑菇", "style": "童话风格"}
)
assert resp.status_code == 200, f"Script gen failed: {resp.text}"
task_id = resp.json()["id"]
print(f"   ✅ Script task: {task_id}")

# Mark task completed, create variant + file
client.put(f"/api/v1/tasks/{task_id}/status", json={"status": "completed", "reason": "LLM generated"})
vg = client.post("/api/v1/variants", json={
    "project_id": project_id, "task_id": task_id,
    "stage": "script", "generation_params": {"topic": "橘猫冒险"}
})
vg_id = vg.json()["id"]
f_resp = client.post("/api/v1/files", json={
    "project_id": project_id, "task_id": task_id,
    "variant_group_id": vg_id, "file_type": "script",
    "file_path": "scripts/script_xiaomao.txt",
    "generation_params": {}
})
file_id = f_resp.json()["id"]

# Read the actual script
script_file = settings.storage_path / "scripts" / "script_xiaomao.txt"
if script_file.exists():
    script_content = script_file.read_text(encoding='utf-8')
    print(f"   📄 Script ({len(script_content)} chars):")
    for line in script_content.split('\n')[:8]:
        print(f"      {line}")
else:
    print("   ⚠️ Script file not found, check storage")

client.post(f"/api/v1/variants/{vg_id}/select", json={"file_id": file_id})

# ─── Step 3: Storyboard Generation (LLM) ───
print("\n🎬 Step 3: 生成分镜 (LLM)...")
resp = client.post(f"/api/v1/workflow/{project_id}/advance/storyboard")
assert resp.status_code == 200, f"Storyboard gen failed: {resp.text}"
task_id = resp.json()["id"]
print(f"   ✅ Storyboard task: {task_id}")

client.put(f"/api/v1/tasks/{task_id}/status", json={"status": "completed"})
vg = client.post("/api/v1/variants", json={
    "project_id": project_id, "task_id": task_id,
    "stage": "storyboard", "generation_params": {}
})
vg_id = vg.json()["id"]
f_resp = client.post("/api/v1/files", json={
    "project_id": project_id, "task_id": task_id,
    "variant_group_id": vg_id, "file_type": "storyboard",
    "file_path": "storyboards/storyboard_xiaomao.json",
    "generation_params": {}
})
file_id = f_resp.json()["id"]

# Read storyboard
sb_file = settings.storage_path / "storyboards" / "storyboard_xiaomao.json"
if sb_file.exists():
    sb = json.loads(sb_file.read_text())
    panels = sb.get("panels", [])
    print(f"   📋 {len(panels)} panels")
    for i, p in enumerate(panels):
        print(f"      Panel {i+1}: {p.get('text', p.get('description', ''))[:50]}...")
else:
    print("   ⚠️ Storyboard not found")

client.post(f"/api/v1/variants/{vg_id}/select", json={"file_id": file_id})

# ─── Step 4: Image Generation (DashScope Wanx) ───
print("\n🖼️ Step 4: 生成图片 (DashScope Wanx)...")
resp = client.post(f"/api/v1/workflow/{project_id}/advance/image")
if resp.status_code == 200:
    task_id = resp.json()["id"]
    print(f"   ✅ Image task: {task_id}")
    image_ok = True
else:
    print(f"   ⚠️ Image advance returned {resp.status_code}: {resp.text[:200]}")
    image_ok = False

if image_ok:
    client.put(f"/api/v1/tasks/{task_id}/status", json={"status": "completed"})
    vg = client.post("/api/v1/variants", json={
        "project_id": project_id, "task_id": task_id,
        "stage": "image", "generation_params": {}
    })
    vg_id = vg.json()["id"]
    f_resp = client.post("/api/v1/files", json={
        "project_id": project_id, "task_id": task_id,
        "variant_group_id": vg_id, "file_type": "image",
        "file_path": "images/panel_1.png",
        "generation_params": {}
    })
    file_id = f_resp.json()["id"]
    client.post(f"/api/v1/variants/{vg_id}/select", json={"file_id": file_id})

    # Check generated images
    import os
    img_dir = settings.storage_path / "images"
    imgs = sorted(img_dir.glob("*.png"))
    print(f"   🖼️ {len(imgs)} images in storage:")
    for img in imgs[-6:]:
        print(f"      {img.name} ({img.stat().st_size} bytes)")

# ─── Step 5: Audio Generation (TTS + BGM) ───
print("\n🔊 Step 5: 生成音频 (TTS + BGM)...")
resp = client.post(f"/api/v1/workflow/{project_id}/advance/audio")
if resp.status_code == 200:
    task_id = resp.json()["id"]
    print(f"   ✅ Audio task: {task_id}")
    audio_ok = True
else:
    print(f"   ⚠️ Audio advance returned {resp.status_code}: {resp.text[:300]}")
    audio_ok = False

if audio_ok:
    client.put(f"/api/v1/tasks/{task_id}/status", json={"status": "completed"})
    vg = client.post("/api/v1/variants", json={
        "project_id": project_id, "task_id": task_id,
        "stage": "audio", "generation_params": {}
    })
    vg_id = vg.json()["id"]
    f_resp = client.post("/api/v1/files", json={
        "project_id": project_id, "task_id": task_id,
        "variant_group_id": vg_id, "file_type": "audio",
        "file_path": "audio/test_audio.wav",
        "generation_params": {}
    })
    file_id = f_resp.json()["id"]
    client.post(f"/api/v1/variants/{vg_id}/select", json={"file_id": file_id})

    audio_dir = settings.storage_path / "audio"
    wavs = sorted(audio_dir.rglob("*.wav"))
    print(f"   🎵 {len(wavs)} audio files:")
    for w in wavs[-8:]:
        print(f"      {w.relative_to(settings.storage_path)} ({w.stat().st_size} bytes)")

# ─── Step 6: Video Composition ───
print("\n🎥 Step 6: 合成视频 (FFmpeg)...")
resp = client.post(f"/api/v1/workflow/{project_id}/advance/video")
if resp.status_code == 200:
    task_id = resp.json()["id"]
    print(f"   ✅ Video task: {task_id}")
    video_ok = True
else:
    print(f"   ⚠️ Video advance returned {resp.status_code}: {resp.text[:300]}")
    video_ok = False

if video_ok:
    client.put(f"/api/v1/tasks/{task_id}/status", json={"status": "completed"})
    vg = client.post("/api/v1/variants", json={
        "project_id": project_id, "task_id": task_id,
        "stage": "video", "generation_params": {}
    })
    vg_id = vg.json()["id"]
    f_resp = client.post("/api/v1/files", json={
        "project_id": project_id, "task_id": task_id,
        "variant_group_id": vg_id, "file_type": "video",
        "file_path": "video/final_video.mp4",
        "generation_params": {}
    })
    file_id = f_resp.json()["id"]
    client.post(f"/api/v1/variants/{vg_id}/select", json={"file_id": file_id})

    video_dir = settings.storage_path / "video"
    mp4s = sorted(video_dir.glob("*.mp4"), key=lambda p: p.stat().st_mtime)
    for v in mp4s[-3:]:
        print(f"   🎬 {v.name}: {v.stat().st_size:,} bytes")

# ─── Final Summary ───
print("\n" + "=" * 60)
print("📊 生成总结")
print("=" * 60)
status = client.get(f"/api/v1/workflow/{project_id}/status")
if status.status_code == 200:
    stages = status.json()
    for name, info in stages.items():
        print(f"   {name}: {info.get('status', 'unknown')}")

files = client.get("/api/v1/files").json()
print(f"   文件总数: {len(files)}")

print(f"\n   存储路径: {settings.storage_path}")
print(f"   视频: {settings.storage_path}/video/")
print(f"   图片: {settings.storage_path}/images/")
print(f"   音频: {settings.storage_path}/audio/")
