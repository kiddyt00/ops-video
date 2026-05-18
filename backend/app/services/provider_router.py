"""
Provider Router — dynamically resolves AI providers from database configuration.

Uses the AIModel table for global defaults (is_active per category) and
allows per-project overrides via project.settings.
"""
from uuid import UUID
from typing import Any, Dict, List, Optional, Type
from sqlalchemy.orm import Session

from ..config import settings
from ..db.ai_model_crud import ai_model_crud
from ..db.project_crud import project_crud
from ..providers.base_provider import BaseProvider
from ..providers.wanx_provider import WanxProvider, wanx_provider
from ..providers.siliconflow_provider import SiliconFlowProvider, siliconflow_provider
from ..providers.local_gpu_provider import LocalGPUProvider, local_gpu_provider

# Registry of provider implementations — maps AIModel.provider → class
PROVIDER_IMPLS: Dict[str, Type[BaseProvider]] = {
    "DashScope": WanxProvider,
    "SiliconFlow": SiliconFlowProvider,
    "LocalGPU": LocalGPUProvider,
}


class ProviderRouter:
    """Resolves AI providers dynamically from database configuration."""

    def __init__(self, db: Session):
        self.db = db

    def resolve(
        self,
        category: str,
        project_id: Optional[UUID] = None,
    ) -> BaseProvider:
        """
        Resolve the provider instance for a given category.

        Resolution order:
        1. Per-project override (project.settings.image_provider)
        2. Global active model (AIModel.is_active for this category)
        3. Fallback to hardcoded config (settings.IMAGE_PROVIDER)
        """
        # Step 1: Per-project override
        if project_id:
            provider_info = self._resolve_project_override(project_id, category)
            if provider_info:
                return self._build_provider(category, provider_info)

        # Step 2: Global active model from database
        active_model = ai_model_crud.get_active(self.db, category)
        if active_model and active_model.is_enabled:
            provider_info = {
                "provider": active_model.provider,
                "model_name": active_model.model_name,
                "api_key": active_model.api_key or "",
                "api_base_url": active_model.api_base_url or "",
            }
            return self._build_provider(category, provider_info)

        # Step 3: Fallback to hardcoded config for text2img
        if category == "text2img":
            return self._fallback_text2img()

        raise ValueError(f"No active provider for category '{category}' and no fallback available")

    def _resolve_project_override(
        self,
        project_id: UUID,
        category: str,
    ) -> Optional[Dict[str, str]]:
        """Check if the project has a provider override in its settings."""
        project = project_crud.get(self.db, project_id=project_id)
        if not project or not project.settings:
            return None

        setting_key_map = {
            "text2img": "image_provider",
        }
        key = setting_key_map.get(category)
        if not key:
            return None

        override = project.settings.get(key)
        if not override:
            return None

        # override could be a model ID (UUID) — load from AIModel table
        if isinstance(override, str) and len(override) == 36 and "-" in override:
            try:
                model_uuid = UUID(override)
                model = ai_model_crud.get(self.db, model_uuid)
                if model:
                    return {
                        "provider": model.provider,
                        "model_name": model.model_name,
                        "api_key": model.api_key or "",
                        "api_base_url": model.api_base_url or "",
                    }
            except (ValueError, AttributeError):
                pass

        # override is a provider name (e.g. "DashScope" or "SiliconFlow")
        impl = PROVIDER_IMPLS.get(override)
        if impl:
            models = ai_model_crud.get_all(self.db, category=category)
            for m in models:
                if m.provider == override and m.is_enabled:
                    return {
                        "provider": m.provider,
                        "model_name": m.model_name,
                        "api_key": m.api_key or "",
                        "api_base_url": m.api_base_url or "",
                    }
            # Provider known but no DB entry — construct minimal config
            return {
                "provider": override,
                "model_name": "",
                "api_key": "",
                "api_base_url": "",
            }

        return None

    def _build_provider(self, category: str, info: Dict[str, str]) -> BaseProvider:
        """Instantiate a provider from config info."""
        provider_type = info.get("provider", "")
        model_name = info.get("model_name", "")
        api_key = info.get("api_key", "")

        if provider_type == "DashScope":
            api_key = api_key or settings.DASHSCOPE_API_KEY
            model_name = model_name or settings.DASHSCOPE_MODEL
            if api_key == settings.DASHSCOPE_API_KEY and model_name == settings.DASHSCOPE_MODEL:
                return wanx_provider
            return WanxProvider(api_key=api_key, model=model_name)

        if provider_type == "SiliconFlow":
            api_key = api_key or settings.SILICONFLOW_API_KEY
            model_name = model_name or settings.SILICONFLOW_MODEL
            if api_key == settings.SILICONFLOW_API_KEY and model_name == settings.SILICONFLOW_MODEL:
                return siliconflow_provider
            return SiliconFlowProvider(api_key=api_key, model=model_name)

        if provider_type == "LocalGPU":
            model_name = model_name or "sdxl"
            return LocalGPUProvider(model=model_name)

        raise ValueError(f"Unsupported provider type '{provider_type}' for category '{category}'")

    def _fallback_text2img(self) -> BaseProvider:
        """Fallback to hardcoded IMAGE_PROVIDER config."""
        provider_name = settings.IMAGE_PROVIDER
        if provider_name == "DASHSCOPE":
            return wanx_provider
        elif provider_name == "SILICONFLOW":
            return siliconflow_provider
        return wanx_provider

    def list_available(self, category: str) -> List[Dict[str, Any]]:
        """List all available (enabled) providers for a category.

        Returns metadata suitable for frontend selection UI.
        """
        models = ai_model_crud.get_all(self.db, category=category)
        results = []
        for m in models:
            if not m.is_enabled:
                continue
            results.append({
                "id": str(m.id),
                "name": m.name,
                "provider": m.provider,
                "model_name": m.model_name,
                "is_active": m.is_active,
                "is_builtin": m.is_builtin,
            })
        return results
