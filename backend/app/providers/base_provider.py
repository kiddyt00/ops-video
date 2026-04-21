"""
Base provider interface
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List
from pydantic import BaseModel


class GenerationResult(BaseModel):
    """Result of a generation operation"""
    file_paths: List[Path]
    parameters: Dict[str, Any]
    metadata: Dict[str, Any] = {}
    success: bool = True
    error_message: str = ""


class BaseProvider(ABC):
    """Base class for AI service providers"""

    @abstractmethod
    async def generate(self, parameters: Dict[str, Any]) -> GenerationResult:
        """Generate content based on parameters"""
        pass

    @abstractmethod
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate generation parameters"""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Provider description"""
        pass
