"""
ComfyUI Provider for image generation
Connects to ComfyUI server via WebSocket and HTTP API
"""
import uuid
import json
import urllib.request
import urllib.parse
import urllib.error
from typing import Any, Dict, List, Optional
from pathlib import Path
import asyncio
from ..config import settings
from .base_provider import BaseProvider, GenerationResult


class ComfyUIProvider(BaseProvider):
    """ComfyUI Provider for image generation"""

    def __init__(
        self,
        host: str = "",
        port: int = 0,
    ):
        self.host = host or settings.COMFYUI_HOST
        self.port = port or settings.COMFYUI_PORT
        self.base_url = f"http://{self.host}:{self.port}"
        self.client_id = str(uuid.uuid4())

    @property
    def name(self) -> str:
        return "ComfyUI"

    @property
    def description(self) -> str:
        return "ComfyUI for manga/anime style image generation"

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate ComfyUI parameters"""
        required_fields = ["prompt"]
        return all(field in parameters for field in required_fields)

    async def generate(self, parameters: Dict[str, Any]) -> GenerationResult:
        """Generate image using ComfyUI"""
        prompt_text = parameters.get("prompt", "")
        negative_prompt = parameters.get("negative_prompt", "")
        seed = parameters.get("seed", -1)
        steps = parameters.get("steps", 20)
        cfg_scale = parameters.get("cfg_scale", 7.0)
        sampler = parameters.get("sampler", "euler")
        scheduler = parameters.get("scheduler", "normal")
        width = parameters.get("width", 512)
        height = parameters.get("height", 768)
        workflow_id = parameters.get("workflow_id", "default")

        try:
            # Build workflow
            workflow = self._build_workflow(
                prompt=prompt_text,
                negative_prompt=negative_prompt,
                seed=seed,
                steps=steps,
                cfg_scale=cfg_scale,
                sampler=sampler,
                scheduler=scheduler,
                width=width,
                height=height,
            )

            # Queue prompt
            prompt_id = await self._queue_prompt(workflow)

            # Wait for generation to complete
            result = await self._wait_for_completion(prompt_id)

            # Download images
            image_paths = await self._download_images(
                result["outputs"],
                parameters.get("output_dir", "images"),
            )

            return GenerationResult(
                file_paths=image_paths,
                parameters=parameters,
                metadata={
                    "prompt_id": prompt_id,
                    "seed": seed if seed != -1 else result.get("seed"),
                    "workflow_id": workflow_id,
                },
            )

        except Exception as e:
            return GenerationResult(
                file_paths=[],
                parameters=parameters,
                success=False,
                error_message=str(e),
            )

    def _build_workflow(
        self,
        prompt: str,
        negative_prompt: str,
        seed: int,
        steps: int,
        cfg_scale: float,
        sampler: str,
        scheduler: str,
        width: int,
        height: int,
    ) -> Dict[str, Any]:
        """Build ComfyUI workflow JSON"""
        # This is a basic workflow for SDXL
        # Users can customize this or load from workflow files
        workflow = {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "cfg": cfg_scale,
                    "denoise": 1,
                    "latent_image": ["5", 0],
                    "model": ["4", 0],
                    "negative": ["7", 0],
                    "positive": ["6", 0],
                    "sampler": sampler,
                    "scheduler": scheduler,
                    "seed": seed if seed != -1 else int(asyncio.get_event_loop().time() * 1000) % (2**31),
                    "steps": steps,
                }
            },
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {
                    "ckpt_name": "anime-model.safetensors"
                }
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {
                    "batch_size": 1,
                    "height": height,
                    "width": width
                }
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "clip": ["4", 1],
                    "text": prompt
                }
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "clip": ["4", 1],
                    "text": negative_prompt
                }
            },
            "8": {
                "class_type": "VAEDecode",
                "inputs": {
                    "samples": ["3", 0],
                    "vae": ["4", 2]
                }
            },
            "9": {
                "class_type": "SaveImage",
                "inputs": {
                    "filename_prefix": "ops_video",
                    "images": ["8", 0]
                }
            }
        }

        return workflow

    async def _queue_prompt(self, workflow: Dict[str, Any]) -> str:
        """Queue prompt to ComfyUI"""
        data = {
            "prompt": workflow,
            "client_id": self.client_id,
        }

        req = urllib.request.Request(
            f"{self.base_url}/prompt",
            data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result["prompt_id"]

    async def _wait_for_completion(
        self,
        prompt_id: str,
        timeout: int = 120,
    ) -> Dict[str, Any]:
        """Wait for prompt to complete"""
        import time

        start_time = time.time()

        while time.time() - start_time < timeout:
            req = urllib.request.Request(
                f"{self.base_url}/history/{prompt_id}"
            )

            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode("utf-8"))

                if prompt_id in result:
                    history = result[prompt_id]
                    if history.get("outputs"):
                        return history["outputs"]

            await asyncio.sleep(1)

        raise TimeoutError(f"Generation timed out after {timeout} seconds")

    async def _download_images(
        self,
        outputs: Dict[str, Any],
        output_dir: str = "images",
    ) -> List[Path]:
        """Download generated images"""
        from ..config import settings

        image_paths = []

        for node_id, node_output in outputs.items():
            if "images" in node_output:
                for image_info in node_output["images"]:
                    filename = image_info.get("filename")
                    subfolder = image_info.get("subfolder", "")

                    # Build image path
                    rel_path = f"{subfolder}/{filename}" if subfolder else filename
                    image_paths.append(Path(rel_path))

                    # Download image
                    params = {
                        "filename": filename,
                        "subfolder": subfolder,
                        "type": "output",
                    }
                    url = f"{self.base_url}/view?{urllib.parse.urlencode(params)}"

                    # Save to storage
                    storage_path = settings.storage_path / output_dir
                    storage_path.mkdir(parents=True, exist_ok=True)

                    local_path = storage_path / filename
                    urllib.request.urlretrieve(url, local_path)

        return image_paths

    async def get_workflows(self) -> List[str]:
        """Get available workflows"""
        # This would query ComfyUI for available workflow files
        # For now, return a default list
        return ["default", "anime_portrait", "full_body", "scene"]

    async def execute_workflow(
        self,
        workflow_id: str,
        parameters: Dict[str, Any],
    ) -> GenerationResult:
        """Execute a specific workflow"""
        # Load workflow from file or use default
        workflow = self._load_workflow(workflow_id)

        # Merge parameters
        merged_params = {**workflow.get("default_params", {}), **parameters}

        return await self.generate(merged_params)

    def _load_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Load workflow from file"""
        # This would load workflow JSON from disk
        # For now, return a basic workflow
        return {
            "default_params": {
                "steps": 20,
                "cfg_scale": 7.0,
                "sampler": "euler",
            }
        }


comfyui_provider = ComfyUIProvider()
