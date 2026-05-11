"""
Phase 16 tests: Tail-frame extend for continuous i2v scenes

Tests:
- extract_last_frame: FFmpeg extraction of final frame from a video clip
- extend method: WanVideoProvider.extend() with mocked API
- scene_grouping: I2VComposer.group_panels_by_scene() logic
- compose_episode_with_tail_extend: end-to-end with mocked provider
"""
import asyncio
import os
import subprocess
import struct
import sys
import zlib
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.providers.base_provider import GenerationResult
from app.providers.wan_video_provider import WanVideoProvider
from app.services.i2v_composer import I2VComposer


# ─── Fixtures ───────────────────────────────────────────────────────

@pytest.fixture
def home_tmp_dir():
    """Provide a temp directory in home dir (snap ffmpeg can't access /tmp)."""
    d = Path(os.path.expanduser("~")) / "test_tail_frame_tmp"
    d.mkdir(parents=True, exist_ok=True)
    yield d


@pytest.fixture
def sample_image(home_tmp_dir):
    """Create a minimal PNG image for testing."""
    img_path = home_tmp_dir / "test_image.png"

    def chunk(chunk_type, data):
        c = chunk_type + data
        return (
            struct.pack(">I", len(data))
            + c
            + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
        )

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", 10, 10, 8, 2, 0, 0, 0)
    ihdr = chunk(b"IHDR", ihdr_data)

    raw_data = b""
    for y in range(10):
        raw_data += b"\x00"
        for x in range(10):
            raw_data += bytes((255, 0, 0))

    idat = chunk(b"IDAT", zlib.compress(raw_data))
    iend = chunk(b"IEND", b"")

    with open(img_path, "wb") as f:
        f.write(sig + ihdr + idat + iend)

    yield img_path
    try:
        img_path.unlink(missing_ok=True)
    except OSError:
        pass


@pytest.fixture
def sample_video(home_tmp_dir, sample_image):
    """Create a minimal MP4 video from test image using FFmpeg."""
    video_path = home_tmp_dir / "test_video.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(sample_image),
        "-f", "lavfi",
        "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-t", "2",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-r", "24",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        str(video_path),
    ]
    env = os.environ.copy()
    env["LIBGL_ALWAYS_SOFTWARE"] = "1"
    env.pop("DISPLAY", None)
    home = os.path.expanduser("~")
    env["TMPDIR"] = home
    env["TEMP"] = home
    env["TMP"] = home

    result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=60)
    if result.returncode != 0:
        pytest.skip(f"FFmpeg not available or failed: {result.stderr[:200]}")
    yield video_path
    try:
        video_path.unlink(missing_ok=True)
    except OSError:
        pass


@pytest.fixture
def provider():
    """Create a WanVideoProvider instance."""
    return WanVideoProvider(api_key="test-key")


@pytest.fixture
def composer():
    """Create an I2VComposer instance."""
    return I2VComposer()


# ─── test_extract_last_frame ───────────────────────────────────────

class TestExtractLastFrame:
    """Test WanVideoProvider.extract_last_frame()."""

    @pytest.mark.skipif(
        os.environ.get("SKIP_FFMPEG_TESTS") == "1",
        reason="FFmpeg tests skipped",
    )
    def test_extract_last_frame_returns_png(self, provider, sample_video):
        """Should extract last frame as PNG file."""
        result = asyncio.run(provider.extract_last_frame(sample_video))
        assert result is not None
        assert result.exists()
        assert result.suffix == ".png"
        assert result.name == "last_frame.png"

    def test_extract_last_frame_missing_video(self, provider):
        """Should return None for non-existent video."""
        result = asyncio.run(provider.extract_last_frame(Path("/nonexistent/video.mp4")))
        assert result is None

    def test_extract_last_frame_none_path(self, provider):
        """Should handle None/empty path gracefully."""
        result = asyncio.run(provider.extract_last_frame(None))  # type: ignore
        assert result is None


# ─── test_extend_method ────────────────────────────────────────────

class TestExtendMethod:
    """Test WanVideoProvider.extend() with mocked API."""

    def test_extend_calls_generate_with_extracted_frame(self, provider, sample_video, home_tmp_dir):
        """extend() should extract last frame and call generate() with it."""
        # Mock generate to return a successful result
        mock_result = GenerationResult(
            file_paths=[home_tmp_dir / "extended_clip.mp4"],
            parameters={},
            success=True,
        )

        async def mock_generate(params):
            # Verify that image_path was set to a last_frame.png
            assert "image_path" in params
            assert "last_frame.png" in params["image_path"]
            return mock_result

        frame_path = home_tmp_dir / "last_frame.png"
        frame_path.touch()  # Ensure the path "exists"

        with patch.object(provider, "extract_last_frame", new=AsyncMock(return_value=frame_path)):
            with patch.object(provider, "generate", new=mock_generate):
                result = asyncio.run(provider.extend(
                    prev_clip_path=sample_video,
                    prompt="continue the scene",
                    duration=5,
                    output_filename="extended.mp4",
                ))
                assert result.success
                assert len(result.file_paths) == 1

    def test_extend_returns_error_on_extract_failure(self, provider, sample_video):
        """extend() should return error if frame extraction fails."""
        with patch.object(provider, "extract_last_frame", new=AsyncMock(return_value=None)):
            result = asyncio.run(provider.extend(
                prev_clip_path=sample_video,
                prompt="continue",
                duration=5,
            ))
            assert not result.success
            assert result.error_message == "Failed to extract last frame from previous clip"

    def test_extend_returns_error_on_generate_exception(self, provider, sample_video):
        """extend() should catch and report generate() exceptions."""
        fake_frame = Path(os.path.expanduser("~")) / "test_tail_frame_tmp" / "last_frame.png"
        fake_frame.parent.mkdir(parents=True, exist_ok=True)
        fake_frame.touch()

        async def mock_generate(params):
            raise RuntimeError("API connection refused")

        with patch.object(provider, "extract_last_frame", new=AsyncMock(return_value=fake_frame)):
            with patch.object(provider, "generate", new=mock_generate):
                result = asyncio.run(provider.extend(
                    prev_clip_path=sample_video,
                    prompt="continue",
                    duration=5,
                ))
                assert not result.success
                assert "API connection refused" in result.error_message


# ─── test_scene_grouping ───────────────────────────────────────────

class TestSceneGrouping:
    """Test I2VComposer.group_panels_by_scene()."""

    def test_single_scene_when_no_scene_ids(self, composer):
        """Without scene_id, all panels grouped into one scene."""
        panels = [{"image_path": f"img{i}.png"} for i in range(4)]
        sb_panels = [
            {"scene_description": f"Scene desc {i}", "duration": 5}
            for i in range(4)
        ]

        groups = I2VComposer.group_panels_by_scene(panels, sb_panels)
        assert len(groups) == 1
        assert len(groups[0]) == 4
        # Verify tuple structure
        for i, (global_idx, panel, sb) in enumerate(groups[0]):
            assert global_idx == i
            assert panel == panels[i]
            assert sb == sb_panels[i]

    def test_two_scenes(self, composer):
        """Panels with different scene_ids are grouped separately."""
        panels = [{"image_path": f"img{i}.png"} for i in range(5)]
        sb_panels = [
            {"scene_id": "scene_A", "scene_description": "A1", "duration": 5},
            {"scene_id": "scene_A", "scene_description": "A2", "duration": 5},
            {"scene_id": "scene_B", "scene_description": "B1", "duration": 5},
            {"scene_id": "scene_A", "scene_description": "A3", "duration": 5},
            {"scene_id": "scene_B", "scene_description": "B2", "duration": 5},
        ]

        groups = I2VComposer.group_panels_by_scene(panels, sb_panels)
        assert len(groups) == 2

        # First group: scene_A (panels 0, 1, 3)
        assert len(groups[0]) == 3
        assert [g[0] for g in groups[0]] == [0, 1, 3]

        # Second group: scene_B (panels 2, 4)
        assert len(groups[1]) == 2
        assert [g[0] for g in groups[1]] == [2, 4]

    def test_three_scenes_ordered(self, composer):
        """Scene groups maintain first-occurrence order."""
        panels = [{"image_path": f"img{i}.png"} for i in range(3)]
        sb_panels = [
            {"scene_id": "gamma", "duration": 5},
            {"scene_id": "alpha", "duration": 5},
            {"scene_id": "beta", "duration": 5},
        ]

        groups = I2VComposer.group_panels_by_scene(panels, sb_panels)
        assert len(groups) == 3
        assert groups[0][0][0] == 0  # gamma first
        assert groups[1][0][0] == 1  # alpha second
        assert groups[2][0][0] == 2  # beta third

    def test_empty_panels(self, composer):
        """Empty panel list returns empty groups."""
        groups = I2VComposer.group_panels_by_scene([], [])
        assert groups == []

    def test_more_panels_than_storyboard(self, composer):
        """When panels exceed storyboard count, use empty dict for missing."""
        panels = [{"image_path": f"img{i}.png"} for i in range(3)]
        sb_panels = [
            {"scene_description": "only one", "duration": 5},
        ]

        groups = I2VComposer.group_panels_by_scene(panels, sb_panels)
        assert len(groups) == 1
        assert len(groups[0]) == 3
        # First panel has sb data, rest have empty dict
        assert groups[0][0][2] == sb_panels[0]
        assert groups[0][1][2] == {}
        assert groups[0][2][2] == {}


# ─── test_compose_episode_with_tail_extend ──────────────────────────

class TestComposeEpisodeWithTailExtend:
    """Test compose_episode_with_tail_extend end-to-end with mocked provider."""

    @pytest.mark.skipif(
        os.environ.get("SKIP_FFMPEG_TESTS") == "1",
        reason="FFmpeg tests skipped",
    )
    def test_single_scene_tail_extend_chain(self, composer, sample_image, sample_video, home_tmp_dir):
        """Single scene: panel 0 generates, panel 1 extends from panel 0."""
        composer.video_dir = home_tmp_dir / "video"
        composer.video_dir.mkdir(parents=True, exist_ok=True)

        panels = [
            {"image_path": str(sample_image)},
            {"image_path": str(sample_image)},
        ]
        storyboard = {
            "panels": [
                {"scene_description": "Scene A part 1", "duration": 2},
                {"scene_description": "Scene A part 2", "duration": 2},
            ]
        }

        # Use real video copies for FFmpeg processing
        fake_clip1 = home_tmp_dir / "clip1.mp4"
        fake_clip2 = home_tmp_dir / "clip2.mp4"
        fake_clip1.write_bytes(sample_video.read_bytes())
        fake_clip2.write_bytes(sample_video.read_bytes())

        call_count = {"generate": 0, "extend": 0}

        async def mock_generate(params):
            call_count["generate"] += 1
            return GenerationResult(
                file_paths=[fake_clip1],
                parameters=params,
                success=True,
            )

        async def mock_extend(prev_clip_path, prompt, duration, output_filename=""):
            call_count["extend"] += 1
            return GenerationResult(
                file_paths=[fake_clip2],
                parameters={"prev_clip_path": str(prev_clip_path)},
                success=True,
            )

        with patch("app.services.i2v_composer.wan_video_provider") as mock_provider:
            mock_provider.generate = mock_generate
            mock_provider.extend = mock_extend

            result = asyncio.run(
                composer.compose_episode_with_tail_extend(
                    panels=panels,
                    storyboard=storyboard,
                    bgm_path=None,
                    tts_paths=None,
                    sfx_paths=None,
                    resolution=(640, 480),
                    fps=24,
                )
            )

            assert result.exists()
            assert result.suffix == ".mp4"
            assert call_count["generate"] == 1  # First panel
            assert call_count["extend"] == 1    # Second panel extends

    @pytest.mark.skipif(
        os.environ.get("SKIP_FFMPEG_TESTS") == "1",
        reason="FFmpeg tests skipped",
    )
    def test_multiple_scenes_independent_generate(self, composer, sample_image, sample_video, home_tmp_dir):
        """Two scenes: each starts with generate(), no extend across scenes."""
        composer.video_dir = home_tmp_dir / "video"
        composer.video_dir.mkdir(parents=True, exist_ok=True)

        panels = [
            {"image_path": str(sample_image)},
            {"image_path": str(sample_image)},
            {"image_path": str(sample_image)},
        ]
        storyboard = {
            "panels": [
                {"scene_id": "scene_A", "scene_description": "A1", "duration": 2},
                {"scene_id": "scene_B", "scene_description": "B1", "duration": 2},
                {"scene_id": "scene_A", "scene_description": "A2", "duration": 2},
            ]
        }

        fake_clip = home_tmp_dir / "fake_clip.mp4"
        fake_clip.write_bytes(sample_video.read_bytes())
        call_count = {"generate": 0, "extend": 0}

        async def mock_generate(params):
            call_count["generate"] += 1
            return GenerationResult(file_paths=[fake_clip], parameters=params, success=True)

        async def mock_extend(**kwargs):
            call_count["extend"] += 1
            return GenerationResult(file_paths=[fake_clip], parameters=kwargs, success=True)

        with patch("app.services.i2v_composer.wan_video_provider") as mock_provider:
            mock_provider.generate = mock_generate
            mock_provider.extend = mock_extend

            result = asyncio.run(
                composer.compose_episode_with_tail_extend(
                    panels=panels,
                    storyboard=storyboard,
                    resolution=(640, 480),
                    fps=24,
                )
            )

            assert result.exists()
            # Scene A has 2 panels (1 generate + 1 extend)
            # Scene B has 1 panel (1 generate)
            # Total: 2 generates, 1 extend
            assert call_count["generate"] == 2
            assert call_count["extend"] == 1

    @pytest.mark.skipif(
        os.environ.get("SKIP_FFMPEG_TESTS") == "1",
        reason="FFmpeg tests skipped",
    )
    def test_fallback_when_no_scene_ids(self, composer, sample_image, sample_video, home_tmp_dir):
        """Without scene_ids, all panels treated as one continuous scene."""
        composer.video_dir = home_tmp_dir / "video"
        composer.video_dir.mkdir(parents=True, exist_ok=True)

        panels = [
            {"image_path": str(sample_image)},
            {"image_path": str(sample_image)},
            {"image_path": str(sample_image)},
        ]
        storyboard = {
            "panels": [
                {"scene_description": "Part 1", "duration": 2},
                {"scene_description": "Part 2", "duration": 2},
                {"scene_description": "Part 3", "duration": 2},
            ]
        }

        fake_clip = home_tmp_dir / "fake.mp4"
        fake_clip.write_bytes(sample_video.read_bytes())
        call_count = {"generate": 0, "extend": 0}

        async def mock_generate(params):
            call_count["generate"] += 1
            return GenerationResult(file_paths=[fake_clip], parameters=params, success=True)

        async def mock_extend(**kwargs):
            call_count["extend"] += 1
            return GenerationResult(file_paths=[fake_clip], parameters=kwargs, success=True)

        with patch("app.services.i2v_composer.wan_video_provider") as mock_provider:
            mock_provider.generate = mock_generate
            mock_provider.extend = mock_extend

            result = asyncio.run(
                composer.compose_episode_with_tail_extend(
                    panels=panels,
                    storyboard=storyboard,
                    resolution=(640, 480),
                    fps=24,
                )
            )

            assert result.exists()
            # 1 generate (first) + 2 extends (continuations)
            assert call_count["generate"] == 1
            assert call_count["extend"] == 2
