"""
SiliconFlow Provider for image generation
Compatible with OpenAI /images/generations API, supporting FLUX.1
"""
import base64
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import httpx

from ..config import settings, STORAGE_DIRS
from .base_provider import BaseProvider, GenerationResult


class SiliconFlowProvider(BaseProvider):
    """SiliconFlow provider for image generation via OpenAI-compatible API."""

    BASE_URL = "https://api.siliconflow.cn/v1"

    MODEL_MAPPING = {
        "flux-schnell": "black-forest-labs/FLUX.1-schnell",
        "flux-dev": "black-forest-labs/FLUX.1-dev",
        "sd3": "stabilityai/stable-diffusion-3-medium",
    }

    def __init__(
        self,
        api_key: str = "",
        model: str = "",
    ):
        self.api_key = api_key or settings.SILICONFLOW_API_KEY
        model_name = model or settings.SILICONFLOW_MODEL
        self.model = self.MODEL_MAPPING.get(model_name, model_name)

    @property
    def name(self) -> str:
        return "SiliconFlow"

    @property
    def description(self) -> str:
        return "SiliconFlow (FLUX.1 / SD3) — OpenAI-compatible image API"

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate parameters."""
        return "prompt" in parameters

    async def generate(self, parameters: Dict[str, Any]) -> GenerationResult:
        """Generate image using SiliconFlow API (OpenAI-compatible)."""
        prompt = parameters.get("prompt", "")
        negative_prompt = parameters.get("negative_prompt", "")
        width = parameters.get("width", 1024)
        height = parameters.get("height", 1024)
        seed = parameters.get("seed", -1)
        steps = parameters.get("steps", 4)
        guidance_scale = parameters.get("cfg_scale", 3.5)
        batch_size = parameters.get("n", 1)
        output_dir = parameters.get("output_dir", "images")

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": self.model,
                "prompt": prompt,
                "response_format": "b64_json",
                "n": batch_size,
            }

            # Model-specific parameters
            if negative_prompt:
                payload["negative_prompt"] = negative_prompt
            if width:
                payload["width"] = width
            if height:
                payload["height"] = height
            if seed != -1:
                payload["seed"] = seed
            if steps:
                payload["num_inference_steps"] = steps
            if guidance_scale:
                payload["guidance_scale"] = guidance_scale

            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    f"{self.BASE_URL}/images/generations",
                    headers=headers,
                    json=payload,
                )
                resp.raise_for_status()
                result = resp.json()

            # Save images from b64_json response
            image_paths = self._save_images(
                [item.get("b64_json") for item in result.get("data", []) if item.get("b64_json")],
                output_dir,
            )

            return GenerationResult(
                file_paths=image_paths,
                parameters=parameters,
                metadata={
                    "model": self.model,
                    "seed": seed,
                    "revised_prompt": result.get("data", [{}])[0].get("revised_prompt"),
                },
            )

        except Exception as e:
            return GenerationResult(
                file_paths=[],
                parameters=parameters,
                success=False,
                error_message=str(e),
            )

    def _save_images(
        self,
        b64_images: List[str],
        output_dir: str,
    ) -> List[Path]:
        """Save base64-encoded images to disk."""
        storage = STORAGE_DIRS["images"]
        storage.mkdir(parents=True, exist_ok=True)

        paths = []
        for i, b64_data in enumerate(b64_images):
            data = base64.b64decode(b64_data)
            filename = f"siliconflow_{int(time.time())}_{i:03d}.png"
            img_path = storage / filename
            img_path.write_bytes(data)
            paths.append(img_path)

        return paths


siliconflow_provider = SiliconFlowProvider()
