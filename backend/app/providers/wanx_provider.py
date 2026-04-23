"""
DashScope (通义万相) Provider for image generation
Supports wanx-v1/v2 for text-to-image and image-to-image
"""
import asyncio
import base64
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import httpx

from ..config import settings, STORAGE_DIRS
from .base_provider import BaseProvider, GenerationResult


class WanxProvider(BaseProvider):
    """DashScope Wanx (通义万相) provider for manga-style image generation."""

    BASE_URL = "https://dashscope.aliyuncs.com/api/v1"

    MODEL_MAPPING = {
        "wanx-v1": "wanx-v1",
        "wanx-v2": "wanx-v2",
        "wanx2.1-t2i-turbo": "wanx2.1-t2i-turbo",
        "wanx2.1-t2i-plus": "wanx2.1-t2i-plus",
    }

    def __init__(
        self,
        api_key: str = "",
        model: str = "",
    ):
        self.api_key = api_key or settings.DASHSCOPE_API_KEY
        self.model = self.MODEL_MAPPING.get(model or settings.DASHSCOPE_MODEL, "wanx-v1")

    @property
    def name(self) -> str:
        return "DashScope-Wanx"

    @property
    def description(self) -> str:
        return "通义万相 - 阿里达摩院文生图模型"

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate Wanx parameters."""
        return "prompt" in parameters

    async def generate(self, parameters: Dict[str, Any]) -> GenerationResult:
        """Generate image using DashScope Wanx API."""
        prompt = parameters.get("prompt", "")
        negative_prompt = parameters.get("negative_prompt", "")
        size = parameters.get("size", "1024*1024")
        seed = parameters.get("seed", -1)
        steps = parameters.get("steps", 30)
        width = parameters.get("width", 1024)
        height = parameters.get("height", 1024)
        reference_image = parameters.get("reference_image")  # For image-to-image
        output_dir = parameters.get("output_dir", "images")

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": self.model,
                "input": {
                    "prompt": prompt,
                },
                "parameters": {
                    "size": size,
                    "steps": steps,
                },
            }

            if negative_prompt:
                payload["input"]["negative_prompt"] = negative_prompt
            if seed != -1:
                payload["parameters"]["seed"] = seed

            # Image-to-image: include reference image
            if reference_image:
                payload["input"]["reference_image"] = self._encode_image(reference_image)

            async with httpx.AsyncClient(timeout=120.0) as client:
                # Submit generation task
                resp = await client.post(
                    f"{self.BASE_URL}/services/aigc/text2image/image-synthesis",
                    headers=headers,
                    json=payload,
                )
                resp.raise_for_status()
                task_data = resp.json()
                task_id = task_data["output"]["task_id"]

                # Poll for completion
                result_data = await self._wait_for_task(task_id, headers, client)

                # Download and save images
                image_paths = await self._save_images(
                    result_data["output"]["results"],
                    output_dir,
                )

                return GenerationResult(
                    file_paths=image_paths,
                    parameters=parameters,
                    metadata={
                        "task_id": task_id,
                        "model": self.model,
                        "seed": seed,
                    },
                )

        except Exception as e:
            return GenerationResult(
                file_paths=[],
                parameters=parameters,
                success=False,
                error_message=str(e),
            )

    async def _wait_for_task(
        self,
        task_id: str,
        headers: Dict[str, str],
        client: httpx.AsyncClient,
        timeout: int = 180,
    ) -> Dict[str, Any]:
        """Poll task status until complete or timeout."""
        import time
        start = time.time()
        while time.time() - start < timeout:
            resp = await client.get(
                f"{self.BASE_URL}/tasks/{task_id}",
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            status = data["output"]["task_status"]

            if status == "SUCCEEDED":
                return data
            if status == "FAILED":
                raise RuntimeError(f"DashScope task failed: {data['output'].get('message', 'unknown error')}")

            await asyncio.sleep(2)

        raise TimeoutError(f"DashScope task timed out after {timeout}s")

    async def _save_images(
        self,
        results: List[Dict[str, Any]],
        output_dir: str,
    ) -> List[Path]:
        """Save base64-encoded images to disk."""
        import time
        storage = STORAGE_DIRS["images"]
        storage.mkdir(parents=True, exist_ok=True)

        paths = []
        for i, r in enumerate(results):
            # DashScope returns images as base64 or URL
            if "b64_image" in r:
                data = base64.b64decode(r["b64_image"])
            elif "url" in r:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.get(r["url"])
                    resp.raise_for_status()
                    data = resp.content
            else:
                continue

            filename = f"wanx_{int(time.time())}_{i:03d}.png"
            img_path = storage / filename
            img_path.write_bytes(data)
            paths.append(img_path)

        return paths

    @staticmethod
    def _encode_image(image_path: Path) -> str:
        """Encode image to base64 for image-to-image."""
        return base64.b64encode(image_path.read_bytes()).decode("utf-8")


wanx_provider = WanxProvider()
