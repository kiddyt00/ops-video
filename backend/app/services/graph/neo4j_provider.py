"""Neo4j graph provider - optional, requires GRAPH_PROVIDER=neo4j in .env"""
from typing import List, Optional
from ...config import settings
from . import GraphProvider, RelationData, CharacterStateData


class Neo4jGraphProvider(GraphProvider):
    """Neo4j implementation of graph storage.

    Nodes:
      Character {name, project_id, status, location, faction, chapter, summary}
      Location {name, project_id, description}
      Organization {name, project_id, description}

    Relationships:
      (c1:Character)-[:MENTOR_OF]->(c2:Character)
      (c1:Character)-[:RIVAL_OF]->(c2:Character)
      (c)-[:LOCATED_IN]->(l:Location)
      (c)-[:SERVES]->(o:Organization)
    """

    def __init__(self):
        self._driver = None

    async def _get_driver(self):
        if self._driver is None:
            try:
                from neo4j import AsyncGraphDatabase
                self._driver = AsyncGraphDatabase.driver(
                    settings.NEO4J_URI,
                    auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                )
            except ImportError:
                raise RuntimeError("neo4j package not installed: pip install neo4j")
        return self._driver

    async def get_relations(self, project_id: str) -> List[RelationData]:
        driver = await self._get_driver()
        async with driver.session() as session:
            result = await session.run(
                """MATCH (a)-[r]->(b)
                   WHERE a.project_id = $pid AND b.project_id = $pid
                   RETURN a.name AS src_name, labels(a)[0] AS src_type,
                          type(r) AS rel_type,
                          b.name AS tgt_name, labels(b)[0] AS tgt_type""",
                pid=project_id,
            )
            rels = []
            async for record in result:
                rels.append(RelationData(
                    project_id=project_id,
                    source_type=getattr(record, "src_type", "character"),
                    source_name=record["src_name"],
                    relation_type=record["rel_type"].lower(),
                    target_type=getattr(record, "tgt_type", "character"),
                    target_name=record["tgt_name"],
                ))
            return rels

    async def create_relation(self, project_id: str, source_type: str, source_name: str,
                              relation_type: str, target_type: str, target_name: str,
                              properties: Optional[dict] = None) -> RelationData:
        driver = await self._get_driver()
        rel_type_upper = relation_type.upper()
        source_label = source_type.capitalize()
        target_label = target_type.capitalize()
        async with driver.session() as session:
            await session.run(
                f"""MERGE (a:{source_label} {{name: $src_name, project_id: $pid}})
                    MERGE (b:{target_label} {{name: $tgt_name, project_id: $pid}})
                    MERGE (a)-[r:{rel_type_upper}]->(b)
                    SET r.project_id = $pid""",
                pid=project_id, src_name=source_name, tgt_name=target_name,
            )
        return RelationData(project_id, source_type, source_name,
                            relation_type, target_type, target_name, properties)

    async def get_latest_character_state(self, project_id: str, character_name: str) -> Optional[CharacterStateData]:
        driver = await self._get_driver()
        async with driver.session() as session:
            result = await session.run(
                """MATCH (c:Character {name: $name, project_id: $pid})
                   RETURN c.chapter AS chapter, c.status AS status,
                          c.location AS location, c.faction AS faction,
                          c.summary AS summary
                   ORDER BY c.chapter DESC LIMIT 1""",
                pid=project_id, name=character_name,
            )
            record = await result.single()
            if not record:
                return None
            return CharacterStateData(
                project_id=project_id, character_name=character_name,
                chapter_number=record.get("chapter", 0),
                status=record.get("status", "alive"),
                location=record.get("location"),
                faction=record.get("faction"),
                summary=record.get("summary"),
            )

    async def save_character_state(self, project_id: str, character_name: str,
                                   chapter_number: int, status: str = "alive",
                                   location: Optional[str] = None,
                                   faction: Optional[str] = None,
                                   summary: Optional[str] = None) -> CharacterStateData:
        driver = await self._get_driver()
        async with driver.session() as session:
            await session.run(
                """MERGE (c:Character {name: $name, project_id: $pid})
                   SET c.chapter = $chapter, c.status = $status,
                       c.location = $location, c.faction = $faction,
                       c.summary = $summary, c.updated = timestamp()""",
                pid=project_id, name=character_name, chapter=chapter_number,
                status=status, location=location or "",
                faction=faction or "", summary=summary or "",
            )
        return CharacterStateData(project_id, character_name, chapter_number,
                                  status, location, faction, summary)

    async def get_continuity_context(self, project_id: str) -> str:
        driver = await self._get_driver()
        async with driver.session() as session:
            result = await session.run(
                """MATCH (c:Character {project_id: $pid})
                   RETURN c.name AS name, c.status AS status,
                          c.location AS location, c.faction AS faction,
                          c.chapter AS chapter
                   ORDER BY c.chapter DESC""",
                pid=project_id,
            )
            lines = ["当前角色状态（请保持情节连贯性）："]
            async for record in result:
                line = f"- {record['name']}: status={record.get('status', 'unknown')}"
                loc = record.get("location")
                if loc:
                    line += f", location={loc}"
                faction = record.get("faction")
                if faction:
                    line += f", faction={faction}"
                if record.get("status") == "dead":
                    line += f"（已于第{record.get('chapter', '?')}章死亡，不可复活）"
                lines.append(line)

            # Get relationships
            rel_result = await session.run(
                """MATCH (a:Character {project_id: $pid})-[r]->(b:Character {project_id: $pid})
                   RETURN a.name AS src, type(r) AS rel, b.name AS tgt""",
                pid=project_id,
            )
            rel_lines = []
            async for record in rel_result:
                rel_lines.append(
                    f"- {record['src']} 是 {record['tgt']} 的{record['rel'].lower()}"
                )
            if rel_lines:
                lines.append("\n角色关系：")
                lines.extend(rel_lines)

            return "\n".join(lines)

    async def close(self):
        if self._driver:
            await self._driver.close()
            self._driver = None
