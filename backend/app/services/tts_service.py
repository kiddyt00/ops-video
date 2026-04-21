"""
TTS (Text-to-Speech) Service using edge-tts

Generates speech audio from text input, suitable for manga video narration.
"""
import asyncio
import edge_tts
from pathlib import Path
from typing import Optional
from uuid import UUID

from ..config import settings, STORAGE_DIRS


class TTSService:
    """
    TTS service using edge-tts (Microsoft Edge online TTS, free, no API key).

    Supported voices: any edge-tts voice (e.g. zh-CN-XiaoxiaoNeural, ja-JP-NanamiNeural).
    """

    DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"
    DEFAULT_RATE = "+0%"
    DEFAULT_VOLUME = "+0%"

    AUDIO_DIR = STORAGE_DIRS["audio"]

    async def synthesize(
        self,
        text: str,
        voice: str = DEFAULT_VOICE,
        rate: str = DEFAULT_RATE,
        volume: str = DEFAULT_VOLUME,
        output_filename: Optional[str] = None,
    ) -> Path:
        """
        Synthesize speech from text and save to audio file.

        Args:
            text: Text to synthesize
            voice: Edge TTS voice name
            rate: Speech rate (e.g. "+10%", "-20%")
            volume: Volume adjustment (e.g. "+10%")
            output_filename: Optional output filename (auto-generated if None)

        Returns:
            Path to the generated audio file
        """
        if not text.strip():
            raise ValueError("Text cannot be empty")

        if output_filename is None:
            import hashlib
            import time
            h = hashlib.md5(text[:50].encode()).hexdigest()[:8]
            output_filename = f"tts_{h}_{int(time.time())}.mp3"

        output_path = self.AUDIO_DIR / output_filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)
        await communicate.save(str(output_path))

        return output_path

    async def synthesize_panels(
        self,
        panels: list[dict],
        voice: str = DEFAULT_VOICE,
        output_dir: Optional[Path] = None,
    ) -> list[Path]:
        """
        Synthesize speech for multiple storyboard panels (sequential narration).

        Args:
            panels: List of dicts with 'text' and optional 'index' keys
            voice: Edge TTS voice
            output_dir: Output directory for audio files

        Returns:
            List of paths to generated audio files, in panel order
        """
        if output_dir is None:
            output_dir = self.AUDIO_DIR / "panels"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Sort panels by index
        sorted_panels = sorted(panels, key=lambda p: p.get("index", 0))

        audio_paths = []
        for i, panel in enumerate(sorted_panels):
            text = panel.get("text", panel.get("dialogue", ""))
            if not text:
                continue
            filename = f"panel_{i:03d}.mp3"
            path = await self.synthesize(text, voice=voice, output_filename=filename)
            audio_paths.append(path)

        return audio_paths

    async def list_voices(self, language: Optional[str] = None) -> list[dict]:
        """List available TTS voices, optionally filtered by language code."""
        voices = await edge_tts.list_voices()
        if language:
            voices = [v for v in voices if v["Locale"].startswith(language)]
        return voices


tts_service = TTSService()
