"""
DashScope Wanx (通义万相) Provider for image generation.
Supports wan2.6-t2i (sync, multimodal-generation) and legacy async models.
"""
import asyncio
import base64
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import httpx

from ..config import settings, STORAGE_DIRS
from ..db.session import SessionLocal
from ..db.storage_provider_crud import storage_provider_crud
from ..core.oss_service import OSSService
from .base_provider import BaseProvider, GenerationResult

logger = logging.getLogger(__name__)


class WanxProvider(BaseProvider):
    """DashScope Wanx provider for manga-style image generation."""

    BASE_URL = "https://dashscope.aliyuncs.com/api/v1"

    MODEL_MAPPING = {
        # v2.6 (recommended, sync)
        "wan2.6-t2i": "wan2.6-t2i",
        # Legacy models (async only)
        "wanx-v1": "wanx-v1",
        "wanx-v2": "wanx-v2",
        "wanx2.1-t2i-turbo": "wanx2.1-t2i-turbo",
        "wanx2.1-t2i-plus": "wanx2.1-t2i-plus",
    }

    # Models that use the new multimodal-generation sync API
    SYNC_MODELS = {"wan2.6-t2i"}

    # Models that use the old async image-synthesis API
    ASYNC_MODELS = {"wanx-v1", "wanx-v2", "wanx2.1-t2i-turbo", "wanx2.1-t2i-plus"}

    def __init__(
        self,
        api_key: str = "",
        model: str = "",
    ):
        self.api_key = api_key or settings.DASHSCOPE_API_KEY
        resolved = model or settings.DASHSCOPE_MODEL
        self.model = self.MODEL_MAPPING.get(resolved, resolved)

    @property
    def name(self) -> str:
        return "DashScope-Wanx"

    @property
    def description(self) -> str:
        return "通义万相 - 阿里达摩院文生图模型"

    @property
    def is_sync(self) -> bool:
        return self.model in self.SYNC_MODELS

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        return "prompt" in parameters

    async def generate(self, parameters: Dict[str, Any]) -> GenerationResult:
        if self.is_sync:
            return await self._generate_sync(parameters)
        else:
            return await self._generate_async(parameters)

    # ─── Wan2.6 (multimodal-generation, task-based async) ─────────────

    async def _generate_sync(self, parameters: Dict[str, Any]) -> GenerationResult:
        """Generate via multimodal-generation (wan2.6-t2i, task-based async).

        Submits a generation task, polls until complete, then downloads images.
        Despite the method name, wan2.6 uses the same async task/poll pattern
        as legacy models — just with a different submission endpoint.
        """
        prompt = parameters.get("prompt", "")
        negative_prompt = parameters.get("negative_prompt", "")
        size = parameters.get("size", "1280*1280")
        n = int(parameters.get("n", 1))
        seed = parameters.get("seed", -1)
        prompt_extend = parameters.get("prompt_extend", True)
        output_dir = parameters.get("output_dir", "images")

        try:
            payload = {
                "model": self.model,
                "input": {
                    "messages": [
                        {
                            "role": "user",
                            "content": [{"text": prompt}],
                        }
                    ],
                },
                "parameters": {
                    "size": size,
                    "n": n,
                    "prompt_extend": prompt_extend,
                    "watermark": False,
                },
            }

            if negative_prompt:
                payload["parameters"]["negative_prompt"] = negative_prompt
            if seed != -1:
                payload["parameters"]["seed"] = seed

            async with httpx.AsyncClient(timeout=300.0) as client:
                # Step 1: Submit task
                resp = await client.post(
                    f"{self.BASE_URL}/services/aigc/multimodal-generation/generation",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()

                task_id = data.get("output", {}).get("task_id")
                if not task_id:
                    # Maybe synchronous response with inline images?
                    image_urls = []
                    for choice in data.get("output", {}).get("choices", []):
                        for item in choice.get("message", {}).get("content", []):
                            if item.get("type") == "image":
                                image_urls.append(item["image"])
                    if image_urls:
                        image_paths = await self._download_images(image_urls, output_dir, client)
                        oss_urls = await self._try_upload_to_oss(image_paths)
                        return GenerationResult(
                            file_paths=image_paths,
                            parameters=parameters,
                            metadata={"model": self.model, "seed": seed, "image_count": len(image_paths)},
                            oss_urls=oss_urls,
                        )
                    raise RuntimeError(f"No task_id or images in response: {json.dumps(data, ensure_ascii=False)[:500]}")

                # Step 2: Poll task
                result_data = await self._wait_for_task(task_id, client)

                # Step 3: Download and save images
                image_paths = await self._save_images(
                    result_data["output"]["results"],
                    output_dir,
                )

                oss_urls = await self._try_upload_to_oss(image_paths)

                return GenerationResult(
                    file_paths=image_paths,
                    parameters=parameters,
                    metadata={
                        "task_id": task_id,
                        "model": self.model,
                        "seed": seed,
                        "image_count": len(image_paths),
                    },
                    oss_urls=oss_urls,
                )

        except Exception as e:
            return GenerationResult(
                file_paths=[],
                parameters=parameters,
                success=False,
                error_message=str(e),
            )

    # ─── Async legacy (wanx2.1 / wanx-v1/v2) ──────────────────────────

    async def _generate_async(self, parameters: Dict[str, Any]) -> GenerationResult:
        """Legacy async flow: create task → poll → download."""
        prompt = parameters.get("prompt", "")
        negative_prompt = parameters.get("negative_prompt", "")
        size = parameters.get("size", "1024*1024")
        seed = parameters.get("seed", -1)
        steps = parameters.get("steps", 30)
        output_dir = parameters.get("output_dir", "images")

        try:
            payload = {
                "model": self.model,
                "input": {"prompt": prompt},
                "parameters": {"size": size, "steps": steps},
            }
            if negative_prompt:
                payload["input"]["negative_prompt"] = negative_prompt
            if seed != -1:
                payload["parameters"]["seed"] = seed

            async with httpx.AsyncClient(timeout=300.0) as client:
                resp = await client.post(
                    f"{self.BASE_URL}/services/aigc/text2image/image-synthesis",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "X-DashScope-Async": "enable",
                    },
                    json=payload,
                )
                resp.raise_for_status()
                task_data = resp.json()
                task_id = task_data["output"]["task_id"]

                # Poll for completion
                result_data = await self._wait_for_task(task_id, client)

                # Download and save images
                image_paths = await self._save_images(
                    result_data["output"]["results"],
                    output_dir,
                )

                oss_urls = await self._try_upload_to_oss(image_paths)

                return GenerationResult(
                    file_paths=image_paths,
                    parameters=parameters,
                    metadata={
                        "task_id": task_id,
                        "model": self.model,
                        "seed": seed,
                    },
                    oss_urls=oss_urls,
                )

        except Exception as e:
            return GenerationResult(
                file_paths=[],
                parameters=parameters,
                success=False,
                error_message=str(e),
            )

    # ─── Helpers ──────────────────────────────────────────────────────

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
                        logger.info("WanxProvider uploaded %s -> %s", p, url)
                    except Exception as e:
                        logger.warning("WanxProvider OSS upload failed for %s: %s", p, e)
                return urls
            finally:
                db.close()
        except Exception as e:
            logger.warning("WanxProvider OSS upload check failed: %s", e)
            return []

    async def _download_images(
        self,
        urls: List[str],
        output_dir: str,
        client: httpx.AsyncClient,
    ) -> List[Path]:
        """Download images from signed URLs to local storage."""
        import time
        storage = STORAGE_DIRS["images"]
        storage.mkdir(parents=True, exist_ok=True)

        paths = []
        for i, url in enumerate(urls):
            resp = await client.get(url)
            resp.raise_for_status()
            filename = f"wanx_{int(time.time() * 1000)}_{i:03d}.png"
            img_path = storage / filename
            img_path.write_bytes(resp.content)
            paths.append(img_path)

        return paths

    async def _wait_for_task(
        self,
        task_id: str,
        client: httpx.AsyncClient,
        timeout: int = 300,
    ) -> Dict[str, Any]:
        """Poll task status until complete or timeout."""
        import time
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

            await asyncio.sleep(2)

        raise TimeoutError(f"Task timed out after {timeout}s")

    async def _save_images(
        self,
        results: List[Dict[str, Any]],
        output_dir: str,
    ) -> List[Path]:
        """Save base64 or URL images to disk (legacy async response format)."""
        import time
        storage = STORAGE_DIRS["images"]
        storage.mkdir(parents=True, exist_ok=True)

        paths = []
        async with httpx.AsyncClient(timeout=60.0) as client:
            for i, r in enumerate(results):
                if "b64_image" in r:
                    data = base64.b64decode(r["b64_image"])
                elif "url" in r:
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
        return base64.b64encode(image_path.read_bytes()).decode("utf-8")


wanx_provider = WanxProvider()
