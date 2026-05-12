"""
LLM Provider for script and storyboard generation
Supports both local LLM (Ollama) and API (OpenAI-compatible)
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
    """LLM Provider for text generation.

    Configuration is loaded dynamically from the database on each generate() call.
    Requires an AIModel with category='llm' and is_active=True to be configured.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        # Config is loaded dynamically from DB; constructor params are only for testing/mocking
        self._api_key = api_key
        self._api_base_url = api_base_url
        self._model = model
        self._loaded = False

    async def _load_model_config(self) -> None:
        """Load active LLM model configuration from the database.

        Must be called before generate(). Cached for the lifetime of the instance
        unless explicitly reset.
        """
        if self._loaded and self._api_key and self._api_base_url and self._model:
            return

        db = SessionLocal()
        try:
            active_model = ai_model_crud.get_active(db, category="llm")
            if not active_model:
                from ..services.workflow_service import WorkflowError
                raise WorkflowError(
                    "No active LLM model configured. Please enable one in AI Models settings."
                )
            self._api_key = active_model.api_key or ""
            self._api_base_url = active_model.api_base_url or ""
            self._model = active_model.model_name or ""
            self._loaded = True
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
        """Validate LLM parameters"""
        required_fields = ["prompt"]
        return all(field in parameters for field in required_fields)

    async def generate(self, parameters: Dict[str, Any]) -> GenerationResult:
        """Generate text using LLM"""
        await self._load_model_config()

        prompt = parameters.get("prompt", "")
        system_prompt = parameters.get("system_prompt", "")
        temperature = parameters.get("temperature", 0.7)
        max_tokens = parameters.get("max_tokens", 2000)
        response_format = parameters.get("response_format")

        try:
            response = await self._call_llm(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
            )

            # Save result to file
            output_path = self._save_result(response, parameters)

            return GenerationResult(
                file_paths=[output_path],
                parameters=parameters,
                metadata={
                    "model": self.model,
                    "temperature": temperature,
                    "completion_tokens": len(response.split()),
                },
            )

        except Exception as e:
            return GenerationResult(
                file_paths=[],
                parameters=parameters,
                success=False,
                error_message=str(e),
            )

    async def _call_llm(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Call LLM API"""
        headers = {
            "Content-Type": "application/json",
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if response_format:
            payload["response_format"] = response_format

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.api_base_url}/chat/completions",
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

        # Generate filename
        import hashlib
        prompt_hash = hashlib.md5(content[:50].encode()).hexdigest()[:8]
        filename = f"script_{prompt_hash}.txt"
        output_path = output_dir / filename

        # Save content
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

        parameters = {
            "prompt": prompt,
            "system_prompt": system_prompt,
            "topic": topic,
            "style": style,
            "duration": duration,
        }

        return await self.generate(parameters)

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

        parameters = {
            "prompt": prompt,
            "system_prompt": system_prompt,
            "script": script,
            "panel_count": panel_count,
        }

        result = await self.generate(parameters)

        # Try to parse JSON from result
        content = result.file_paths[0].read_text() if result.file_paths else ""

        return result


llm_provider = LLMProvider()
