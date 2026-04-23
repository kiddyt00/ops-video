#!/usr/bin/env python3
"""
End-to-end manga video generation pipeline - v2 (direct API calls)
Theme: 《猫勇者的便利店奇遇》
"""
import os, sys, json, time, base64, asyncio
from pathlib import Path

BASE = Path("/mnt/c/Users/morefine/projects/ops-video/backend")
sys.path.insert(0, str(BASE))
os.chdir(BASE)

API_KEY = "sk-b8bd0f8077764c59b948c503cf1ee5f7"
STORAGE = BASE / "storage"
for d in ["scripts","storyboards","images","audio","video","audio/sfx","audio/bgm","audio/tts"]:
    (STORAGE / d).mkdir(parents=True, exist_ok=True)

import httpx

print("=" * 60)
print("🎬 《猫勇者的便利店奇遇》- 全链路生成 v2")
print("=" * 60)

# ── 6 Panels with full data ──
panels = [
    {
        "panel_number": 1,
        "scene": "暴雨倾盆的冷色调城市后巷，青苔斑驳的湿滑砖墙被雨水冲刷出细碎反光；俯拍视角下，一只瘦小三花猫蜷缩在破损纸箱下避雨，右耳缺一角，湿毛紧贴脊背，琥珀色瞳孔在闪电中收缩",
        "image_prompt": "Anime style manga panel: a small calico cat with a torn right ear huddling under a cardboard box in heavy rain at night, cold blue tones, wet fur, glowing amber eyes, lightning flash, rain drops, detailed manga art, cel-shaded, cinematic lighting, vertical composition 9:16",
        "dialogue": "又是饿肚子的一天……",
        "sfx_type": "rain",
        "duration": 3.0,
    },
    {
        "panel_number": 2,
        "scene": "街角突然出现一家亮着暖黄色灯光的深夜便利店，在雨夜中格外醒目，门上挂着「廿四时便利店」招牌",
        "image_prompt": "Anime style manga panel: a mysterious convenience store glowing with warm yellow light on a rainy street corner at night, neon sign reads '24h', rain reflections on wet ground, cozy atmosphere, manga art style, Studio Ghibli inspired, vertical composition 9:16",
        "dialogue": "喵？",
        "sfx_type": "sparkle",
        "duration": 3.0,
    },
    {
        "panel_number": 3,
        "scene": "便利店内部，穿旧毛衣戴圆眼镜的老者（魔法师）微笑着递给猫咪一件发着蓝光的魔法斗篷",
        "image_prompt": "Anime style manga panel: an old wizard in a sweater and round glasses smiling warmly, holding out a glowing blue magical cloak to a small cat inside a cozy convenience store, magical atmosphere, warm lighting, manga art style, detailed interior, vertical composition 9:16",
        "dialogue": "这件斗篷，也许属于你……",
        "sfx_type": "sparkle",
        "duration": 4.0,
    },
    {
        "panel_number": 4,
        "scene": "猫咪穿上斗篷后，便利店墙壁消失，眼前是奇幻异世界草原，远处有漂浮的岛屿和飞龙",
        "image_prompt": "Anime style manga panel: a small cat wearing a flowing blue magical cloak standing at the edge of a vast fantasy world, floating islands in the sky, flying dragons, epic landscape, sense of wonder, vibrant colors, manga art style, vertical composition 9:16",
        "dialogue": "喵呜！！！",
        "sfx_type": "impact",
        "duration": 3.0,
    },
    {
        "panel_number": 5,
        "scene": "猫咪与巨大的半透明史莱姆战斗，它灵活地跃起攻击，蓝色斗篷发出耀眼光芒",
        "image_prompt": "Anime style manga panel: a heroic small cat wearing a glowing blue cloak leaping mid-air to attack a giant translucent slime monster, dynamic action pose, battle effects, dramatic lighting, manga art style, sense of motion, vertical composition 9:16",
        "dialogue": "喵！我不怕你！",
        "sfx_type": "impact",
        "duration": 3.0,
    },
    {
        "panel_number": 6,
        "scene": "猫咪站在漂浮岛屿顶端，披着斗篷俯瞰整个异世界，远处便利店还亮着微光",
        "image_prompt": "Anime style manga panel: a heroic small cat wearing a flowing blue cloak standing on top of a floating island, overlooking a vast fantasy world, epic sunset, wind blowing the cloak, sense of achievement, beautiful landscape, manga art style, vertical composition 9:16",
        "dialogue": "我有了家，也有了使命。",
        "sfx_type": "whoosh",
        "duration": 4.0,
    },
]

# ── Stage 1: Generate images via Wanx API ──
print("\n" + "=" * 60)
print("🖼️  Stage 1: 生成图片 (通义万相 wanx2.1-t2i-turbo)")
print("=" * 60)

def wait_wanx_task(task_id, headers, client, timeout=60):
    start = time.time()
    while time.time() - start < timeout:
        resp = client.get(f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}", headers=headers)
        data = resp.json()
        status = data["output"]["task_status"]
        if status == "SUCCEEDED":
            return data
        elif status == "FAILED":
            raise RuntimeError(f"Task failed: {data['output'].get('message','')}")
        time.sleep(3)
    raise TimeoutError("Task timed out")

wanx_headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "X-DashScope-Async": "enable",
}

image_paths = []
with httpx.Client(timeout=120) as client:
    for i, panel in enumerate(panels):
        print(f"\n  [{i+1}/6] 生成分镜 {panel['panel_number']}...")
        try:
            # Submit
            payload = {
                "model": "wanx2.1-t2i-turbo",
                "input": {"prompt": panel["image_prompt"]},
                "parameters": {"size": "1024*1024", "n": 1},
            }
            resp = client.post(
                "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis",
                headers=wanx_headers, json=payload,
            )
            resp.raise_for_status()
            task_id = resp.json()["output"]["task_id"]
            print(f"    任务ID: {task_id}")

            # Wait
            result = wait_wanx_task(task_id, wanx_headers, client, timeout=90)
            
            # Download
            img_url = result["output"]["results"][0]["url"]
            img_resp = client.get(img_url)
            img_resp.raise_for_status()
            
            img_path = STORAGE / "images" / f"panel_{panel['panel_number']:02d}_{int(time.time())}.png"
            img_path.write_bytes(img_resp.content)
            image_paths.append(img_path)
            print(f"    ✅ 保存: {img_path} ({len(img_resp.content)/1024:.0f} KB)")
            
        except Exception as e:
            print(f"    ❌ 失败: {e}")

print(f"\n✅ 图片生成完成: {len(image_paths)}/6")

# ── Stage 2: Generate TTS via edge-tts ──
print("\n" + "=" * 60)
print("🔊 Stage 2: 生成 TTS (edge-tts)")
print("=" * 60)

tts_paths = []
try:
    import edge_tts
    async def tts_one(text, output_path, voice="zh-CN-XiaoxiaoNeural"):
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(output_path))
    
    for i, panel in enumerate(panels):
        dialogue = panel["dialogue"]
        tts_path = STORAGE / "audio" / "tts" / f"tts_p{i+1}_{int(time.time())}.mp3"
        print(f"  [{i+1}/6] TTS: '{dialogue}'")
        asyncio.run(tts_one(dialogue, tts_path))
        tts_paths.append(tts_path)
        print(f"    ✅ {tts_path}")
except Exception as e:
    print(f"  ❌ TTS 失败: {e}")

# ── Stage 3: Generate SFX ──
print("\n" + "=" * 60)
print("🎵 Stage 3: 生成 SFX + BGM (scipy)")
print("=" * 60)

from app.services.sfx_service import sfx_service
from app.services.bgm_service import bgm_service

sfx_paths = []
for i, panel in enumerate(panels):
    sfx_type = panel["sfx_type"]
    sfx_path = sfx_service.generate(
        sfx_type=sfx_type,
        duration=panel["duration"] * 0.3,
        intensity=0.6,
        output_filename=f"sfx_{sfx_type}_p{i+1}_{time.time_ns()}.wav",
    )
    sfx_paths.append(sfx_path)
    print(f"  [{i+1}/6] SFX '{sfx_type}': {sfx_path.name} ({sfx_path.stat().st_size/1024:.0f} KB)")

total_dur = sum(p["duration"] for p in panels)
bgm_path = bgm_service.generate(duration=total_dur, mood="dramatic")
print(f"\n  BGM: {bgm_path.name} ({bgm_path.stat().st_size/1024:.0f} KB)")

# ── Stage 4: Video Composition ──
print("\n" + "=" * 60)
print("🎬 Stage 4: 视频合成 (FFmpeg)")
print("=" * 60)

from app.services.video_synthesis_service import video_synthesis_service

# Build panels for video composer
video_panels = []
for i, panel in enumerate(panels):
    img = str(image_paths[i]) if i < len(image_paths) else None
    aud = str(tts_paths[i]) if i < len(tts_paths) else None
    sfx = str(sfx_paths[i]) if i < len(sfx_paths) else None
    video_panels.append({
        "image_path": img,
        "audio_path": aud,
        "sfx_path": sfx,
        "duration": panel["duration"],
        "text": panel["dialogue"],
    })
    print(f"  面板 {i+1}: image={'有' if img else '❌'}, tts={'有' if aud else '❌'}, sfx={'有' if sfx else '❌'}, dur={panel['duration']}s")

try:
    video_path = video_synthesis_service.compose(
        panels=video_panels,
        bgm_path=bgm_path,
        resolution=(1080, 1920),
        fps=24,
        transition="fade",
        transition_duration=0.5,
    )
    print(f"\n✅ 视频合成成功: {video_path}")
    print(f"   大小: {video_path.stat().st_size / 1024 / 1024:.1f} MB")
except Exception as e:
    print(f"\n⚠️  视频合成失败: {e}")
    # Try without audio
    try:
        print("  尝试仅视频合成...")
        no_audio_panels = [{"image_path": vp["image_path"], "duration": vp["duration"], "text": vp["text"]} for vp in video_panels]
        video_path = video_synthesis_service.compose(
            panels=no_audio_panels,
            bgm_path=None,
            resolution=(1080, 1920),
            fps=24,
        )
        print(f"✅ 视频合成成功 (无音频): {video_path}")
        print(f"   大小: {video_path.stat().st_size / 1024 / 1024:.1f} MB")
    except Exception as e2:
        print(f"❌ 视频合成最终失败: {e2}")
        video_path = None

# ── Summary ──
print("\n" + "=" * 60)
print("📊 生成完成总结")
print("=" * 60)
print(f"\n  图片: {len(image_paths)}/6")
print(f"  TTS:  {len(tts_paths)}/6")
print(f"  SFX:  {len(sfx_paths)}/6")
print(f"  BGM:  {'有' if bgm_path and bgm_path.exists() else '无'}")
print(f"  视频: {'✅ ' + str(video_path) if video_path else '❌'}")

if video_path and video_path.exists():
    dest = Path("/mnt/c/Users/morefine/Desktop/猫勇者的便利店奇遇.mp4")
    import shutil
    shutil.copy2(video_path, dest)
    print(f"\n🎬 视频已复制到桌面: {dest}")

print("\n" + "=" * 60)
print("✨ 全链路生成完成！")
print("=" * 60)
