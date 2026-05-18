"""
Local GPU Provider — calls on-premise GPU service (gpu_service.py) for
image generation (SDXL) and video generation (CogVideoX).

The GPU service runs on a separate machine (e.g. 192.168.24.226:8199)
and uses diffusers with a local 4090 GPU. No ComfyUI dependency.
"""
import asyncio
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import httpx

from ..config import settings, STORAGE_DIRS
from .base_provider import BaseProvider, GenerationResult

logger = logging.getLogger(__name__)

GPU_SERVICE_URL = getattr(settings, "GPU_SERVICE_URL", "http://192.168.24.226:8199")


class LocalGPUProvider(BaseProvider):
    """Provider that delegates to the on-premise GPU service (diffusers)."""

    def __init__(self, model: str = "sdxl"):
        self.model = model.lower()
        self.service_url = GPU_SERVICE_URL.rstrip("/")

    @property
    def name(self) -> str:
        return f"LocalGPU-{self.model}"

    @property
    def description(self) -> str:
        return "本地 GPU 服务 (SDXL / CogVideoX)"

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        return "prompt" in parameters

    async def generate(self, parameters: Dict[str, Any]) -> GenerationResult:
        if self.model == "cogvideox" or self._is_video_request(parameters):
            return await self._generate_video(parameters)
        return await self._generate_image(parameters)

    async def _generate_image(self, parameters: Dict[str, Any]) -> GenerationResult:
        prompt = parameters.get("prompt", "")
        negative_prompt = parameters.get("negative_prompt", "")
        width = parameters.get("width", 1024)
        height = parameters.get("height", 1024)
        steps = parameters.get("steps", 25)
        cfg_scale = parameters.get("cfg_scale", 7.0)
        seed = parameters.get("seed", -1)
        n = int(parameters.get("n", 1))
        output_dir = parameters.get("output_dir", "images")

        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                resp = await client.post(
                    f"{self.service_url}/generate/image",
                    json={
                        "prompt": prompt,
                        "negative_prompt": negative_prompt,
                        "width": width,
                        "height": height,
                        "steps": steps,
                        "cfg_scale": cfg_scale,
                        "seed": seed,
                    },
                )
                resp.raise_for_status()

                storage_dir = STORAGE_DIRS.get(output_dir, STORAGE_DIRS["images"])
                storage_dir.mkdir(parents=True, exist_ok=True)

                paths = []
                ts = int(time.time())
                for i in range(n):
                    filename = f"localgpu_{ts}_{i:03d}.png"
                    img_path = storage_dir / filename
                    img_path.write_bytes(resp.content)
                    paths.append(img_path)

                return GenerationResult(
                    file_paths=paths,
                    parameters=parameters,
                    metadata={"model": self.model, "seed": seed, "image_count": len(paths)},
                )

        except Exception as e:
            logger.error("LocalGPU image gen failed: %s", e)
            return GenerationResult(
                file_paths=[], parameters=parameters,
                success=False, error_message=str(e),
            )

    async def _generate_video(self, parameters: Dict[str, Any]) -> GenerationResult:
        image_path = parameters.get("image_path", "")
        image_url = parameters.get("image_url", "")
        prompt = parameters.get("prompt", "让画面动起来")
        steps = parameters.get("steps", 50)
        seed = parameters.get("seed", -1)
        output_dir = parameters.get("output_dir", "video")

        try:
            async with httpx.AsyncClient(timeout=600.0) as client:
                resp = await client.post(
                    f"{self.service_url}/generate/video",
                    json={
                        "image_path": image_path,
                        "image_url": image_url,
                        "prompt": prompt,
                        "steps": steps,
                        "seed": seed,
                    },
                )
                resp.raise_for_status()

                storage_dir = STORAGE_DIRS.get(output_dir, STORAGE_DIRS["video"])
                storage_dir.mkdir(parents=True, exist_ok=True)
                ts = int(time.time())
                ct = resp.headers.get("content-type", "")

                if "video" in ct or "mp4" in ct:
                    fp = storage_dir / f"localgpu_video_{ts}.mp4"
                    fp.write_bytes(resp.content)
                    return GenerationResult(
                        file_paths=[fp], parameters=parameters,
                        metadata={"model": self.model, "format": "mp4"},
                    )
                else:
                    fp = storage_dir / f"localgpu_video_{ts}.png"
                    fp.write_bytes(resp.content)
                    return GenerationResult(
                        file_paths=[fp], parameters=parameters,
                        metadata={"model": self.model, "format": "still"},
                    )

        except Exception as e:
            logger.error("LocalGPU video gen failed: %s", e)
            return GenerationResult(
                file_paths=[], parameters=parameters,
                success=False, error_message=str(e),
            )

    @staticmethod
    def _is_video_request(parameters: Dict[str, Any]) -> bool:
        return bool(parameters.get("image_path") or parameters.get("image_url"))


local_gpu_provider = LocalGPUProvider()
