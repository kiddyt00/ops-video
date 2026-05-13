"""Knowledge base injection and continuity context builder."""
import re
from typing import Any, Dict
from sqlalchemy.orm import Session
from ..db.knowledge_crud import knowledge_crud

_KB_NAME_PATTERN = re.compile(r"@KB\{\s*name\s*=\s*([^}]+)\}")
_KB_ID_PATTERN = re.compile(r"@KB\{\s*id\s*=\s*([^}]+)\}")


def inject_knowledge(db: Session, template: str) -> str:
    """Replace @KB{name=...} and @KB{id=...} with knowledge content."""
    result = template

    def _replace_by_name(match):
        name = match.group(1).strip()
        kb = knowledge_crud.get_by_name(db, name)
        if kb:
            return kb.content
        return f"/* 知识库未找到: name={name} */"

    def _replace_by_id(match):
        kid = match.group(1).strip()
        kb = knowledge_crud.get(db, kid)
        if kb:
            return kb.content
        return f"/* 知识库未找到: id={kid} */"

    result = _KB_NAME_PATTERN.sub(_replace_by_name, result)
    result = _KB_ID_PATTERN.sub(_replace_by_id, result)
    return result


def build_continuity_context(db: Session, project_id: str) -> str:
    """Build a '前情提要' context string for chapter generation.

    Includes all characters' latest status, location, faction, and their relationships.
    """
    from ..db.character_state_crud import character_state_crud
    from ..db.relation_crud import relation_crud

    states = character_state_crud.get_all_latest(db, project_id)
    relations = relation_crud.list_by_project(db, project_id)

    if not states:
        return "（无前情提要，这是第一章）"

    lines = ["当前角色状态（请保持情节连贯性）："]
    for s in states:
        line = f"- {s.character_name}: status={s.status}"
        if s.location:
            line += f", location={s.location}"
        if s.faction:
            line += f", faction={s.faction}"
        if s.status == "dead":
            line += f"（已于第{s.chapter_number}章死亡，不可复活）"
        lines.append(line)

    if relations:
        lines.append("\n角色关系：")
        for r in relations:
            lines.append(f"- {r.source_name} 是 {r.target_name} 的{r.relation_type}")

    return "\n".join(lines)
