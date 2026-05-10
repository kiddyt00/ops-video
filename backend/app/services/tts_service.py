"""
TTS (Text-to-Speech) Service

Primary: DashScope Qwen3-TTS (via multimodal-generation)
Fallback: edge-tts (Microsoft Edge, free)
"""
import asyncio
import httpx
import hashlib
import time
from pathlib import Path
from typing import Optional

from ..config import settings, STORAGE_DIRS


class TTSService:
    DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"
    AUDIO_DIR = STORAGE_DIRS["audio"]

    async def synthesize(
        self,
        text: str,
        voice: str = "",
        rate: str = "+0%",
        volume: str = "+0%",
        output_filename: Optional[str] = None,
    ) -> Path:
        if not text.strip():
            raise ValueError("Text cannot be empty")

        if output_filename is None:
            h = hashlib.md5(text[:50].encode()).hexdigest()[:8]
            output_filename = f"tts_{h}_{int(time.time())}.mp3"

        output_path = self.AUDIO_DIR / output_filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Try DashScope Qwen3-TTS first (faster, better quality)
        api_key = settings.DASHSCOPE_API_KEY
        if api_key:
            try:
                await self._dashscope_tts(text, output_path, api_key)
                return output_path
            except Exception:
                pass  # fall through to edge-tts

        # Fallback: edge-tts
        try:
            import edge_tts
            communicate = edge_tts.Communicate(text, voice or self.DEFAULT_VOICE, rate=rate, volume=volume)
            await communicate.save(str(output_path))
        except Exception:
            # Last resort: write a silent audio placeholder so the pipeline doesn't break
            output_path.write_bytes(b"")

        return output_path

    async def _dashscope_tts(self, text: str, output_path: Path, api_key: str) -> None:
        """Generate TTS via DashScope multimodal-generation (Qwen3-TTS)."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "qwen3-tts-flash",
                    "input": {"text": text},
                    "parameters": {"voice": "Cherry", "language_type": "Chinese"},
                },
            )
            resp.raise_for_status()
            data = resp.json()

            # Extract audio URL
            audio_url = data.get("output", {}).get("audio", {}).get("url")
            if not audio_url:
                raise RuntimeError(f"No audio URL in response: {str(data)[:300]}")

            # Download audio
            audio_resp = await client.get(audio_url)
            audio_resp.raise_for_status()
            output_path.write_bytes(audio_resp.content)

    async def synthesize_panels(
        self,
        panels: list[dict],
        voice: str = "",
        output_dir: Optional[Path] = None,
    ) -> list[Path]:
        if output_dir is None:
            output_dir = self.AUDIO_DIR / "panels"
        output_dir.mkdir(parents=True, exist_ok=True)

        sorted_panels = sorted(panels, key=lambda p: p.get("index", 0))
        audio_paths = []
        for i, panel in enumerate(sorted_panels):
            text = panel.get("text", panel.get("dialogue", ""))
            if not text:
                continue
            filename = f"panel_{i:03d}.mp3"
            path = await self.synthesize(text, voice=voice or self.DEFAULT_VOICE, output_filename=filename)
            audio_paths.append(path)

        return audio_paths

    async def list_voices(self, language: Optional[str] = None) -> list[dict]:
        try:
            import edge_tts
            voices = await edge_tts.list_voices()
            if language:
                voices = [v for v in voices if v["Locale"].startswith(language)]
            return voices
        except Exception:
            return []


tts_service = TTSService()
