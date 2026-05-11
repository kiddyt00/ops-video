"""
Wan2.7 i2v (Image-to-Video) Provider

Uses DashScope video-generation API to animate still images.
"""
import asyncio
import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import httpx

from ..config import settings, STORAGE_DIRS
from ..db.session import SessionLocal
from ..db.storage_provider_crud import storage_provider_crud
from ..core.oss_service import OSSService
from .base_provider import BaseProvider, GenerationResult

logger = logging.getLogger(__name__)


class WanVideoProvider(BaseProvider):
    """Wan2.7 i2v provider — animates images into short video clips."""

    BASE_URL = "https://dashscope.aliyuncs.com/api/v1"

    def __init__(self, api_key: str = "", model: str = "wan2.7-i2v"):
        self.api_key = api_key or settings.DASHSCOPE_API_KEY
        self.model = model

    @property
    def name(self) -> str:
        return "DashScope-WanVideo"

    @property
    def description(self) -> str:
        return "通义万相 Wan2.7 图生视频 — 将静态图片转为动态视频"

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        return "image_url" in parameters

    async def generate(self, parameters: Dict[str, Any]) -> GenerationResult:
        """Generate video from image + prompt via DashScope async API.
        
        Supports both image_url (public URL) and image_path (local file → base64).
        """
        image_url = parameters.get("image_url", "")
        image_path = parameters.get("image_path", "")
        prompt = parameters.get("prompt", "让画面动起来")
        size = parameters.get("size", "768*768")
        output_dir = parameters.get("output_dir", "video")
        output_filename = parameters.get("output_filename")

        # Build image reference
        if image_path:
            import base64 as b64
            p = Path(image_path)
            mime = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg'}.get(p.suffix.lower(), 'image/png')
            data = b64.b64encode(p.read_bytes()).decode()
            image_ref = f"data:{mime};base64,{data}"
        elif image_url:
            image_ref = image_url
        else:
            return GenerationResult(file_paths=[], parameters=parameters, success=False, error_message="No image_url or image_path")

        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                # Step 1: Submit task
                payload = {
                    "model": self.model,
                    "input": {
                        "prompt": prompt,
                        "media": [
                            {"type": "first_frame", "url": image_ref},
                        ]
                    },
                    "parameters": {
                        "resolution": "720P",
                        "duration": parameters.get("duration", 5),
                        "prompt_extend": True,
                        "watermark": False,
                    },
                }

                resp = await client.post(
                    f"{self.BASE_URL}/services/aigc/video-generation/video-synthesis",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "X-DashScope-Async": "enable",
                    },
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                task_id = data["output"]["task_id"]

                # Step 2: Poll for completion
                result_data = await self._wait_for_task(task_id, client)

                # Step 3: Download video
                video_url = result_data["output"]["video_url"]
                video_path = await self._download_video(
                    video_url, output_dir, output_filename, client
                )

                oss_urls = await self._try_upload_to_oss([video_path])

                return GenerationResult(
                    file_paths=[video_path],
                    parameters=parameters,
                    metadata={"model": self.model, "task_id": task_id},
                    oss_urls=oss_urls,
                )

        except Exception as e:
            return GenerationResult(
                file_paths=[],
                parameters=parameters,
                success=False,
                error_message=str(e),
            )

    async def generate_batch(
        self,
        image_paths: List[Path],
        panel_prompts: List[str],
        output_dir: str = "video",
    ) -> GenerationResult:
        """Generate videos for multiple images in parallel."""
        import asyncio

        async def generate_one(i: int, img_path: Path, prompt: str) -> Optional[Path]:
            # Upload image to get a URL, or use local path via temp server
            # For now, use the image URL directly (assuming images are accessible)
            # DashScope needs a publicly accessible URL
            # We'll upload via multipart/form-data first if needed
            result = await self.generate({
                "image_url": str(img_path),
                "prompt": prompt,
                "output_dir": output_dir,
                "output_filename": f"wan_i2v_{i:03d}.mp4",
            })
            return result.file_paths[0] if result.success and result.file_paths else None

        tasks = [
            generate_one(i, img_path, prompt)
            for i, (img_path, prompt) in enumerate(zip(image_paths, panel_prompts))
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        paths = [r for r in results if isinstance(r, Path) and r.exists()]
        return GenerationResult(
            file_paths=paths,
            parameters={"image_count": len(image_paths), "generated": len(paths)},
            metadata={"model": self.model},
        )

    async def extend(
        self,
        prev_clip_path: Path,
        prompt: str,
        duration: int = 5,
        output_filename: str = "",
    ) -> GenerationResult:
        """Generate a continuation video clip using the last frame of a previous clip.

        Uses DashScope i2v API with the tail frame of prev_clip_path as reference.

        Args:
            prev_clip_path: Path to the previous video clip.
            prompt: Prompt for the continuation.
            duration: Duration in seconds.
            output_filename: Output filename (auto-generated if empty).

        Returns:
            GenerationResult with the generated clip path.
        """
        # Extract last frame from previous clip
        last_frame_path = await self.extract_last_frame(prev_clip_path)
        if not last_frame_path or not last_frame_path.exists():
            return GenerationResult(
                file_paths=[],
                parameters={
                    "prev_clip_path": str(prev_clip_path),
                    "prompt": prompt,
                },
                success=False,
                error_message="Failed to extract last frame from previous clip",
            )

        try:
            # Reuse generate() with the extracted last frame as image_path
            params: Dict[str, Any] = {
                "image_path": str(last_frame_path),
                "prompt": prompt,
                "duration": duration,
                "output_dir": "video",
            }
            if output_filename:
                params["output_filename"] = output_filename

            result = await self.generate(params)
            return result
        except Exception as e:
            return GenerationResult(
                file_paths=[],
                parameters={
                    "prev_clip_path": str(prev_clip_path),
                    "prompt": prompt,
                },
                success=False,
                error_message=str(e),
            )

    async def extract_last_frame(self, clip_path: Path) -> Optional[Path]:
        """Extract the last frame of a video clip as a PNG image.

        Uses FFmpeg to seek to the last frame and save as last_frame.png.
        Temp files use home directory (snap FFmpeg confinement).

        Args:
            clip_path: Path to the source video clip.

        Returns:
            Path to the extracted last_frame.png, or None on failure.
        """
        if not clip_path or not clip_path.exists():
            logger.warning("extract_last_frame: clip not found: %s", clip_path)
            return None

        home = os.path.expanduser("~")
        output_dir = Path(home) / "tail_frame_tmp"
        output_dir.mkdir(parents=True, exist_ok=True)

        frame_path = output_dir / "last_frame.png"

        # FFmpeg command: seek to near the end, extract 1 frame
        # -sseof -1 seeks to 1 second before the end, -update 1 overwrites
        cmd = [
            "ffmpeg", "-y",
            "-sseof", "-1",
            "-i", str(clip_path),
            "-update", "1",
            "-frames:v", "1",
            "-q:v", "1",
            str(frame_path),
        ]
        env = os.environ.copy()
        env["LIBGL_ALWAYS_SOFTWARE"] = "1"
        env.pop("DISPLAY", None)
        env["TMPDIR"] = home
        env["TEMP"] = home
        env["TMP"] = home

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=30)
            if result.returncode != 0:
                logger.warning("FFmpeg extract_last_frame failed: %s", result.stderr[:300])
                return None
            if not frame_path.exists():
                logger.warning("FFmpeg did not produce output file")
                return None
            logger.info("Extracted last frame: %s (%d bytes)", frame_path, frame_path.stat().st_size)
            return frame_path
        except subprocess.TimeoutExpired:
            logger.warning("FFmpeg extract_last_frame timed out")
            return None
        except Exception as e:
            logger.warning("extract_last_frame error: %s", e)
            return None

    # ─── Helpers ──────────────────────────────────────────────────

    async def _try_upload_to_oss(self, paths: List[Path]) -> List[str]:
        """Try uploading generated files to active OSS storage.

        Non-blocking: on any error, logs a warning and returns [].
        """
        if not paths:
            return []
        try:
            db = SessionLocal()
            try:
                provider = storage_provider_crud.get_active(db)
                if not provider:
                    return []
                oss = OSSService(provider)
                urls = []
                for p in paths:
                    try:
                        url = oss.upload(str(p))
                        urls.append(url)
                        logger.info("WanVideoProvider uploaded %s -> %s", p, url)
                    except Exception as e:
                        logger.warning("WanVideoProvider OSS upload failed for %s: %s", p, e)
                return urls
            finally:
                db.close()
        except Exception as e:
            logger.warning("WanVideoProvider OSS upload check failed: %s", e)
            return []

    async def _wait_for_task(self, task_id: str, client: httpx.AsyncClient, timeout: int = 300) -> Dict[str, Any]:
        """Poll task status until SUCCEEDED or FAILED."""
        start = time.time()
        while time.time() - start < timeout:
            resp = await client.get(
                f"{self.BASE_URL}/tasks/{task_id}",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            resp.raise_for_status()
            data = resp.json()
            status = data["output"]["task_status"]

            if status == "SUCCEEDED":
                return data
            if status == "FAILED":
                raise RuntimeError(f"Task failed: {data['output'].get('message', 'unknown')}")

            await asyncio.sleep(3)

        raise TimeoutError(f"Task {task_id} timed out after {timeout}s")

    async def _download_video(
        self,
        url: str,
        output_dir: str,
        filename: Optional[str],
        client: httpx.AsyncClient,
    ) -> Path:
        """Download generated video from signed URL."""
        storage = STORAGE_DIRS["video"]
        storage.mkdir(parents=True, exist_ok=True)

        if not filename:
            filename = f"wan_i2v_{int(time.time() * 1000)}.mp4"

        video_path = storage / filename

        resp = await client.get(url)
        resp.raise_for_status()
        video_path.write_bytes(resp.content)

        return video_path


wan_video_provider = WanVideoProvider()
