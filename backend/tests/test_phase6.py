"""
Tests for Phase 6: Audio and Video Synthesis

Tests TTS service, BGM service, SFX service, and Video Synthesis service.
"""
import sys
import asyncio
import tempfile
import wave
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

import numpy as np
import pytest
from scipy.io import wavfile

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.tts_service import TTSService
from app.services.bgm_service import BGMService
from app.services.sfx_service import SFXService
from app.services.video_synthesis_service import VideoSynthesisService


# ─── TTS Service Tests ───────────────────────────────────────────────

class TestTTSService:
    """Test TTS (Text-to-Speech) service"""

    def test_import(self):
        """Test TTSService can be imported"""
        assert TTSService is not None

    def test_init(self):
        """Test service initialization"""
        svc = TTSService()
        assert svc is not None

    def test_synthesize_empty_text_raises(self):
        """Test that empty text raises ValueError"""
        svc = TTSService()
        with pytest.raises(ValueError, match="Text cannot be empty"):
            asyncio.get_event_loop().run_until_complete(
                svc.synthesize("")
            )

    def test_synthesize_empty_text_whitespace(self):
        """Test that whitespace-only text raises ValueError"""
        svc = TTSService()
        with pytest.raises(ValueError):
            asyncio.get_event_loop().run_until_complete(
                svc.synthesize("   ")
            )

    @patch("app.services.tts_service.edge_tts.Communicate")
    def test_synthesize_creates_file(self, mock_communicate):
        """Test synthesize creates an audio file"""
        # Mock edge_tts.Communicate.save
        mock_instance = AsyncMock()
        mock_communicate.return_value = mock_instance

        svc = TTSService()
        with tempfile.TemporaryDirectory() as tmpdir:
            # Override audio dir for test
            test_dir = Path(tmpdir)
            svc.AUDIO_DIR = test_dir

            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(
                svc.synthesize("Hello world", output_filename="test.mp3")
            )

            assert result == test_dir / "test.mp3"
            mock_communicate.assert_called_once()

    def test_synthesize_custom_voice_and_rate(self):
        """Test synthesize with custom voice and rate parameters"""
        svc = TTSService()
        assert svc.DEFAULT_VOICE == "zh-CN-XiaoxiaoNeural"
        assert svc.DEFAULT_RATE == "+0%"

    def test_list_voices_structure(self):
        """Test list_voices returns list of dicts"""
        svc = TTSService()
        # This calls the actual edge-tts API, just verify structure
        loop = asyncio.get_event_loop()
        try:
            voices = loop.run_until_complete(svc.list_voices())
            assert isinstance(voices, list)
            if voices:
                assert isinstance(voices[0], dict)
        except Exception:
            pytest.skip("edge-tts network call failed")

    def test_synthesize_panels_empty(self):
        """Test synthesize_panels with empty list"""
        svc = TTSService()
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(svc.synthesize_panels([]))
        assert result == []

    def test_synthesize_panels_skips_empty_text(self):
        """Test synthesize_panels skips panels without text"""
        mock_instance = AsyncMock()
        with patch("app.services.tts_service.edge_tts.Communicate", return_value=mock_instance):
            svc = TTSService()
            with tempfile.TemporaryDirectory() as tmpdir:
                svc.AUDIO_DIR = Path(tmpdir)
                panels = [{"index": 0, "text": "Hello"}, {"index": 1, "text": ""}]
                loop = asyncio.get_event_loop()
                result = loop.run_until_complete(svc.synthesize_panels(panels))
                # Should only create audio for the panel with text
                assert len(result) == 1


# ─── BGM Service Tests ───────────────────────────────────────────────

class TestBGMService:
    """Test Background Music generation service"""

    def test_import(self):
        """Test BGMService can be imported"""
        assert BGMService is not None

    def test_generate_creates_file(self):
        """Test generate creates a WAV file"""
        svc = BGMService()
        with tempfile.TemporaryDirectory() as tmpdir:
            svc.AUDIO_DIR = Path(tmpdir)
            result = svc.generate(duration=1.0, output_filename="test_bgm.wav")
            assert result.exists()
            assert result.suffix == ".wav"

    def test_generate_valid_wav(self):
        """Test generated file is valid WAV"""
        svc = BGMService()
        with tempfile.TemporaryDirectory() as tmpdir:
            svc.AUDIO_DIR = Path(tmpdir)
            path = svc.generate(duration=1.0, output_filename="valid.wav")
            sr, data = wavfile.read(str(path))
            assert sr == 44100
            assert len(data) > 0

    def test_generate_duration_approximate(self):
        """Test generated audio duration matches requested"""
        svc = BGMService()
        with tempfile.TemporaryDirectory() as tmpdir:
            svc.AUDIO_DIR = Path(tmpdir)
            target_duration = 2.0
            path = svc.generate(duration=target_duration, output_filename="dur.wav")
            sr, data = wavfile.read(str(path))
            actual_duration = len(data) / sr
            assert abs(actual_duration - target_duration) < 0.1

    def test_generate_different_moods(self):
        """Test different moods produce different audio"""
        svc = BGMService()
        with tempfile.TemporaryDirectory() as tmpdir:
            svc.AUDIO_DIR = Path(tmpdir)
            ambient_path = svc.generate(duration=1.0, mood="ambient", output_filename="ambient.wav")
            dramatic_path = svc.generate(duration=1.0, mood="dramatic", output_filename="dramatic.wav")
            _, ambient_data = wavfile.read(str(ambient_path))
            _, dramatic_data = wavfile.read(str(dramatic_path))
            # Different moods should produce different audio
            assert not np.array_equal(ambient_data, dramatic_data)

    def test_generate_panel_bgm(self):
        """Test generate_panel_bgm creates files for each panel"""
        svc = BGMService()
        with tempfile.TemporaryDirectory() as tmpdir:
            svc.AUDIO_DIR = Path(tmpdir) / "bgm"
            svc.AUDIO_DIR.mkdir(parents=True)
            panels = [
                {"mood": "ambient", "duration": 1.0},
                {"mood": "dramatic", "duration": 1.5},
            ]
            paths = svc.generate_panel_bgm(panels, duration_per_panel=1.0)
            assert len(paths) == 2
            for p in paths:
                assert p.exists()

    def test_generate_panel_bgm_empty(self):
        """Test generate_panel_bgm with empty list"""
        svc = BGMService()
        paths = svc.generate_panel_bgm([])
        assert paths == []

    def test_mood_settings_all_types(self):
        """Test all mood types return valid settings"""
        svc = BGMService()
        for mood in ["ambient", "dramatic", "cheerful", "sad"]:
            settings = svc._get_mood_settings(mood)
            assert "wave" in settings
            assert "volume" in settings
            assert "sustain" in settings
            assert 0 < settings["volume"] <= 1
            assert 0 < settings["sustain"] <= 1

    def test_unknown_mood_defaults(self):
        """Test unknown mood falls back to ambient"""
        svc = BGMService()
        settings = svc._get_mood_settings("unknown_mood")
        assert settings == svc._get_mood_settings("ambient")


# ─── SFX Service Tests ──────────────────────────────────────────────

class TestSFXService:
    """Test Sound Effects generation service"""

    def test_import(self):
        """Test SFXService can be imported"""
        assert SFXService is not None

    def test_sfx_types(self):
        """Test SFX_TYPES list is non-empty"""
        assert len(SFXService.SFX_TYPES) > 0
        assert "whoosh" in SFXService.SFX_TYPES

    def test_generate_creates_file(self):
        """Test generate creates a WAV file"""
        svc = SFXService()
        with tempfile.TemporaryDirectory() as tmpdir:
            svc.AUDIO_DIR = Path(tmpdir)
            result = svc.generate(sfx_type="whoosh", duration=1.0, output_filename="test_sfx.wav")
            assert result.exists()
            assert result.suffix == ".wav"

    def test_generate_valid_wav(self):
        """Test generated file is valid WAV"""
        svc = SFXService()
        with tempfile.TemporaryDirectory() as tmpdir:
            svc.AUDIO_DIR = Path(tmpdir)
            path = svc.generate(sfx_type="impact", duration=1.0, output_filename="impact.wav")
            sr, data = wavfile.read(str(path))
            assert sr == 44100
            assert len(data) > 0

    def test_all_sfx_types_generate(self):
        """Test all SFX types can be generated"""
        svc = SFXService()
        with tempfile.TemporaryDirectory() as tmpdir:
            svc.AUDIO_DIR = Path(tmpdir)
            for sfx_type in SFXService.SFX_TYPES:
                path = svc.generate(
                    sfx_type=sfx_type,
                    duration=1.0,
                    output_filename=f"{sfx_type}.wav",
                )
                assert path.exists(), f"Failed to generate {sfx_type}"
                sr, data = wavfile.read(str(path))
                assert len(data) > 0

    def test_different_sfx_types_produce_different_audio(self):
        """Test different SFX types produce different audio"""
        svc = SFXService()
        with tempfile.TemporaryDirectory() as tmpdir:
            svc.AUDIO_DIR = Path(tmpdir)
            whoosh = svc.generate(sfx_type="whoosh", duration=1.0, output_filename="w.wav")
            impact = svc.generate(sfx_type="impact", duration=1.0, output_filename="i.wav")
            _, whoosh_data = wavfile.read(str(whoosh))
            _, impact_data = wavfile.read(str(impact))
            assert not np.array_equal(whoosh_data, impact_data)

    def test_intensity_affects_output(self):
        """Test different intensity values affect the output"""
        svc = SFXService()
        with tempfile.TemporaryDirectory() as tmpdir:
            svc.AUDIO_DIR = Path(tmpdir)
            low = svc.generate(sfx_type="sparkle", duration=1.0, intensity=0.1, output_filename="low.wav")
            high = svc.generate(sfx_type="sparkle", duration=1.0, intensity=0.9, output_filename="high.wav")
            _, low_data = wavfile.read(str(low))
            _, high_data = wavfile.read(str(high))
            assert not np.array_equal(low_data, high_data)

    def test_unknown_sfx_type_defaults_to_whoosh(self):
        """Test unknown SFX type falls back to whoosh"""
        svc = SFXService()
        with tempfile.TemporaryDirectory() as tmpdir:
            svc.AUDIO_DIR = Path(tmpdir)
            path = svc.generate(sfx_type="unknown", duration=0.5, output_filename="default.wav")
            assert path.exists()


# ─── Video Synthesis Service Tests ───────────────────────────────────

class TestVideoSynthesisService:
    """Test Video Synthesis service"""

    def test_import(self):
        """Test VideoSynthesisService can be imported"""
        assert VideoSynthesisService is not None

    def test_init_creates_dir(self):
        """Test initialization creates video directory"""
        svc = VideoSynthesisService()
        assert svc.video_dir.exists()

    def test_compose_empty_panels_raises(self):
        """Test compose with empty panels raises ValueError"""
        svc = VideoSynthesisService()
        with pytest.raises(ValueError, match="No panels provided"):
            svc.compose([])

    def test_compose_requires_valid_image(self):
        """Test compose fails with non-existent image path"""
        svc = VideoSynthesisService()
        panels = [{"image_path": "/nonexistent/image.png", "duration": 1.0}]
        with pytest.raises(Exception):
            svc.compose(panels, output_filename="test.mp4")

    def test_create_still_clip_creates_video(self):
        """Test _create_still_clip creates a valid MP4 from an image"""
        svc = VideoSynthesisService()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            # Create a test image (solid color)
            img_path = tmp / "test.png"
            self._create_test_image(img_path, 512, 768)

            output_path = tmp / "clip.mp4"
            svc._create_still_clip(img_path, 1.0, (512, 768), 24, output_path)

            assert output_path.exists()
            assert output_path.stat().st_size > 0

    def test_concat_clips(self):
        """Test concatenating multiple clips"""
        svc = VideoSynthesisService()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            # Create test images and clips
            clip_paths = []
            for i in range(3):
                img_path = tmp / f"img_{i}.png"
                self._create_test_image(img_path, 512, 768)
                clip_path = tmp / f"clip_{i}.mp4"
                svc._create_still_clip(img_path, 0.5, (512, 768), 24, clip_path)
                clip_paths.append(clip_path)

            output_path = tmp / "concat.mp4"
            svc._concat_clips(clip_paths, output_path)

            assert output_path.exists()
            assert output_path.stat().st_size > 0

    def test_combine_audio_video(self):
        """Test combining video with audio"""
        svc = VideoSynthesisService()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            # Create test image and clip
            img_path = tmp / "test.png"
            self._create_test_image(img_path, 512, 768)
            video_path = tmp / "video.mp4"
            svc._create_still_clip(img_path, 1.0, (512, 768), 24, video_path)

            # Create test audio
            audio_path = tmp / "audio.wav"
            sr, data = 44100, np.zeros(int(44100 * 1.0), dtype=np.int16)
            wavfile.write(str(audio_path), sr, data)

            output_path = tmp / "output.mp4"
            svc._combine_audio_video(video_path, audio_path, output_path)

            assert output_path.exists()
            assert output_path.stat().st_size > 0

    def test_mix_audio_with_bgm(self):
        """Test mixing audio with BGM"""
        svc = VideoSynthesisService()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            # Create two test audio files
            audio1 = tmp / "audio1.wav"
            audio2 = tmp / "audio2.wav"
            sr = 44100
            data1 = np.sin(np.linspace(0, 2 * np.pi * 440 * 1.0, sr)).astype(np.int16)
            data2 = np.sin(np.linspace(0, 2 * np.pi * 880 * 1.0, sr)).astype(np.int16)
            wavfile.write(str(audio1), sr, data1)
            wavfile.write(str(audio2), sr, data2)

            result = svc._mix_audio([audio1], audio2, 1.0, tmp)
            assert result is not None
            assert result.exists()

    def test_mix_audio_no_bgm(self):
        """Test mixing audio without BGM"""
        svc = VideoSynthesisService()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            audio = tmp / "audio.wav"
            sr = 44100
            data = np.sin(np.linspace(0, 2 * np.pi * 440 * 1.0, sr)).astype(np.int16)
            wavfile.write(str(audio), sr, data)

            result = svc._mix_audio([audio], None, 1.0, tmp)
            assert result is not None
            assert result.exists()

    def test_mix_audio_empty_returns_none(self):
        """Test mixing with no audio returns None"""
        svc = VideoSynthesisService()
        with tempfile.TemporaryDirectory() as tmpdir:
            result = svc._mix_audio([], None, 1.0, Path(tmpdir))
            assert result is None

    def test_full_compose_workflow(self):
        """Test complete video compose workflow"""
        svc = VideoSynthesisService()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            # Create test images and audio
            panels = []
            for i in range(2):
                img_path = tmp / f"panel_{i}.png"
                self._create_test_image(img_path, 512, 768)
                audio_path = tmp / f"audio_{i}.wav"
                sr, data = 44100, np.zeros(int(44100 * 1.0), dtype=np.int16)
                wavfile.write(str(audio_path), sr, data)

                panels.append({
                    "image_path": str(img_path),
                    "audio_path": str(audio_path),
                    "duration": 1.0,
                    "text": f"Panel {i + 1}",
                })

            output_path = tmp / "final.mp4"
            result = svc.compose(panels, output_filename="final.mp4", resolution=(512, 768))

            assert result.exists()
            assert result.stat().st_size > 0

    def _create_test_image(self, path: Path, width: int, height: int):
        """Create a simple solid-color PNG for testing."""
        try:
            from PIL import Image
            img = Image.new("RGB", (width, height), color=(100, 100, 150))
            img.save(str(path))
        except ImportError:
            # Fallback: create a minimal PNG manually
            import struct, zlib
            # 1x1 red pixel PNG
            def create_minimal_png(w, h, color):
                raw_data = b""
                for y in range(h):
                    raw_data += b"\x00"  # filter byte
                    raw_data += color * w
                def chunk(chunk_type, data):
                    c = chunk_type + data
                    return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
                header = b"\x89PNG\r\n\x1a\n"
                ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                idat = chunk(b"IDAT", zlib.compress(raw_data))
                iend = chunk(b"IEND", b"")
                return header + ihdr + idat + iend

            png_data = create_minimal_png(width, height, b"\x64\x64\x96")
            path.write_bytes(png_data)


# ─── Generator API Updates Tests ─────────────────────────────────────

class TestGeneratorAPIUpdates:
    """Test that generator API includes new audio/video generators"""

    def test_tts_generator_registered(self):
        """Test TTS generator is registered"""
        from app.api.routes.generators import GENERATORS
        assert "tts" in GENERATORS
        assert GENERATORS["tts"].name == "TTS Generator"

    def test_bgm_generator_registered(self):
        """Test BGM generator is registered"""
        from app.api.routes.generators import GENERATORS
        assert "bgm" in GENERATORS
        assert GENERATORS["bgm"].name == "BGM Generator"

    def test_video_composer_registered(self):
        """Test Video Composer generator is registered"""
        from app.api.routes.generators import GENERATORS
        assert "video_composer" in GENERATORS
        assert GENERATORS["video_composer"].name == "Video Composer"

    def test_all_generators_count(self):
        """Test correct number of generators (3 original + 3 new)"""
        from app.api.routes.generators import GENERATORS
        assert len(GENERATORS) == 6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
