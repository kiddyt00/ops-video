"""Abstract graph provider interface.

Supports SQLite (default) and Neo4j backends.
Configuration in settings: GRAPH_PROVIDER=sqlite|neo4j
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from sqlalchemy.orm import Session


class RelationData:
    def __init__(self, project_id: str, source_type: str, source_name: str,
                 relation_type: str, target_type: str, target_name: str,
                 properties: Optional[dict] = None):
        self.project_id = project_id
        self.source_type = source_type
        self.source_name = source_name
        self.relation_type = relation_type
        self.target_type = target_type
        self.target_name = target_name
        self.properties = properties or {}


class CharacterStateData:
    def __init__(self, project_id: str, character_name: str,
                 chapter_number: int, status: str = "alive",
                 location: Optional[str] = None, faction: Optional[str] = None,
                 summary: Optional[str] = None):
        self.project_id = project_id
        self.character_name = character_name
        self.chapter_number = chapter_number
        self.status = status
        self.location = location
        self.faction = faction
        self.summary = summary


class GraphProvider(ABC):
    """Abstract interface for graph/relation storage."""

    @abstractmethod
    async def get_relations(self, project_id: str) -> List[RelationData]:
        ...

    @abstractmethod
    async def create_relation(self, project_id: str, source_type: str, source_name: str,
                              relation_type: str, target_type: str, target_name: str,
                              properties: Optional[dict] = None) -> RelationData:
        ...

    @abstractmethod
    async def get_latest_character_state(self, project_id: str, character_name: str) -> Optional[CharacterStateData]:
        ...

    @abstractmethod
    async def save_character_state(self, project_id: str, character_name: str,
                                   chapter_number: int, status: str = "alive",
                                   location: Optional[str] = None,
                                   faction: Optional[str] = None,
                                   summary: Optional[str] = None) -> CharacterStateData:
        ...

    @abstractmethod
    async def get_continuity_context(self, project_id: str) -> str:
        ...


def get_graph_provider() -> GraphProvider:
    """Get the configured graph provider."""
    from ...config import settings
    if settings.GRAPH_PROVIDER == "neo4j":
        from .neo4j_provider import Neo4jGraphProvider
        return Neo4jGraphProvider()
    from .sqlite_provider import SQLiteGraphProvider
    return SQLiteGraphProvider()
