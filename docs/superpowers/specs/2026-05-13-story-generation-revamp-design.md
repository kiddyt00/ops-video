# Phase A: 故事生成逻辑重构 + 知识库系统

**日期**: 2026-05-13
**参考**: NovelForge (RhythmicWave/NovelForge) 的卡片生成、知识库注入、指令流式设计方案

## 目标

将 ops-video 的故事生成从"一次性黑盒 JSON 返回"改造为更可控、更丰富的创作体验。核心改动三点：

1. **知识库系统** — 名字生成字典、地名库、世界观模板等，用 `@KB{name=...}` 注入提示词
2. **提示词模板化** — 从硬编码 f-string 改为可编辑模板，支持 `$variable` 替换 + `@KB` 注入
3. **丰富输出 Schema** — 扩展 Story 模型字段，增加更多创作维度

## 不做的事

- 不做指令流式生成（instruction flow）—— 那是 Phase B 的事
- 不碰前端 —— Phase A 纯后端改动
- 不改变工作流 Tab 的 8 阶段结构

---

## 一、知识库系统

### 数据模型

```
Knowledge {
    id: UUID
    name: str (unique)           # e.g. "chinese-surnames", "dynasty-names"
    category: str                 # e.g. "name", "world", "style", "genre"
    content: str                  # Markdown/JSON 格式的知识内容
    description: Optional[str]
    built_in: bool = False        # 系统内置的不可删除
    created_at, updated_at
}
```

### 内置知识库种子数据（6 个）

| name | category | 内容 |
|------|----------|------|
| `chinese-names` | name | 100 个姓氏 + 200 个名字用字，分男女，附含义 |
| `chinese-place-names` | world | 50 个地名前缀 + 30 个地名后缀 + 命名规则 |
| `chinese-dynasties` | world | 15 个常见朝代设定模板（含政治制度、服饰、科技水平） |
| `xianxia-world-rules` | world | 修仙世界观设定指南：境界体系、宗门结构、灵石货币等 |
| `scifi-world-rules` | world | 科幻世界观设定指南：科技等级、星际政治、AI 伦理等 |
| `story-structures` | genre | 7 种经典叙事结构（英雄之旅、三幕式、起承转合等） |

### API 端点

```
GET    /api/v1/knowledge              # 列表（支持 ?category= 过滤）
GET    /api/v1/knowledge/{id}         # 详情
POST   /api/v1/knowledge              # 创建
PUT    /api/v1/knowledge/{id}         # 更新
DELETE /api/v1/knowledge/{id}         # 删除（built_in 保护）
```

### 注入逻辑

```
prompt 中的 @KB{name=chinese-names} → 替换为该知识库的 content
prompt 中的 @KB{id=xxx}            → 按 ID 替换
```

实现为 `knowledge_service.inject_knowledge(template: str, session) -> str`。

---

## 二、提示词模板化

### 改造方式

现有 `_build_story_prompt()` 和 `_build_chapter_prompt()` 是硬编码 f-string。改为：

1. 系统启动时加载默认模板，存入 `prompts` 表（如果不存在）
2. `generate_story()` 时从 DB 读取模板，`string.Template.substitute()` 替换变量
3. 替换后再 `inject_knowledge()` 注入知识库

### 数据模型

```
Prompt {
    id: UUID
    name: str (unique)           # e.g. "story-generation", "chapter-outline"
    description: Optional[str]
    template: str                 # 支持 $variable 和 @KB{name=...}
    version: int = 1
    built_in: bool = False
    created_at, updated_at
}
```

### 内置模板

**story-generation**: 
```
你是一位专业的中文故事开发者。请将以下灵感扩展为完整的故事大纲。

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

请返回以下结构的 JSON...
```

**chapter-outline**: 同上风格。

---

## 三、Story Schema 扩展

### 新增字段

在现有 schema 基础上增加 NovelForge 风格的字段：

```python
# 现有: logline, synopsis, worldbuilding, characters, themes, plot_points
# 新增:
"title_suggestions": ["备选书名1", ...],     # NovelForge 的"作品标签"
"target_audience": "目标读者群",
"style_tags": ["热血", "轻松", ...],         # 风格标签
"word_count_estimate": 50000,                 # 预估总字数
"gpen_finger_detail": "...",                  # 金手指详细设定
"power_system": {                              # 力量体系详情
    "name": "修仙",
    "stages": ["炼气", "筑基", ...],
    "description": "..."
},
"world_map_hints": "世界地图概述",            # 地图描述
"prologue_preview": "楔子/开篇预览文本"      # NovelForge 的"一句话梗概"+开篇预览
```

这些字段都是 optional，不影响现有逻辑。

---

## 四、角色关系图谱（轻量 SQLite 方案）

参考 NovelForge v0.9.1 起的关系图设计，用 SQLite 表存储角色、地点、组织之间的关联。后续多集联动时可直接升级 Neo4j。

### 数据模型

```
Relation {
    id: UUID
    project_id: UUID (FK → projects)
    source_type: str    # "character" | "location" | "organization" | "item"
    source_id: UUID      # 可以是 character_card.id 或 story characters 数组中的索引
    relation_type: str   # 见下方枚举
    target_type: str
    target_id: UUID
    properties: JSON     # 可选附加属性 {"since_chapter": 3, "detail": "..."}
    created_at, updated_at
}
```

### 关系类型枚举

| relation_type | 含义 | 反向 |
|---|---|---|
| `mentor_of` | A 是 B 的师父 | `student_of` |
| `rival_of` | A 与 B 是竞争关系 | 双向 |
| `lover_of` | A 与 B 是恋人 | 双向 |
| `friend_of` | A 与 B 是朋友 | 双向 |
| `enemy_of` | A 与 B 是仇人 | 双向 |
| `family_of` | A 是 B 的家人 | 双向 |
| `serves` | A 效忠于 B (组织/人物) | `commands` |
| `located_in` | A (人物/组织) 位于 B (地点) | `contains` |
| `owns` | A 拥有 B (物品) | `owned_by` |

### API 端点

```
GET    /api/v1/projects/{id}/relations                    # 全部关系
GET    /api/v1/projects/{id}/relations?source_type=character&source_id=xxx  # 某人相关
POST   /api/v1/projects/{id}/relations                    # 创建
DELETE /api/v1/projects/{id}/relations/{rel_id}          # 删除
```

### 上下文注入

在生成章节/剧本时，自动注入当前章节涉及角色的关系图：

```
story_generator_service 的 generate_chapter_outline() 中：
1. 从 story.characters 中提取角色名
2. 查询 relations 表找出所有关联关系
3. 将关系概要注入到章节大纲生成的 context_info 参数中
```

---

## 五、文件变更清单（更新）

### 新增文件
1. `backend/app/models/knowledge.py` — Knowledge 模型
2. `backend/app/models/prompt.py` — Prompt 模型
3. `backend/app/models/relation.py` — Relation 模型
4. `backend/app/db/knowledge_crud.py` — CRUD
5. `backend/app/db/prompt_crud.py` — CRUD
6. `backend/app/db/relation_crud.py` — CRUD
7. `backend/app/services/knowledge_service.py` — 注入逻辑
8. `backend/app/services/prompt_service.py` — 模板渲染
9. `backend/app/api/routes/knowledge.py` — API 路由
10. `backend/app/api/routes/relations.py` — 关系图 API
11. `backend/app/db/migrations/versions/014_add_knowledge_prompt_relation.py` — 迁移（合并）
12. `backend/app/db/seed_data/knowledge_seeds.py` — 种子数据
13. `backend/tests/test_knowledge.py` — 测试
14. `backend/tests/test_prompt_template.py` — 测试
15. `backend/tests/test_relations.py` — 测试

### 修改文件
1. `backend/app/models/story.py` — 扩展字段
2. `backend/app/schemas/story.py` — 扩展 Schema
3. `backend/app/services/generator_services/story_generator_service.py` — 用模板+知识库替换硬编码
4. `backend/app/main.py` — 注册 knowledge + relations 路由
5. `backend/app/db/migrations/versions/015_extend_story_fields.py` — 迁移
6. `backend/tests/test_story_generator.py` — 更新测试

### 不碰的文件
- 前端所有文件（Phase B 再做）
- workflow_service.py
- 工作流 Tab 的 8 个阶段
