"""Prompt template rendering with $variable substitution and KB injection."""
from string import Template
from typing import Any, Dict
from sqlalchemy.orm import Session
from ..db.prompt_crud import prompt_crud
from .knowledge_service import inject_knowledge


def render_prompt(template: str, context: Dict[str, Any]) -> str:
    """Render a prompt template with $variable substitution."""
    try:
        return Template(template).substitute(context)
    except KeyError as e:
        raise ValueError(f"渲染提示词失败：上下文中缺少变量 '{e.args[0]}'")


def get_rendered_prompt(db: Session, name: str, context: Dict[str, Any]) -> str:
    """Load a prompt template by name, render it, and inject knowledge bases."""
    p = prompt_crud.get_by_name(db, name)
    if not p:
        raise ValueError(f"提示词模板 '{name}' 不存在")
    rendered = render_prompt(p.template, context)
    return inject_knowledge(db, rendered)


_STORY_TEMPLATE = """你是一位专业的中文故事开发者。请将以下灵感扩展为完整的故事大纲。所有输出必须使用中文。

@KB{name=story-structures}

灵感：$inspiration
类型：$genre
基调：$tone
目标篇幅：$target_length
主角设定：$protagonist
主角金手指：$golden_finger
人物关系：$relationship
世界观提示：$worldbuilding_hints

@KB{name=chinese-names}

请基于以上设定，创作一个结构完整、人物鲜明的故事大纲。

返回以下结构的 JSON 对象（所有字段内容必须使用中文）：
{
  "logline": "一句话概括整个故事",
  "synopsis": "详细的故事梗概（300-500字）",
  "title_suggestions": ["备选书名1", "备选书名2"],
  "target_audience": "目标读者群",
  "style_tags": ["风格标签1", "风格标签2"],
  "word_count_estimate": 50000,
  "worldbuilding": {
    "setting": "故事发生的世界背景",
    "time_period": "故事发生的时代",
    "rules": "这个世界的基本规则和力量体系"
  },
  "world_map_hints": "世界地理概述",
  "power_system": {
    "name": "力量体系名称",
    "stages": ["境界1", "境界2", "境界3"],
    "description": "力量体系简述"
  },
  "golden_finger_detail": "主角金手指的详细设定和限制",
  "characters": [
    {
      "name": "角色姓名",
      "role": "角色定位",
      "description": "角色外貌和性格描述",
      "arc": "角色成长弧线简述",
      "abilities": "角色能力或特长"
    }
  ],
  "themes": ["故事主题1", "故事主题2"],
  "plot_points": [
    {"act": "开篇", "description": "开篇设定和冲突引入"},
    {"act": "发展", "description": "主要冲突展开和升级"},
    {"act": "转折", "description": "重大转折或意外事件"},
    {"act": "高潮", "description": "最终对决或关键抉择"},
    {"act": "结局", "description": "故事收束和新平衡"}
  ],
  "prologue_preview": "故事开篇楔子（100-200字吸引读者的段落）"
}

请只返回有效的 JSON，不要包含 markdown 或解释。"""

_CHAPTER_TEMPLATE = """你是一位专业的叙事结构师。请将以下故事大纲拆分为恰好 $chapter_count 个章节。所有输出必须使用中文。

故事大纲：
$story_data_json

前情提要（请严格保持情节连贯性，已死亡的角色不能复活，角色位置变化需合理过渡）：
$continuity_context

角色关系：
$relations_context

返回以下结构的 JSON 对象（所有字段内容必须使用中文）：
{
  "chapters": [
    {
      "chapter_number": 1,
      "title": "章节标题",
      "summary": "本章概要",
      "key_scenes": ["场景1描述"],
      "characters": ["本章出现的角色姓名"],
      "character_events": [
        {"character": "角色名", "event": "重要事件"}
      ],
      "new_locations": ["首次出现的地点"],
      "duration": 5.0
    }
  ]
}

要求：
1. 角色不能复活已死亡状态
2. 角色位置移动必须合理
3. 总章节数必须恰好为 $chapter_count
4. 所有内容使用中文

请只返回有效的 JSON，不要包含 markdown 或解释。"""


_SCRIPT_TEMPLATE = """你是一位专业的漫剧编剧。请根据以下故事设定和角色信息创作剧本。

=== 故事设定 ===
故事梗概：$synopsis
世界观：$worldbuilding
风格：$style_tags

=== 角色信息 ===
$characters_context

主题：$topic

=== 补充上下文 ===
$additional_context

要求：
1. 剧本格式清晰，包含场景描述、角色对话、动作指示
2. 角色对话符合角色设定，保持性格一致
3. 适合漫剧风格，时长 1-3 分钟
4. 对话简洁有力，适合配音
5. 场景描述详细，便于后续生成分镜

请输出完整的剧本内容。"""


_STORYBOARD_TEMPLATE = """你是一位专业的分镜师。请根据以下剧本和故事设定生成分镜描述。

=== 故事设定 ===
故事梗概：$synopsis
世界观：$worldbuilding
风格：$style_tags

=== 角色信息 ===
$characters_context

=== 剧本 ===
$script

要求：
1. 输出 JSON 格式，包含 panels 列表
2. 每个分镜包含：panel_number, scene_description, camera_angle, characters, emotion, composition
3. 描述详细，便于后续生图
4. 考虑镜头语言和画面构图
5. 角色外貌和行为必须符合角色设定
6. 分镜数量：$panel_count 个

请输出 JSON 格式的分镜数据。"""


def seed_default_prompts(db: Session) -> int:
    """Seed built-in prompt templates. Returns number of newly created items."""
    created = 0
    for name, template, desc in [
        ("story-generation", _STORY_TEMPLATE, "故事大纲生成提示词模板"),
        ("chapter-outline", _CHAPTER_TEMPLATE, "章节大纲拆解提示词模板"),
        ("script-generation", _SCRIPT_TEMPLATE, "剧本生成提示词模板"),
        ("storyboard-generation", _STORYBOARD_TEMPLATE, "分镜生成提示词模板"),
    ]:
        existing = prompt_crud.get_by_name(db, name)
        if existing:
            continue
        prompt_crud.create(db, name=name, template=template, description=desc, built_in=True)
        created += 1
    return created
