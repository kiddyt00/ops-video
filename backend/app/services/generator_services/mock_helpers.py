"""
Shared mock helpers for generator services.
When MOCK_MODE is True, services return fake data without calling external APIs.
"""
import json
from pathlib import Path
from uuid import UUID

from ...config import settings
from ...providers.base_provider import GenerationResult


class MockGenerationResult(GenerationResult):
    """Fake generation result for mock mode."""
    pass


def _mock_file(directory: str, filename: str, content: str | bytes) -> Path:
    """Write a mock file to storage and return its Path."""
    dir_path = settings.storage_path / directory
    dir_path.mkdir(parents=True, exist_ok=True)
    file_path = dir_path / filename
    mode = "wb" if isinstance(content, bytes) else "w"
    with open(file_path, mode) as f:
        f.write(content)
    return file_path


def mock_script_result(topic: str, style: str = "comic", **_) -> MockGenerationResult:
    """Return a mock script generation result."""
    content = f"""# Mock Script
# Topic: {topic}
# Style: {style}

## Scene 1
A character stands in a futuristic city.

## Scene 2
The character approaches a glowing terminal.

## Scene 3
Data streams illuminate the room.
"""
    file_path = _mock_file("scripts", f"mock_script_{topic[:10]}.txt", content)
    return MockGenerationResult(
        success=True,
        file_paths=[file_path],
        parameters={"topic": topic, "style": style},
        metadata={"mock": True, "provider": "mock_llm"},
    )


def mock_storyboard_result(panel_count: int = 6, **_) -> MockGenerationResult:
    """Return a mock storyboard generation result."""
    panels = []
    for i in range(panel_count):
        panels.append({
            "panel_index": i,
            "scene_number": i + 1,
            "description": f"Scene {i+1} - A dramatic moment in the story",
            "text": f"Dialogue for scene {i+1}",
            "image_prompt": f"A cinematic shot of scene {i+1}, dramatic lighting, manga style, detailed illustration",
            "duration": 3.0,
            "camera_angle": "medium",
            "emotion": "dramatic",
        })
    storyboard = {"panels": panels}
    content = json.dumps(storyboard, indent=2, ensure_ascii=False)
    file_path = _mock_file("storyboards", f"mock_storyboard_{panel_count}panels.json", content)
    return MockGenerationResult(
        success=True,
        file_paths=[file_path],
        parameters={"panel_count": panel_count},
        metadata={"mock": True, "provider": "mock_llm"},
    )


def mock_image_result(prompt: str = "", variant_index: int = 0, **_) -> MockGenerationResult:
    """Return a mock image generation result.
    Creates a tiny valid PNG (1x1 pixel)."""
    # Minimal 1x1 transparent PNG (67 bytes)
    png_header = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
        0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4,
        0x89, 0x00, 0x00, 0x00, 0x0A, 0x49, 0x44, 0x41,
        0x54, 0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00,
        0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4, 0x00,
        0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE,
        0x42, 0x60, 0x82,
    ])
    file_path = _mock_file("images", f"mock_image_v{variant_index}.png", png_header)
    return MockGenerationResult(
        success=True,
        file_paths=[file_path],
        parameters={"prompt": prompt, "variant_index": variant_index},
        metadata={"mock": True, "provider": "mock_wanx"},
    )


def mock_story_data(inspiration: str = "", **_) -> dict:
    """Return fake story generation data for MOCK_MODE."""
    return {
        "inspiration": inspiration or "A mysterious artifact is discovered beneath an ancient city.",
        "logline": "A lone explorer discovers a secret that changes everything.",
        "synopsis": "In a world where ancient technology lies dormant, one discovery awakens a forgotten power.",
        "worldbuilding": {
            "setting": "A post-apocalyptic Earth where nature has reclaimed civilization",
            "time_period": "Near future",
            "technology_level": "Advanced but decaying",
        },
        "characters": [
            {"name": "Kai", "role": "Protagonist", "description": "A curious young explorer"},
            {"name": "Lena", "role": "Mentor", "description": "A wise elder with hidden knowledge"},
        ],
        "themes": ["Discovery", "Identity", "Technology vs Nature"],
        "plot_points": [
            {"act": "Setup", "description": "Kai finds the artifact"},
            {"act": "Confrontation", "description": "Forces are awakened"},
            {"act": "Resolution", "description": "A new balance is found"},
        ],
    }


def mock_chapter_outline_data(story_data: dict | None = None, chapter_count: int = 6) -> dict:
    """Return fake chapter outline data for MOCK_MODE."""
    chapters = []
    for i in range(chapter_count):
        chapters.append({
            "chapter_number": i + 1,
            "title": f"Chapter {i + 1}: The Beginning",
            "summary": f"The story unfolds in chapter {i + 1} as events take an unexpected turn.",
            "key_scenes": [f"Scene {i*2 + 1}: Setup", f"Scene {i*2 + 2}: Climax"],
            "characters": ["Kai", "Lena"],
            "duration": 5.0,
        })
    return {"chapters": chapters}


def mock_chapter_body_data(chapter_number: int, title: str, summary: str) -> dict:
    """Return fake chapter body data for MOCK_MODE."""
    body = f"""第{chapter_number}章：{title}

{summary}

清晨的阳光穿过稀疏的云层，洒在废墟之上。空气中弥漫着金属和尘土混合的气味。

Kai 小心翼翼地拨开前方的藤蔓，指尖触碰到一块冰凉的金属表面。那是一个古老的终端，表面已经被苔藓覆盖，但隐约还能看到下方闪烁的微光。

"这不可能……"他喃喃自语，心跳加速。

在过去的三个月里，他走遍了这片废土，从未见过任何尚在运作的前代科技。然而眼前的终端屏幕，正以缓慢的节奏闪烁着暗蓝色的光芒。

"Lena 说过，旧世界的遗迹都只是死物。"Kai 把手按在终端表面，感受着微弱的振动。"但这不是死物。它在等什么。"

突然，终端发出一声低沉的嗡鸣。一道全息投影从终端上方的裂缝中投射而出，在半空中形成了一幅旋转的地图——标注着他从未见过的坐标符号。

"这是一个邀请。"Kai 深吸一口气，"或是一个陷阱。"

远处传来低沉的雷鸣，乌云正在聚集。风暴将至，但他已无退路。"""
    word_count = len(body.replace(" ", "").replace("\n", ""))
    return {
        "chapter_number": chapter_number,
        "title": title,
        "body_text": body,
        "word_count": word_count,
    }
