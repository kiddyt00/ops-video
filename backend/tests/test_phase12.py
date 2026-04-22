"""
Tests for Phase 12: Multi-Provider Image Generation

Tests provider switching, routing logic, and individual provider interfaces.
"""
import sys
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.providers.base_provider import BaseProvider, GenerationResult
from app.providers.wanx_provider import WanxProvider
from app.providers.siliconflow_provider import SiliconFlowProvider
from app.services.generator_services.image_generator_service import get_image_provider


# ─── Provider Base Tests ─────────────────────────────────────────────

class TestWanxProvider:
    """Test DashScope Wanx provider interface."""

    def test_name(self):
        p = WanxProvider()
        assert p.name == "DashScope-Wanx"

    def test_description(self):
        p = WanxProvider()
        assert "通义万相" in p.description

    def test_validate_parameters_missing_prompt(self):
        p = WanxProvider()
        assert p.validate_parameters({}) is False

    def test_validate_parameters_with_prompt(self):
        p = WanxProvider()
        assert p.validate_parameters({"prompt": "一只猫"}) is True

    def test_default_model(self):
        p = WanxProvider()
        assert p.model == "wanx-v1"

    def test_model_override(self):
        p = WanxProvider(model="wanx-v2")
        assert p.model == "wanx-v2"

    def test_model_invalid_falls_back(self):
        p = WanxProvider(model="invalid-model")
        assert p.model == "wanx-v1"

    def test_generate_returns_failure_without_api_key(self):
        """Verify generate returns failure when no API key (no real call)."""
        p = WanxProvider(api_key="invalid-key-for-test")
        result = asyncio.run(p.generate({"prompt": "test"}))
        assert result.success is False


class TestSiliconFlowProvider:
    """Test SiliconFlow provider interface."""

    def test_name(self):
        p = SiliconFlowProvider()
        assert p.name == "SiliconFlow"

    def test_description(self):
        p = SiliconFlowProvider()
        assert "SiliconFlow" in p.description

    def test_validate_parameters_missing_prompt(self):
        p = SiliconFlowProvider()
        assert p.validate_parameters({}) is False

    def test_validate_parameters_with_prompt(self):
        p = SiliconFlowProvider()
        assert p.validate_parameters({"prompt": "test"}) is True

    def test_default_model(self):
        p = SiliconFlowProvider()
        assert p.model == "black-forest-labs/FLUX.1-schnell"

    def test_model_override(self):
        p = SiliconFlowProvider(model="flux-dev")
        assert p.model == "black-forest-labs/FLUX.1-dev"

    def test_model_passthrough_unknown(self):
        p = SiliconFlowProvider(model="custom/model-name")
        assert p.model == "custom/model-name"

    def test_generate_returns_failure_without_api_key(self):
        p = SiliconFlowProvider(api_key="invalid-key-for-test")
        result = asyncio.run(p.generate({"prompt": "test"}))
        assert result.success is False


# ─── Provider Routing Tests ──────────────────────────────────────────

class TestProviderRouting:
    """Test dynamic provider routing based on config."""

    @patch("app.services.generator_services.image_generator_service.settings")
    def test_get_image_provider_dashscope(self, mock_settings):
        mock_settings.IMAGE_PROVIDER = "DASHSCOPE"
        provider = get_image_provider()
        assert isinstance(provider, WanxProvider)

    @patch("app.services.generator_services.image_generator_service.settings")
    def test_get_image_provider_siliconflow(self, mock_settings):
        mock_settings.IMAGE_PROVIDER = "SILICONFLOW"
        provider = get_image_provider()
        assert isinstance(provider, SiliconFlowProvider)

    @patch("app.services.generator_services.image_generator_service.settings")
    def test_get_image_provider_unknown_defaults_to_dashscope(self, mock_settings):
        mock_settings.IMAGE_PROVIDER = "UNKNOWN"
        provider = get_image_provider()
        assert isinstance(provider, WanxProvider)

    @patch("app.services.generator_services.image_generator_service.settings")
    def test_get_image_provider_empty_defaults_to_dashscope(self, mock_settings):
        mock_settings.IMAGE_PROVIDER = ""
        provider = get_image_provider()
        assert isinstance(provider, WanxProvider)


# ─── GenerationResult Tests ──────────────────────────────────────────

class TestGenerationResult:
    """Test GenerationResult model."""

    def test_default_success(self):
        r = GenerationResult(file_paths=[], parameters={})
        assert r.success is True
        assert r.error_message == ""

    def test_failure(self):
        r = GenerationResult(
            file_paths=[],
            parameters={},
            success=False,
            error_message="timeout",
        )
        assert r.success is False
        assert r.error_message == "timeout"

    def test_with_file_paths(self):
        paths = [Path("/tmp/a.png"), Path("/tmp/b.png")]
        r = GenerationResult(file_paths=paths, parameters={"prompt": "test"})
        assert len(r.file_paths) == 2


