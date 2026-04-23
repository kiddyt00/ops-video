"""
Shared mock helpers for generator services.
When MOCK_MODE is True, services return fake data without calling external APIs.
"""
import json
from pathlib import Path
from uuid import UUID

from ..config import settings
from .base_provider import GenerationResult


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
            "scene_description": f"Scene {i+1} - A dramatic moment in the story",
            "text": f"Dialogue for scene {i+1}",
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
