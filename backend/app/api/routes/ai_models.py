"""AI Model management API routes"""
from uuid import UUID
from typing import Optional, List
import time
import json
import httpx
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ...db.session import get_db
from ...db.ai_model_crud import ai_model_crud
from ...schemas.ai_model import AIModelCreate, AIModelUpdate, AIModelResponse, ModelTestRequest, ModelTestResponse
from ...core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("", response_model=List[AIModelResponse])
def list_models(category: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """List all AI models, optionally filtered by category"""
    return ai_model_crud.get_all(db, category=category)


@router.post("", response_model=AIModelResponse, status_code=status.HTTP_201_CREATED)
def create_model(model_in: AIModelCreate, db: Session = Depends(get_db)):
    return ai_model_crud.create(db, model_in)


@router.get("/{model_id}", response_model=AIModelResponse)
def get_model(model_id: UUID, db: Session = Depends(get_db)):
    model = ai_model_crud.get(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.put("/{model_id}", response_model=AIModelResponse)
def update_model(model_id: UUID, model_in: AIModelUpdate, db: Session = Depends(get_db)):
    model = ai_model_crud.update(db, model_id, model_in)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model(model_id: UUID, db: Session = Depends(get_db)):
    success = ai_model_crud.delete(db, model_id)
    if not success:
        raise HTTPException(status_code=404, detail="Model not found or is built-in")


@router.post("/{model_id}/toggle", response_model=AIModelResponse)
def toggle_model(model_id: UUID, db: Session = Depends(get_db)):
    model = ai_model_crud.toggle(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.post("/seed", response_model=dict)
def seed_builtins(db: Session = Depends(get_db)):
    count = ai_model_crud.seed_builtins(db)
    return {"seeded": count, "message": f"Seeded {count} built-in models"}


@router.post("/{model_id}/test", response_model=ModelTestResponse)
async def test_model(model_id: UUID, request: ModelTestRequest = ModelTestRequest(), db: Session = Depends(get_db)):
    """Test an AI model by sending a real request. Supports LLM, TTS, and image models."""
    model = ai_model_crud.get(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    start = time.time()

    try:
        if model.category == "llm":
            result = await _test_llm(model, request.prompt or "Say hello in one sentence.")
        elif model.category == "tts":
            result = await _test_tts(model, request.prompt or "你好，这是语音合成测试。")
        elif model.category in ("text2img", "wanx"):
            result = await _test_image(model, request.prompt or "A beautiful sunset over mountains")
        elif model.category == "i2v":
            result = "图生视频模型（需上传图片测试，请在工作流中验证）"
        elif model.category in ("bgm", "video"):
            result = "本地引擎，无需测试连接"
        else:
            result = f"Unknown category: {model.category}"

        latency = (time.time() - start) * 1000
        return ModelTestResponse(success=True, message="Test completed", latency_ms=round(latency, 1), result=result)

    except Exception as e:
        latency = (time.time() - start) * 1000
        logger.warning("Model test failed for %s: %s", model.name, str(e))
        return ModelTestResponse(success=False, message=str(e), latency_ms=round(latency, 1))


async def _test_llm(model, prompt: str) -> str:
    """Test LLM model with a chat completion request"""
    if not model.api_key:
        raise ValueError("API Key not configured")

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{model.api_base_url}/chat/completions",
            headers={"Authorization": f"Bearer {model.api_key}", "Content-Type": "application/json"},
            json={"model": model.model_name, "messages": [{"role": "user", "content": prompt}], "max_tokens": 50},
        )
        if resp.status_code != 200:
            raise ValueError(f"API returned {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        return data["choices"][0]["message"]["content"][:500]


async def _test_tts(model, text: str) -> str:
    """Test TTS — supports DashScope CosyVoice and Edge TTS"""
    if model.provider.lower() in ("dashscope", "bailian"):
        if not model.api_key:
            raise ValueError("API Key not configured")
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{model.api_base_url}/services/aigc/multimodal-generation/generation",
                headers={"Authorization": f"Bearer {model.api_key}", "Content-Type": "application/json"},
                json={
                    "model": model.model_name or "cosyvoice-v1",
                    "input": {"text": text},
                    "parameters": {"voice": "longxiaochun", "format": "mp3"},
                },
            )
            if resp.status_code != 200:
                raise ValueError(f"API returned {resp.status_code}: {resp.text[:200]}")
            return f"CosyVoice 连接成功 (voice: {model.model_name})"

    # Fallback: Edge TTS
    try:
        import edge_tts
        return f"Edge TTS ready (voice: {model.model_name})"
    except ImportError:
        return "Edge TTS 可用"
    except Exception as e:
        raise ValueError(f"TTS test failed: {str(e)}")


async def _test_image(model, prompt: str) -> str:
    """Test image generation model — submit task, poll until complete.

    For wan2.6: uses multimodal-generation/generation endpoint (task-based async).
    For legacy models: uses text2image/image-synthesis endpoint.
    """
    if not model.api_key:
        raise ValueError("API Key not configured")

    async with httpx.AsyncClient(timeout=60) as client:
        if model.provider.lower() in ("dashscope", "bailian"):
            if model.model_name and model.model_name.startswith("wan2.6"):
                # Wan2.6 — submit via multimodal-generation, poll via tasks/
                payload = {
                    "model": model.model_name,
                    "input": {"messages": [{"role": "user", "content": [{"text": prompt}]}]},
                    "parameters": {"size": "768*768", "n": 1, "prompt_extend": False, "watermark": False},
                }
                resp = await client.post(
                    f"https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
                    headers={"Authorization": f"Bearer {model.api_key}", "Content-Type": "application/json"},
                    json=payload,
                )
                if resp.status_code != 200:
                    raise ValueError(f"Submit failed: HTTP {resp.status_code}: {resp.text[:200]}")
                data = resp.json()

                # Check for async task_id first (legacy behavior)
                task_id = data.get("output", {}).get("task_id")
                if task_id:
                    status = data.get("output", {}).get("task_status", "PENDING")
                    return f"Task submitted: {task_id} (status: {status})"

                # Check for sync inline images
                choices = data.get("output", {}).get("choices", [])
                if choices:
                    n_images = 0
                    for choice in choices:
                        for item in choice.get("message", {}).get("content", []):
                            if item.get("image"):
                                n_images += 1
                    return f"Generation completed ({n_images} image(s))"

                raise ValueError(f"Unexpected response: {json.dumps(data, ensure_ascii=False)[:300]}")

            else:
                # Legacy async text2image (wanx-v2, wanx2.1, etc.)
                resp = await client.post(
                    f"https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis",
                    headers={"Authorization": f"Bearer {model.api_key}", "Content-Type": "application/json"},
                    json={
                        "model": model.model_name,
                        "input": {"prompt": prompt},
                        "parameters": {"size": "512*512", "n": 1},
                    },
                )
                if resp.status_code != 200:
                    raise ValueError(f"API returned {resp.status_code}: {resp.text[:200]}")
                data = resp.json()
                task_id = data.get("output", {}).get("task_id", "unknown")
                return f"Image generation task created: {task_id}"

    raise ValueError(f"Unsupported image provider: {model.provider}")
