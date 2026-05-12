"""
LLM Provider for script and storyboard generation
Supports multiple providers with automatic fallback (qwen → glm → kimi → ...)
Configuration is loaded dynamically from the database (AIModel with category='llm' and is_active=True)
"""
import json
import httpx
from typing import Any, Dict, List, Optional
from pathlib import Path
from ..models.declarative import SessionLocal
from ..db.ai_model_crud import ai_model_crud
from .base_provider import BaseProvider, GenerationResult


class LLMProvider(BaseProvider):
    """LLM Provider for text generation with multi-model fallback.

    Loads ALL active LLM models from database and tries them in order.
    Falls through to next model on any error.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        # Constructor params are for testing/mocking; real config from DB
        self._api_key = api_key
        self._api_base_url = api_base_url
        self._model = model
        self._loaded = False
        self._fallback_models: List[Dict[str, str]] = []  # [{api_key, api_base_url, model_name}]

    async def _load_fallback_models(self) -> List[Dict[str, str]]:
        """Load ALL enabled LLM models from DB, sorted by priority."""
        if self._loaded and self._fallback_models:
            return self._fallback_models

        db = SessionLocal()
        try:
            all_models = ai_model_crud.get_all(db, category="llm")
            enabled = [m for m in all_models if m.is_enabled and m.api_base_url and m.model_name]
            if not enabled:
                from ..services.workflow_service import WorkflowError
                raise WorkflowError(
                    "No enabled LLM model configured. Please enable one in AI Models settings."
                )
            # Prefer is_active first, then by creation order
            enabled.sort(key=lambda m: (not m.is_active, m.created_at or ""))
            self._fallback_models = [
                {
                    "api_key": m.api_key or "",
                    "api_base_url": m.api_base_url or "",
                    "model_name": m.model_name or "",
                    "display_name": m.display_name or m.name or m.model_name or "unknown",
                }
                for m in enabled
            ]
            self._loaded = True
            return self._fallback_models
        finally:
            db.close()

    @property
    def api_key(self) -> str:
        return self._api_key or ""

    @property
    def api_base_url(self) -> str:
        return self._api_base_url or ""

    @property
    def model(self) -> str:
        return self._model or ""

    @property
    def name(self) -> str:
        return "LLM"

    @property
    def description(self) -> str:
        return "Large Language Model for script and storyboard generation"

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        required_fields = ["prompt"]
        return all(field in parameters for field in required_fields)

    async def generate(self, parameters: Dict[str, Any]) -> GenerationResult:
        """Generate text using LLM with multi-model fallback."""
        prompt = parameters.get("prompt", "")
        system_prompt = parameters.get("system_prompt", "")
        temperature = parameters.get("temperature", 0.7)
        max_tokens = parameters.get("max_tokens", 2000)
        response_format = parameters.get("response_format")

        models = await self._load_fallback_models()
        last_error = None

        for i, cfg in enumerate(models):
            try:
                response = await self._call_llm_with_config(
                    cfg=cfg,
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format=response_format,
                )

                output_path = self._save_result(response, parameters)

                return GenerationResult(
                    file_paths=[output_path],
                    parameters=parameters,
                    metadata={
                        "model": cfg["model_name"],
                        "temperature": temperature,
                        "completion_tokens": len(response.split()),
                        "fallback_attempt": i + 1,
                    },
                )

            except Exception as e:
                last_error = str(e)
                from ..core.logging_config import get_logger
                logger = get_logger(__name__)
                logger.warning(
                    "LLM model '%s' failed (attempt %d/%d): %s",
                    cfg.get("display_name"), i + 1, len(models), str(e)[:200]
                )
                continue

        return GenerationResult(
            file_paths=[],
            parameters=parameters,
            success=False,
            error_message=f"All {len(models)} LLM providers failed. Last error: {last_error}",
        )

    async def _call_llm_with_config(
        self,
        cfg: Dict[str, str],
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Call a specific LLM API with the given config."""
        headers = {"Content-Type": "application/json"}
        if cfg["api_key"]:
            headers["Authorization"] = f"Bearer {cfg['api_key']}"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": cfg["model_name"],
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if response_format:
            payload["response_format"] = response_format

        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{cfg['api_base_url']}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]

    def _save_result(self, content: str, parameters: Dict[str, Any]) -> Path:
        """Save generated text to file"""
        from ..config import STORAGE_DIRS
        output_dir = STORAGE_DIRS["scripts"]
        output_dir.mkdir(parents=True, exist_ok=True)
        import hashlib
        prompt_hash = hashlib.md5(content[:50].encode()).hexdigest()[:8]
        filename = f"script_{prompt_hash}.txt"
        output_path = output_dir / filename
        output_path.write_text(content, encoding="utf-8")
        return output_path

    async def generate_script(
        self,
        topic: str,
        style: str = "comic",
        duration: str = "1-3 minutes",
        additional_context: Optional[str] = None,
    ) -> GenerationResult:
        """Generate a script from a topic"""
        system_prompt = """你是一个专业的漫剧编剧。请根据用户提供的主题创作一个短篇漫剧剧本。

要求：
1. 剧本格式清晰，包含场景描述、角色对话、动作指示
2. 适合漫画/动漫风格表现
3. 时长控制在 1-3 分钟
4. 对话简洁有力，适合配音
5. 场景描述详细，便于后续生成分镜"""

        prompt = f"""请为以下主题创作一个漫剧剧本：

主题：{topic}
风格：{style}
时长：{duration}
"""

        if additional_context:
            prompt += f"\n额外信息：{additional_context}\n"

        prompt += "\n请输出完整的剧本内容。"

        return await self.generate({
            "prompt": prompt,
            "system_prompt": system_prompt,
            "topic": topic,
            "style": style,
            "duration": duration,
        })

    async def generate_storyboard(
        self,
        script: str,
        panel_count: int = 6,
    ) -> GenerationResult:
        """Generate storyboard from script"""
        system_prompt = """你是一个专业的分镜师。请根据剧本生成分镜描述。

要求：
1. 输出 JSON 格式，包含以下字段：
   - panels: 分镜列表
   - 每个分镜包含：panel_number, scene_description, camera_angle, characters, emotion, composition
2. 描述详细，便于后续生成图片
3. 考虑镜头语言和画面构图"""

        prompt = f"""请为以下剧本生成分镜描述（共 {panel_count} 个分镜）：

剧本：
{script}

请输出 JSON 格式的分镜数据。"""

        return await self.generate({
            "prompt": prompt,
            "system_prompt": system_prompt,
            "script": script,
            "panel_count": panel_count,
        })


llm_provider = LLMProvider()
