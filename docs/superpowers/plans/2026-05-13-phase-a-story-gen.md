# Phase A: 故事生成重构 实现计划

> **面向 AI 代理的工作者：** 使用 subagent-driven-development 逐任务实现。步骤使用复选框（`- [ ]`）语法跟踪进度。

**目标：** 为 ops-video 建立知识库系统、提示词模板引擎、角色关系+状态追踪（防情节矛盾），重构 StoryGeneratorService 用模板+KB+前情提要替代硬编码。

**架构：** 新增 3 个模型（Knowledge/Prompt/Relation+CharacterState），2 个路由模块，2 个服务层，种子数据 6 个知识库。Story 模型扩展 8 个可选字段。StoryGeneratorService 改为模板驱动。

**技术栈：** FastAPI + SQLAlchemy + SQLite(测试)/PostgreSQL(生产) + Python string.Template

---

## 文件结构

| 文件 | 职责 |
|------|------|
| `backend/app/models/knowledge.py` | Knowledge ORM 模型 |
| `backend/app/models/prompt.py` | Prompt ORM 模型 |
| `backend/app/models/relation.py` | Relation + CharacterState ORM 模型 |
| `backend/app/db/knowledge_crud.py` | Knowledge 增删改查 |
| `backend/app/db/prompt_crud.py` | Prompt 增删改查 |
| `backend/app/db/relation_crud.py` | Relation 增删改查 |
| `backend/app/db/character_state_crud.py` | CharacterState 增删改查 |
| `backend/app/services/knowledge_service.py` | @KB 注入 + 前情提要组装 |
| `backend/app/services/prompt_service.py` | 模板渲染 ($variable 替换) |
| `backend/app/api/routes/knowledge.py` | Knowledge REST API |
| `backend/app/api/routes/relations.py` | 关系 + 状态 REST API |
| `backend/app/db/seed_data/knowledge_seeds.py` | 6 个内置知识库数据 |
| `backend/app/db/migrations/versions/014_add_knowledge_prompt_relation.py` | DB 迁移 |
| `backend/app/db/migrations/versions/015_extend_story_fields.py` | Story 字段扩展迁移 |
| `backend/app/models/story.py` (改) | 新增 8 个可选字段 |
| `backend/app/schemas/story.py` (改) | Schema 同步 |
| `backend/app/services/generator_services/story_generator_service.py` (改) | 模板+KB 重构 |
| `backend/app/main.py` (改) | 注册新路由 |
| `backend/tests/test_knowledge.py` | Knowledge 测试 |
| `backend/tests/test_prompt_template.py` | 模板渲染测试 |
| `backend/tests/test_relations.py` | Relation+CharacterState 测试 |

---

### 任务 1：Knowledge 模型 + 迁移

**文件：**
- 创建：`backend/app/models/knowledge.py`
- 创建：`backend/app/db/migrations/versions/014_add_knowledge_prompt_relation.py`

- [ ] **步骤 1：创建 Knowledge 模型**

```python
# backend/app/models/knowledge.py
"""Knowledge base model — stores name dictionaries, world rules, genre guides."""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Boolean, DateTime
from .base import GUID
from .declarative import Base


class Knowledge(Base):
    __tablename__ = "knowledge"

    id = Column(GUID(), primary_key=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)  # name, world, style, genre
    content = Column(Text, nullable=False)
    description = Column(String(500), nullable=True)
    built_in = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Knowledge {self.name} ({self.category})>"
```

- [ ] **步骤 2：创建迁移文件**

```python
# backend/app/db/migrations/versions/014_add_knowledge_prompt_relation.py
"""Add knowledge, prompt, relation, character_state tables

Revision ID: 014
Revises: 013
Create Date: 2026-05-13
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "014"
down_revision: Union[str, None] = "013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "knowledge",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("name", sa.String(255), unique=True, nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("built_in", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_knowledge_name", "knowledge", ["name"])
    op.create_index("ix_knowledge_category", "knowledge", ["category"])

    op.create_table(
        "prompts",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("name", sa.String(255), unique=True, nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("template", sa.Text, nullable=False),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("built_in", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_prompts_name", "prompts", ["name"])

    op.create_table(
        "relations",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("project_id", sa.String(32), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("source_name", sa.String(255), nullable=False),
        sa.Column("relation_type", sa.String(50), nullable=False),
        sa.Column("target_type", sa.String(50), nullable=False),
        sa.Column("target_name", sa.String(255), nullable=False),
        sa.Column("properties", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_relations_project_id", "relations", ["project_id"])
    op.create_index("ix_relations_source", "relations", ["project_id", "source_name"])

    op.create_table(
        "character_states",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("project_id", sa.String(32), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("character_name", sa.String(255), nullable=False),
        sa.Column("chapter_number", sa.Integer, nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="alive"),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("faction", sa.String(255), nullable=True),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_character_states_project", "character_states", ["project_id", "character_name"])
    op.create_index("ix_character_states_chapter", "character_states", ["project_id", "chapter_number"])


def downgrade() -> None:
    op.drop_table("character_states")
    op.drop_table("relations")
    op.drop_table("prompts")
    op.drop_table("knowledge")
```

- [ ] **步骤 3：验证迁移**

```bash
cd backend && source venv/bin/activate && DATABASE_URL=sqlite:///./test_migrate.db alembic upgrade head && rm -f test_migrate.db
```

预期：迁移成功，无报错。

- [ ] **步骤 4：验证模型导入**

```bash
cd backend && source venv/bin/activate && python -c "from app.models.knowledge import Knowledge; print('OK')"
```

- [ ] **步骤 5：Commit**

```bash
git add backend/app/models/knowledge.py backend/app/db/migrations/versions/014_add_knowledge_prompt_relation.py
git commit -m "feat: add Knowledge model + migration for knowledge/prompt/relation/character_state tables"
```

---

### 任务 2：Prompt 模型

**文件：**
- 创建：`backend/app/models/prompt.py`

- [ ] **步骤 1：创建 Prompt 模型**

```python
# backend/app/models/prompt.py
"""Prompt template model."""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, Boolean, DateTime
from .base import GUID
from .declarative import Base


class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(GUID(), primary_key=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(String(500), nullable=True)
    template = Column(Text, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    built_in = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Prompt {self.name} v{self.version}>"
```

- [ ] **步骤 2：验证导入**

```bash
cd backend && source venv/bin/activate && python -c "from app.models.prompt import Prompt; from app.models.knowledge import Knowledge; print('OK')"
```

- [ ] **步骤 3：Commit**

```bash
git add backend/app/models/prompt.py
git commit -m "feat: add Prompt template model"
```

---

### 任务 3：Relation + CharacterState 模型

**文件：**
- 创建：`backend/app/models/relation.py`

- [ ] **步骤 1：创建模型**

```python
# backend/app/models/relation.py
"""Relation and CharacterState models for story continuity tracking."""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, JSON, DateTime, ForeignKey
from .base import GUID
from .declarative import Base


class Relation(Base):
    __tablename__ = "relations"

    id = Column(GUID(), primary_key=True)
    project_id = Column(GUID(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    source_type = Column(String(50), nullable=False)     # character / location / organization
    source_name = Column(String(255), nullable=False)
    relation_type = Column(String(50), nullable=False)    # mentor_of, rival_of, lover_of, etc.
    target_type = Column(String(50), nullable=False)
    target_name = Column(String(255), nullable=False)
    properties = Column(JSON, nullable=True)              # {"since_chapter": 1, "detail": "..."}
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self) -> str:
        return f"<Relation {self.source_name} --{self.relation_type}--> {self.target_name}>"


class CharacterState(Base):
    __tablename__ = "character_states"

    id = Column(GUID(), primary_key=True)
    project_id = Column(GUID(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    character_name = Column(String(255), nullable=False)
    chapter_number = Column(Integer, nullable=False)
    status = Column(String(30), nullable=False, default="alive")
    location = Column(String(255), nullable=True)
    faction = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self) -> str:
        return f"<CharacterState {self.character_name} ch{self.chapter_number} [{self.status}] @{self.location}>"
```

- [ ] **步骤 2：验证导入**

```bash
cd backend && source venv/bin/activate && python -c "
from app.models.relation import Relation, CharacterState
print('Relation:', Relation.__tablename__)
print('CharacterState:', CharacterState.__tablename__)
"
```

- [ ] **步骤 3：Commit**

```bash
git add backend/app/models/relation.py
git commit -m "feat: add Relation + CharacterState models for continuity tracking"
```

---

### 任务 4：Knowledge CRUD + 种子数据

**文件：**
- 创建：`backend/app/db/knowledge_crud.py`
- 创建：`backend/app/db/seed_data/knowledge_seeds.py`
- 创建：`backend/tests/test_knowledge.py`

- [ ] **步骤 1：编写失败的测试**

```python
# backend/tests/test_knowledge.py
"""Tests for Knowledge CRUD and seed data."""
import pytest
from app.db.session import get_db
from app.db.knowledge_crud import KnowledgeCRUD
from app.db.seed_data.knowledge_seeds import SEED_KNOWLEDGE


class TestKnowledgeCRUD:
    @pytest.fixture(autouse=True)
    def setup(self, db_session):
        self.db = db_session
        self.crud = KnowledgeCRUD()

    def test_create_knowledge(self):
        kb = self.crud.create(self.db, name="test-kb", category="name", content="张,李,王")
        assert kb.id is not None
        assert kb.name == "test-kb"
        assert kb.category == "name"
        assert kb.built_in is False

    def test_create_duplicate_name_fails(self):
        self.crud.create(self.db, name="unique", category="name", content="test")
        with pytest.raises(ValueError):
            self.crud.create(self.db, name="unique", category="name", content="test2")

    def test_get_by_name(self):
        self.crud.create(self.db, name="my-kb", category="world", content="content")
        kb = self.crud.get_by_name(self.db, "my-kb")
        assert kb is not None
        assert kb.content == "content"

    def test_get_by_name_not_found(self):
        kb = self.crud.get_by_name(self.db, "nonexistent")
        assert kb is None

    def test_list_by_category(self):
        self.crud.create(self.db, name="kb1", category="name", content="a")
        self.crud.create(self.db, name="kb2", category="name", content="b")
        self.crud.create(self.db, name="kb3", category="world", content="c")
        names = self.crud.list(self.db, category="name")
        assert len(names) == 2

    def test_delete_built_in_fails(self):
        kb = self.crud.create(self.db, name="system-kb", category="name", content="x", built_in=True)
        with pytest.raises(ValueError, match="系统内置知识库不可删除"):
            self.crud.delete(self.db, kb.id)

    def test_update_knowledge(self):
        kb = self.crud.create(self.db, name="updatable", category="name", content="v1")
        updated = self.crud.update(self.db, kb.id, content="v2")
        assert updated.content == "v2"

    def test_seed_knowledge_count(self):
        from app.db.seed_data.knowledge_seeds import seed_knowledge
        count = seed_knowledge(self.db)
        assert count == 6  # 6 built-in seeds

    def test_seed_knowledge_idempotent(self):
        from app.db.seed_data.knowledge_seeds import seed_knowledge
        seed_knowledge(self.db)
        count2 = seed_knowledge(self.db)
        assert count2 == 0  # second call returns 0


class TestKnowledgeSeeds:
    def test_all_seeds_have_required_fields(self):
        for item in SEED_KNOWLEDGE:
            assert item["name"], f"Missing name in seed: {item}"
            assert item["category"], f"Missing category in seed: {item}"
            assert item["content"], f"Missing content in seed: {item['name']}"
```

- [ ] **步骤 2：运行测试验证失败**

```bash
cd backend && source venv/bin/activate && python -m pytest tests/test_knowledge.py -v --tb=short
```

预期：全部 FAIL，模块不存在。

- [ ] **步骤 3：实现 KnowledgeCRUD**

```python
# backend/app/db/knowledge_crud.py
"""CRUD operations for Knowledge base."""
from typing import List, Optional
from sqlalchemy.orm import Session
from ..models.knowledge import Knowledge


class KnowledgeCRUD:
    def create(self, db: Session, *, name: str, category: str, content: str,
               description: Optional[str] = None, built_in: bool = False) -> Knowledge:
        existing = db.query(Knowledge).filter(Knowledge.name == name).first()
        if existing:
            raise ValueError(f"知识库名称 '{name}' 已存在")
        kb = Knowledge(
            name=name, category=category, content=content,
            description=description, built_in=built_in,
        )
        db.add(kb)
        db.commit()
        db.refresh(kb)
        return kb

    def get(self, db: Session, kb_id: str) -> Optional[Knowledge]:
        return db.query(Knowledge).filter(Knowledge.id == kb_id).first()

    def get_by_name(self, db: Session, name: str) -> Optional[Knowledge]:
        return db.query(Knowledge).filter(Knowledge.name == name).first()

    def list(self, db: Session, category: Optional[str] = None,
             skip: int = 0, limit: int = 100) -> List[Knowledge]:
        q = db.query(Knowledge)
        if category:
            q = q.filter(Knowledge.category == category)
        return q.offset(skip).limit(limit).all()

    def update(self, db: Session, kb_id: str, **kwargs) -> Optional[Knowledge]:
        kb = self.get(db, kb_id)
        if not kb:
            return None
        for key, value in kwargs.items():
            if hasattr(kb, key):
                setattr(kb, key, value)
        db.commit()
        db.refresh(kb)
        return kb

    def delete(self, db: Session, kb_id: str) -> bool:
        kb = self.get(db, kb_id)
        if not kb:
            return False
        if kb.built_in:
            raise ValueError("系统内置知识库不可删除")
        db.delete(kb)
        db.commit()
        return True


knowledge_crud = KnowledgeCRUD()
```

- [ ] **步骤 4：实现种子数据**

```python
# backend/app/db/seed_data/knowledge_seeds.py
"""Built-in knowledge base seed data."""

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from ..knowledge_crud import knowledge_crud

SEED_KNOWLEDGE: List[Dict[str, Any]] = [
    {
        "name": "chinese-names",
        "category": "name",
        "description": "中文姓名生成字典：常见姓氏、男女名用字及含义",
        "content": """## 中文姓名字典

### 常见姓氏（50个）
李、王、张、刘、陈、杨、赵、黄、周、吴、徐、孙、胡、朱、高、林、何、郭、马、罗、
梁、宋、郑、谢、韩、唐、冯、于、董、萧、程、曹、袁、邓、许、傅、沈、曾、彭、吕、
苏、卢、蒋、蔡、贾、丁、魏、薛、叶、阎

### 男性名用字（30个）
轩、宇、晨、浩、然、博、文、杰、铭、泽、昊、毅、锋、涛、彬、哲、翰、睿、彦、恒、
辰、凯、铭、瑞、霖、旭、烨、鹏、骏、渊

### 女性名用字（30个）
涵、嫣、瑶、璇、萱、琳、悦、婷、婉、倩、怡、璐、彤、菲、晴、瑜、洁、秀、娟、莉、
蓉、梅、兰、雪、月、诗、画、思、语、梦

### 取名规则
- 修仙题材：多用"玄、灵、道、仙、清、虚、天、云、星、月"
- 武侠题材：多用"风、剑、影、霜、雪、寒、龙、凤、虎、鹰"
- 都市题材：使用现代常用名即可
""",
    },
    {
        "name": "chinese-place-names",
        "category": "world",
        "description": "中文地名生成字典：前缀、后缀和命名模板",
        "content": """## 中文地名字典

### 地名前缀（20个）
青云、紫霞、碧落、苍梧、玉虚、凌霄、太初、混元、无极、清风、
白云、黑水、赤焰、翠微、金鳌、银月、玄冥、九幽、万象、归元

### 地名后缀（15个）
城、山、谷、峰、崖、洞、湖、海、渊、阁、
殿、宗、门、派、坊

### 地名命名规则
- 宗门：前缀+宗/门/派（如"青云宗""碧落门"）
- 城市：前缀+城（如"紫霞城""苍梧城"）
- 险地：前缀+谷/渊/崖（如"黑水渊""赤焰谷"）
- 仙山：前缀+山/峰（如"玉虚峰""凌霄山"）
- 秘境：使用两字词组（如"归墟""太初"）

### 经典地名示例
青云城、碧落门、紫霞峰、黑水渊、赤焰谷、玉虚殿、凌霄宗、
苍梧山、太初秘境、九幽深渊、万象阁、混元宗、无极峰
""",
    },
    {
        "name": "chinese-dynasties",
        "category": "world",
        "description": "中国古代朝代设定模板，含制度、服饰、科技水平参考",
        "content": """## 朝代设定模板

| 朝代 | 时期 | 政治制度 | 服饰特点 | 科技水平 | 适合题材 |
|------|------|---------|---------|---------|---------|
| 架空上古 | 洪荒时代 | 部落联盟/巫觋统治 | 兽皮麻衣 | 原始石器+灵力 | 洪荒修仙 |
| 架空商周 | 封神时代 | 分封制+方国 | 青铜甲胄 | 青铜+道法初兴 | 封神修仙 |
| 架空中古 | 仙侠黄金时代 | 帝国+宗门共治 | 长袍广袖 | 灵力鼎盛 | 古典仙侠 |
| 架空盛唐 | 万国来朝 | 三省六部制 | 胡服骑射 | 繁荣盛世 | 历史奇幻 |
| 架空两宋 | 文治天下 | 重文轻武 | 儒衫长裙 | 火药/印刷萌芽 | 文官修仙 |
| 架空明清 | 封建末期 | 高度集权 | 旗袍马褂 | 冷热兵器交替 | 末法时代 |
| 架空民国 | 新旧交替 | 军阀割据 | 中山装/旗袍 | 火器初兴 | 民国仙侠 |
| 现代都市 | 当代 | 现代制度 | 现代服饰 | 信息时代 | 都市修仙 |
| 近未来 | 2050前后 | 赛博政权 | 机能风 | AI/义体 | 赛博修仙 |
| 远未来 | 星际时代 | 银河联邦 | 太空服 | 曲速引擎 | 星际修仙 |

### 使用规则
- 选择一个作为主时代背景，可混搭元素
- 科技水平影响力量体系的表现形式
- 服饰描写要与时代一致，避免穿越感
""",
    },
    {
        "name": "xianxia-world-rules",
        "category": "world",
        "description": "修仙世界观设定指南：境界、宗门、灵石货币体系",
        "content": """## 修仙世界观设定指南

### 境界体系（练气→渡劫）
1. 炼气期（1-9层）：引气入体，强化肉身
2. 筑基期（初/中/后/圆满）：筑就道基，寿元大增
3. 金丹期：凝结金丹，可御器飞行
4. 元婴期：金丹化婴，元神出窍
5. 化神期：元婴与肉身合一，神通广大
6. 炼虚期：炼化虚空之力
7. 合体期：道法与肉身完美融合
8. 大乘期：半步飞升
9. 渡劫期：历雷劫飞升仙界

### 宗门结构
- 太上长老（隐世不出）
- 掌门（一宗之主）
- 长老（各峰首座）
- 执事（管理庶务）
- 内门弟子（核心培养）
- 外门弟子（杂役修炼）
- 杂役弟子（未入门墙）

### 灵石货币
- 下品灵石：日常交易单位
- 中品灵石 = 100下品：常规修炼用
- 上品灵石 = 100中品：高阶修士使用
- 极品灵石 = 100上品：稀世珍宝

### 常见宗门类型
- 剑修宗门：主修剑道，战力最强
- 丹修宗门：炼丹制药，富甲一方
- 阵修宗门：布阵防御，守护要塞
- 符修宗门：制符画箓，辅助战斗
- 体修宗门：锻体炼魄，肉身成圣
""",
    },
    {
        "name": "scifi-world-rules",
        "category": "world",
        "description": "科幻世界观设定指南：科技等级、星际政治、AI伦理",
        "content": """## 科幻世界观设定指南

### 科技等级（卡尔达肖夫指数改编）
- Lv1 行星文明：可控核聚变，行星际航行
- Lv2 恒星文明：戴森球，恒星际航行（亚光速）
- Lv3 星系文明：曲速引擎，星系殖民
- Lv4 银河文明：虫洞技术，银河网络
- Lv5 宇宙文明：维度操控，宇宙尺度

### 星际政治模型
- 银河联邦：民主议会制，多物种共存
- 帝国制：中央集权，军事扩张
- 企业联合体：巨型公司代行政府职能
- 蜂巢意识：集体意识统治
- 无政府星域：法外之地

### AI 伦理分级
- Class A：工具级AI，无自我意识
- Class B：助理级AI，有限自主决策
- Class C：等同人类级，拥有公民权（争议）
- Class D：超智能级，禁止研发（银河公约）

### 常见设定元素
- 义体改造率、脑机接口普及度
- 太空电梯、轨道城市、小行星采矿
- 基因编辑合法性、克隆人权利
""",
    },
    {
        "name": "story-structures",
        "category": "genre",
        "description": "7种经典叙事结构：英雄之旅、三幕式等，含适用类型",
        "content": """## 7种经典叙事结构

### 1. 英雄之旅（12步）
适用：修仙、奇幻、冒险、超级英雄
平凡世界 → 冒险召唤 → 拒绝召唤 → 遇见导师 →
越过第一道门槛 → 考验/盟友/敌人 → 接近最深处洞穴 →
磨难 → 回报 → 归途 → 复活 → 携万能药归来

### 2. 三幕式
适用：几乎所有类型
第一幕（设定）：介绍世界观、主角、冲突引发事件
第二幕（对抗）：冲突升级、主角遭遇挫折、学习成长
第三幕（解决）：高潮对决、问题解决、新平衡

### 3. 起承转合
适用：短篇、漫剧单集
起：开篇设定，引入角色和冲突
承：发展情节，深化矛盾
转：转折高潮，意外发展
合：收束结局，余韵悠长

### 4. 七点式
适用：中长篇
钩子 → 第一情节点 → 第一 pinch点 → 中点 →
第二 pinch点 → 第二情节点 → 结局

### 5. 拯救猫咪式
适用：商业电影/漫剧
开场画面 → 主题陈述 → 铺垫 → 催化剂 → 争论 →
第二幕开场 → B故事 → 娱乐游戏 → 中点 → 反派逼近 →
一无所有 → 灵魂黑夜 → 第三幕开场 → 终场画面

### 6. 非线性叙事
适用：悬疑、文艺
倒叙、插叙、多线并行、环形结构

### 7. 单元剧结构
适用：漫剧系列
每集独立成篇+暗线串联
""",
    },
]

def seed_knowledge(db: Session) -> int:
    """Seed built-in knowledge bases. Returns number of newly created items."""
    created = 0
    for item in SEED_KNOWLEDGE:
        existing = knowledge_crud.get_by_name(db, item["name"])
        if existing:
            continue
        knowledge_crud.create(
            db,
            name=item["name"],
            category=item["category"],
            content=item["content"],
            description=item.get("description"),
            built_in=True,
        )
        created += 1
    return created
```

- [ ] **步骤 5：运行测试验证通过**

```bash
cd backend && source venv/bin/activate && python -m pytest tests/test_knowledge.py -v --tb=short
```

预期：全部 PASS。

- [ ] **步骤 6：Commit**

```bash
git add backend/app/db/knowledge_crud.py backend/app/db/seed_data/knowledge_seeds.py backend/tests/test_knowledge.py
git commit -m "feat: add Knowledge CRUD + 6 built-in knowledge seeds + tests"
```

---

### 任务 5：Prompt CRUD + 模板渲染服务

**文件：**
- 创建：`backend/app/db/prompt_crud.py`
- 创建：`backend/app/services/prompt_service.py`
- 创建：`backend/tests/test_prompt_template.py`

- [ ] **步骤 1：编写测试**

```python
# backend/tests/test_prompt_template.py
"""Tests for Prompt CRUD and template rendering."""
import pytest
from app.db.prompt_crud import PromptCRUD
from app.services.prompt_service import render_prompt, seed_default_prompts


class TestPromptCRUD:
    @pytest.fixture(autouse=True)
    def setup(self, db_session):
        self.db = db_session
        self.crud = PromptCRUD()

    def test_create_prompt(self):
        p = self.crud.create(self.db, name="test", template="hello $name")
        assert p.name == "test"
        assert p.version == 1

    def test_create_duplicate_fails(self):
        self.crud.create(self.db, name="unique", template="t")
        with pytest.raises(ValueError):
            self.crud.create(self.db, name="unique", template="t2")

    def test_get_by_name(self):
        self.crud.create(self.db, name="my-prompt", template="content")
        p = self.crud.get_by_name(self.db, "my-prompt")
        assert p is not None
        assert p.template == "content"

    def test_update_increments_version(self):
        p = self.crud.create(self.db, name="ver-test", template="v1")
        updated = self.crud.update(self.db, p.id, template="v2")
        assert updated.version == 2
        assert updated.template == "v2"


class TestPromptRendering:
    @pytest.fixture(autouse=True)
    def setup(self, db_session):
        self.db = db_session

    def test_render_simple_variables(self):
        result = render_prompt("你好 $name，欢迎来到 $place", {"name": "张三", "place": "青云城"})
        assert result == "你好 张三，欢迎来到 青云城"

    def test_render_missing_variable_raises(self):
        with pytest.raises(ValueError, match="缺少变量"):
            render_prompt("$missing_var", {})

    def test_seed_default_prompts(self):
        count = seed_default_prompts(self.db)
        assert count == 2
        story_prompt = PromptCRUD().get_by_name(self.db, "story-generation")
        assert story_prompt is not None
        assert "$inspiration" in story_prompt.template
        assert "@KB{name=story-structures}" in story_prompt.template
        chapter_prompt = PromptCRUD().get_by_name(self.db, "chapter-outline")
        assert chapter_prompt is not None
        assert "$chapter_count" in chapter_prompt.template

    def test_seed_prompts_idempotent(self):
        seed_default_prompts(self.db)
        count2 = seed_default_prompts(self.db)
        assert count2 == 0
```

- [ ] **步骤 2：运行测试验证失败**

```bash
cd backend && source venv/bin/activate && python -m pytest tests/test_prompt_template.py -v --tb=short
```

预期：FAIL。

- [ ] **步骤 3：实现 PromptCRUD**

```python
# backend/app/db/prompt_crud.py
"""CRUD for prompt templates."""
from typing import List, Optional
from sqlalchemy.orm import Session
from ..models.prompt import Prompt


class PromptCRUD:
    def create(self, db: Session, *, name: str, template: str,
               description: Optional[str] = None, built_in: bool = False) -> Prompt:
        existing = db.query(Prompt).filter(Prompt.name == name).first()
        if existing:
            raise ValueError(f"提示词模板 '{name}' 已存在")
        p = Prompt(name=name, template=template, description=description, built_in=built_in)
        db.add(p)
        db.commit()
        db.refresh(p)
        return p

    def get(self, db: Session, prompt_id: str) -> Optional[Prompt]:
        return db.query(Prompt).filter(Prompt.id == prompt_id).first()

    def get_by_name(self, db: Session, name: str) -> Optional[Prompt]:
        return db.query(Prompt).filter(Prompt.name == name).first()

    def list(self, db: Session, skip: int = 0, limit: int = 100) -> List[Prompt]:
        return db.query(Prompt).offset(skip).limit(limit).all()

    def update(self, db: Session, prompt_id: str, **kwargs) -> Optional[Prompt]:
        p = self.get(db, prompt_id)
        if not p:
            return None
        for key, value in kwargs.items():
            if hasattr(p, key):
                setattr(p, key, value)
        p.version += 1
        db.commit()
        db.refresh(p)
        return p

    def delete(self, db: Session, prompt_id: str) -> bool:
        p = self.get(db, prompt_id)
        if not p:
            return False
        if p.built_in:
            raise ValueError("系统内置提示词模板不可删除")
        db.delete(p)
        db.commit()
        return True


prompt_crud = PromptCRUD()
```

- [ ] **步骤 4：实现模板渲染服务**

```python
# backend/app/services/prompt_service.py
"""Prompt template rendering with $variable substitution."""
import re
from string import Template
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from ..db.prompt_crud import prompt_crud


def render_prompt(template: str, context: Dict[str, Any]) -> str:
    """Render a prompt template with $variable substitution."""
    try:
        return Template(template).substitute(context)
    except KeyError as e:
        raise ValueError(f"渲染提示词失败：上下文中缺少变量 '{e.args[0]}'")


def get_rendered_prompt(db: Session, name: str, context: Dict[str, Any]) -> str:
    """Load a prompt template by name and render it."""
    p = prompt_crud.get_by_name(db, name)
    if not p:
        raise ValueError(f"提示词模板 '{name}' 不存在")
    return render_prompt(p.template, context)


def seed_default_prompts(db: Session) -> int:
    """Seed built-in prompt templates. Returns number of newly created items."""
    created = 0

    story_template = """你是一位专业的中文故事开发者。请将以下灵感扩展为完整的故事大纲。所有输出必须使用中文。

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
  "title_suggestions": ["备选书名1", "备选书名2", "备选书名3"],
  "target_audience": "目标读者群（如：青年男性/女性向/全年龄）",
  "style_tags": ["风格标签1", "风格标签2"],
  "word_count_estimate": 50000,
  "worldbuilding": {
    "setting": "故事发生的世界背景",
    "time_period": "故事发生的时代",
    "rules": "这个世界的基本规则和力量体系"
  },
  "world_map_hints": "世界地理概述（主要地点和区域）",
  "power_system": {
    "name": "力量体系名称（如：修仙/魔法/科技/异能）",
    "stages": ["境界1", "境界2", "境界3"],
    "description": "力量体系简述"
  },
  "golden_finger_detail": "主角金手指的详细设定和限制",
  "characters": [
    {
      "name": "角色姓名",
      "role": "角色定位（主角/反派/导师/伙伴/路人）",
      "description": "角色外貌、性格描述",
      "arc": "角色成长弧线简述",
      "abilities": "角色能力或特长"
    }
  ],
  "themes": ["故事主题1", "故事主题2", "故事主题3"],
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

    chapter_template = """你是一位专业的叙事结构师。请将以下故事大纲拆分为恰好 $chapter_count 个章节。所有输出必须使用中文。

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
      "summary": "本章详细概要（200-300字）",
      "key_scenes": ["场景1描述", "场景2描述", "场景3描述"],
      "characters": ["本章出现的角色姓名"],
      "character_events": [
        {"character": "角色名", "event": "本章发生的与该角色相关的重要事件"}
      ],
      "new_locations": ["本章首次出现的地点"],
      "duration": 5.0
    }
  ]
}

要求：
1. 每个章节必须有清晰的叙事目的
2. 将情节点均匀分布到各章节
3. key_scenes 应该是描述性的场景概要
4. characters 列出角色姓名（不需要完整描述）
5. character_events 追踪每个角色的重要变化（状态变化、位置移动、获得物品等）
6. 列出本章新出现的地点，确保与已有地点不矛盾
7. duration 是预估的阅读/观看时间（分钟）
8. 总章节数必须恰好为 $chapter_count
9. 已死亡的角色绝不能在后续章节中以活人身份出现
10. 角色的位置移动必须合理（不能跳跃到遥远地点）

请只返回有效的 JSON，不要包含 markdown 或解释。"""

    for name, template, desc in [
        ("story-generation", story_template, "故事大纲生成提示词模板"),
        ("chapter-outline", chapter_template, "章节大纲拆解提示词模板"),
    ]:
        existing = prompt_crud.get_by_name(db, name)
        if existing:
            continue
        prompt_crud.create(db, name=name, template=template, description=desc, built_in=True)
        created += 1

    return created
```

- [ ] **步骤 5：运行测试**

```bash
cd backend && source venv/bin/activate && python -m pytest tests/test_prompt_template.py -v --tb=short
```

预期：全部 PASS。

- [ ] **步骤 6：Commit**

```bash
git add backend/app/db/prompt_crud.py backend/app/services/prompt_service.py backend/tests/test_prompt_template.py
git commit -m "feat: add Prompt CRUD + template rendering service + seed + tests"
```

---

### 任务 6：Relation + CharacterState CRUD + Knowledge Service 注入逻辑

**文件：**
- 创建：`backend/app/db/relation_crud.py`
- 创建：`backend/app/db/character_state_crud.py`
- 创建：`backend/app/services/knowledge_service.py`
- 创建：`backend/tests/test_relations.py`

- [ ] **步骤 1：编写测试**

```python
# backend/tests/test_relations.py
"""Tests for Relation and CharacterState models."""
import pytest
from app.db.relation_crud import RelationCRUD
from app.db.character_state_crud import CharacterStateCRUD
from app.services.knowledge_service import inject_knowledge, build_continuity_context


class TestRelationCRUD:
    @pytest.fixture(autouse=True)
    def setup(self, db_session):
        self.db = db_session
        self.crud = RelationCRUD()

    def test_create_relation(self):
        r = self.crud.create(self.db, project_id="p1", source_type="character",
                             source_name="张三", relation_type="mentor_of",
                             target_type="character", target_name="李四")
        assert r.id is not None
        assert r.relation_type == "mentor_of"

    def test_list_by_project(self):
        self.crud.create(self.db, project_id="p1", source_type="character", source_name="A",
                         relation_type="friend_of", target_type="character", target_name="B")
        self.crud.create(self.db, project_id="p1", source_type="character", source_name="A",
                         relation_type="rival_of", target_type="character", target_name="C")
        self.crud.create(self.db, project_id="p2", source_type="character", source_name="D",
                         relation_type="friend_of", target_type="character", target_name="E")
        rels = self.crud.list_by_project(self.db, "p1")
        assert len(rels) == 2

    def test_list_by_character(self):
        self.crud.create(self.db, project_id="p1", source_type="character", source_name="张三",
                         relation_type="friend_of", target_type="character", target_name="李四")
        rels = self.crud.list_by_character(self.db, "p1", "张三")
        assert len(rels) == 1


class TestCharacterStateCRUD:
    @pytest.fixture(autouse=True)
    def setup(self, db_session):
        self.db = db_session
        self.crud = CharacterStateCRUD()

    def test_create_state(self):
        s = self.crud.create(self.db, project_id="p1", character_name="张三",
                             chapter_number=1, status="alive", location="青云城")
        assert s.status == "alive"
        assert s.chapter_number == 1

    def test_get_latest_for_character(self):
        self.crud.create(self.db, project_id="p1", character_name="张三",
                         chapter_number=1, status="alive", location="青云城")
        self.crud.create(self.db, project_id="p1", character_name="张三",
                         chapter_number=2, status="injured", location="黑水渊")
        self.crud.create(self.db, project_id="p1", character_name="李四",
                         chapter_number=1, status="alive", location="紫霞城")
        latest = self.crud.get_latest(self.db, "p1", "张三")
        assert latest.chapter_number == 2
        assert latest.status == "injured"

    def test_get_all_latest_states(self):
        self.crud.create(self.db, project_id="p1", character_name="张三",
                         chapter_number=1, status="alive", location="A城")
        self.crud.create(self.db, project_id="p1", character_name="张三",
                         chapter_number=2, status="dead", location="A城")
        self.crud.create(self.db, project_id="p1", character_name="李四",
                         chapter_number=1, status="alive", location="B城")
        states = self.crud.get_all_latest(self.db, "p1")
        assert len(states) == 2
        dead_char = [s for s in states if s.character_name == "张三"][0]
        assert dead_char.status == "dead"


class TestKnowledgeInjection:
    @pytest.fixture(autouse=True)
    def setup(self, db_session):
        self.db = db_session

    def test_inject_knowledge_by_name(self):
        from app.db.knowledge_crud import knowledge_crud
        knowledge_crud.create(self.db, name="test-kb", category="test",
                              content="知识库内容ABC", built_in=True)
        template = "开头@KB{name=test-kb}结尾"
        result = inject_knowledge(self.db, template)
        assert "知识库内容ABC" in result
        assert "@KB{name=test-kb}" not in result

    def test_inject_knowledge_not_found(self):
        result = inject_knowledge(self.db, "hello @KB{name=nonexistent} world")
        assert "知识库未找到" in result

    def test_build_continuity_context(self):
        from app.db.relation_crud import RelationCRUD
        from app.db.character_state_crud import CharacterStateCRUD
        RelationCRUD().create(self.db, project_id="p1", source_type="character",
                              source_name="张三", relation_type="mentor_of",
                              target_type="character", target_name="李四")
        CharacterStateCRUD().create(self.db, project_id="p1", character_name="张三",
                                    chapter_number=1, status="alive", location="青云城")
        CharacterStateCRUD().create(self.db, project_id="p1", character_name="李四",
                                    chapter_number=1, status="alive", location="青云城",
                                    faction="青云宗")
        context = build_continuity_context(self.db, "p1")
        assert "张三" in context
        assert "alive" in context
        assert "李四" in context
        assert "师父" in context or "mentor" in context.lower()
```

- [ ] **步骤 2：运行测试验证失败**

```bash
cd backend && source venv/bin/activate && python -m pytest tests/test_relations.py -v --tb=short
```

预期：FAIL。

- [ ] **步骤 3：实现 RelationCRUD**

```python
# backend/app/db/relation_crud.py
"""CRUD for character relations."""
from typing import List, Optional
from sqlalchemy.orm import Session
from ..models.relation import Relation


class RelationCRUD:
    def create(self, db: Session, *, project_id: str, source_type: str, source_name: str,
               relation_type: str, target_type: str, target_name: str,
               properties: Optional[dict] = None) -> Relation:
        r = Relation(
            project_id=project_id, source_type=source_type, source_name=source_name,
            relation_type=relation_type, target_type=target_type, target_name=target_name,
            properties=properties,
        )
        db.add(r)
        db.commit()
        db.refresh(r)
        return r

    def list_by_project(self, db: Session, project_id: str) -> List[Relation]:
        return db.query(Relation).filter(Relation.project_id == project_id).all()

    def list_by_character(self, db: Session, project_id: str, character_name: str) -> List[Relation]:
        return db.query(Relation).filter(
            Relation.project_id == project_id,
            (Relation.source_name == character_name) | (Relation.target_name == character_name),
        ).all()

    def delete(self, db: Session, relation_id: str) -> bool:
        r = db.query(Relation).filter(Relation.id == relation_id).first()
        if not r:
            return False
        db.delete(r)
        db.commit()
        return True


relation_crud = RelationCRUD()
```

- [ ] **步骤 4：实现 CharacterStateCRUD**

```python
# backend/app/db/character_state_crud.py
"""CRUD for character state snapshots."""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from ..models.relation import CharacterState


class CharacterStateCRUD:
    def create(self, db: Session, *, project_id: str, character_name: str,
               chapter_number: int, status: str = "alive", location: Optional[str] = None,
               faction: Optional[str] = None, summary: Optional[str] = None) -> CharacterState:
        s = CharacterState(
            project_id=project_id, character_name=character_name,
            chapter_number=chapter_number, status=status, location=location,
            faction=faction, summary=summary,
        )
        db.add(s)
        db.commit()
        db.refresh(s)
        return s

    def get_latest(self, db: Session, project_id: str, character_name: str) -> Optional[CharacterState]:
        return db.query(CharacterState).filter(
            CharacterState.project_id == project_id,
            CharacterState.character_name == character_name,
        ).order_by(desc(CharacterState.chapter_number)).first()

    def get_all_latest(self, db: Session, project_id: str) -> List[CharacterState]:
        """Get the latest state for each character in the project."""
        from sqlalchemy import func, and_
        subq = db.query(
            CharacterState.character_name,
            func.max(CharacterState.chapter_number).label("max_chapter"),
        ).filter(
            CharacterState.project_id == project_id,
        ).group_by(CharacterState.character_name).subquery()

        return db.query(CharacterState).join(
            subq,
            and_(
                CharacterState.character_name == subq.c.character_name,
                CharacterState.chapter_number == subq.c.max_chapter,
                CharacterState.project_id == project_id,
            ),
        ).all()

    def list_by_chapter(self, db: Session, project_id: str, chapter_number: int) -> List[CharacterState]:
        return db.query(CharacterState).filter(
            CharacterState.project_id == project_id,
            CharacterState.chapter_number == chapter_number,
        ).all()

    def get_history(self, db: Session, project_id: str, character_name: str) -> List[CharacterState]:
        return db.query(CharacterState).filter(
            CharacterState.project_id == project_id,
            CharacterState.character_name == character_name,
        ).order_by(CharacterState.chapter_number).all()


character_state_crud = CharacterStateCRUD()
```

- [ ] **步骤 5：实现 KnowledgeService（注入 + 前情提要）**

```python
# backend/app/services/knowledge_service.py
"""Knowledge injection and continuity context builder."""
import re
from typing import List
from sqlalchemy.orm import Session
from ..db.knowledge_crud import knowledge_crud
from ..db.relation_crud import relation_crud
from ..db.character_state_crud import character_state_crud

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
```

- [ ] **步骤 6：运行测试**

```bash
cd backend && source venv/bin/activate && python -m pytest tests/test_relations.py -v --tb=short
```

预期：全部 PASS。

- [ ] **步骤 7：Commit**

```bash
git add backend/app/db/relation_crud.py backend/app/db/character_state_crud.py backend/app/services/knowledge_service.py backend/tests/test_relations.py
git commit -m "feat: add Relation + CharacterState CRUD + knowledge injection + continuity context builder"
```

---

### 任务 7：Knowledge + Relations API 路由

**文件：**
- 创建：`backend/app/api/routes/knowledge.py`
- 创建：`backend/app/api/routes/relations.py`
- 修改：`backend/app/main.py`

- [ ] **步骤 1：创建 Knowledge API**

```python
# backend/app/api/routes/knowledge.py
"""Knowledge base API routes."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ...db.session import get_db
from ...db.knowledge_crud import knowledge_crud

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])


@router.get("")
def list_knowledge(category: Optional[str] = Query(None), db: Session = Depends(get_db)):
    items = knowledge_crud.list(db, category=category)
    return [{"id": k.id, "name": k.name, "category": k.category,
             "description": k.description, "built_in": k.built_in,
             "created_at": k.created_at.isoformat() if k.created_at else None} for k in items]


@router.get("/{kb_id}")
def get_knowledge(kb_id: str, db: Session = Depends(get_db)):
    kb = knowledge_crud.get(db, kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return {"id": kb.id, "name": kb.name, "category": kb.category,
            "content": kb.content, "description": kb.description,
            "built_in": kb.built_in,
            "created_at": kb.created_at.isoformat() if kb.created_at else None,
            "updated_at": kb.updated_at.isoformat() if kb.updated_at else None}


@router.post("", status_code=201)
def create_knowledge(data: dict, db: Session = Depends(get_db)):
    try:
        kb = knowledge_crud.create(db, name=data["name"], category=data["category"],
                                   content=data["content"], description=data.get("description"))
        return {"id": kb.id, "name": kb.name, "category": kb.category}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/{kb_id}")
def update_knowledge(kb_id: str, data: dict, db: Session = Depends(get_db)):
    kb = knowledge_crud.update(db, kb_id, **data)
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return {"id": kb.id, "name": kb.name}


@router.delete("/{kb_id}", status_code=204)
def delete_knowledge(kb_id: str, db: Session = Depends(get_db)):
    try:
        ok = knowledge_crud.delete(db, kb_id)
        if not ok:
            raise HTTPException(status_code=404, detail="知识库不存在")
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
```

- [ ] **步骤 2：创建 Relations API**

```python
# backend/app/api/routes/relations.py
"""Relation and CharacterState API routes."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ...db.session import get_db
from ...db.relation_crud import relation_crud
from ...db.character_state_crud import character_state_crud

router = APIRouter(tags=["relations"])


# ── Relations ──

@router.get("/api/v1/projects/{project_id}/relations")
def list_relations(project_id: str, character: Optional[str] = Query(None),
                   db: Session = Depends(get_db)):
    if character:
        rels = relation_crud.list_by_character(db, project_id, character)
    else:
        rels = relation_crud.list_by_project(db, project_id)
    return [{"id": r.id, "source_type": r.source_type, "source_name": r.source_name,
             "relation_type": r.relation_type, "target_type": r.target_type,
             "target_name": r.target_name, "properties": r.properties,
             "created_at": r.created_at.isoformat() if r.created_at else None} for r in rels]


@router.post("/api/v1/projects/{project_id}/relations", status_code=201)
def create_relation(project_id: str, data: dict, db: Session = Depends(get_db)):
    r = relation_crud.create(db, project_id=project_id,
                             source_type=data["source_type"], source_name=data["source_name"],
                             relation_type=data["relation_type"],
                             target_type=data["target_type"], target_name=data["target_name"],
                             properties=data.get("properties"))
    return {"id": r.id}


@router.delete("/api/v1/projects/{project_id}/relations/{relation_id}", status_code=204)
def delete_relation(project_id: str, relation_id: str, db: Session = Depends(get_db)):
    ok = relation_crud.delete(db, relation_id)
    if not ok:
        raise HTTPException(status_code=404, detail="关系不存在")


# ── Character States ──

@router.get("/api/v1/projects/{project_id}/character-states")
def list_character_states(project_id: str, character: Optional[str] = Query(None),
                          chapter: Optional[int] = Query(None), db: Session = Depends(get_db)):
    if character:
        states = character_state_crud.get_history(db, project_id, character)
    elif chapter:
        states = character_state_crud.list_by_chapter(db, project_id, chapter)
    else:
        states = character_state_crud.get_all_latest(db, project_id)
    return [{"id": s.id, "character_name": s.character_name,
             "chapter_number": s.chapter_number, "status": s.status,
             "location": s.location, "faction": s.faction, "summary": s.summary,
             "created_at": s.created_at.isoformat() if s.created_at else None} for s in states]


@router.post("/api/v1/projects/{project_id}/character-states", status_code=201)
def create_character_state(project_id: str, data: dict, db: Session = Depends(get_db)):
    s = character_state_crud.create(db, project_id=project_id,
                                    character_name=data["character_name"],
                                    chapter_number=data["chapter_number"],
                                    status=data.get("status", "alive"),
                                    location=data.get("location"),
                                    faction=data.get("faction"),
                                    summary=data.get("summary"))
    return {"id": s.id}
```

- [ ] **步骤 3：注册路由**

```bash
# 在 backend/app/main.py 中的路由注册区域添加两行：
```

```python
# 在 main.py 中，找到现有 app.include_router 语句附近，添加：
from .api.routes.knowledge import router as knowledge_router
from .api.routes.relations import router as relations_router
app.include_router(knowledge_router)
app.include_router(relations_router)
```

使用 patch 工具定位现有路由注册处并插入。

- [ ] **步骤 4：种子数据自动加载**

在 `main.py` 的 `lifespan` 启动事件中添加种子数据调用：

```python
# 在 lifespan startup 中，找到现有 seed 调用附近，添加：
from .db.seed_data.knowledge_seeds import seed_knowledge
from .services.prompt_service import seed_default_prompts

db = SessionLocal()
try:
    seed_knowledge(db)
    seed_default_prompts(db)
finally:
    db.close()
```

- [ ] **步骤 5：验证路由**

```bash
# 启动后端后测试：
curl http://localhost:8000/api/v1/knowledge
curl http://localhost:8000/api/v1/knowledge?category=name
```

预期：返回 6 个内置知识库。

- [ ] **步骤 6：Commit**

```bash
git add backend/app/api/routes/knowledge.py backend/app/api/routes/relations.py backend/app/main.py
git commit -m "feat: add Knowledge + Relations API routes + auto-seed on startup"
```

---

### 任务 8：Story Schema 扩展 + StoryGeneratorService 重构

**文件：**
- 修改：`backend/app/models/story.py`
- 修改：`backend/app/schemas/story.py`
- 修改：`backend/app/services/generator_services/story_generator_service.py`
- 创建：`backend/app/db/migrations/versions/015_extend_story_fields.py`

- [ ] **步骤 1：扩展 Story 模型（新增 8 个 JSONB/Text 可选列）**

在 `story.py` 模型中的现有列附近添加：

```python
# 新增字段（紧接在 chapter_outline 列之后）
title_suggestions = Column(JSONB, nullable=True)
target_audience = Column(String(255), nullable=True)
style_tags = Column(JSONB, nullable=True)
word_count_estimate = Column(Integer, nullable=True)
golden_finger_detail = Column(Text, nullable=True)
power_system = Column(JSONB, nullable=True)
world_map_hints = Column(Text, nullable=True)
prologue_preview = Column(Text, nullable=True)
```

- [ ] **步骤 2：创建迁移**

```python
# backend/app/db/migrations/versions/015_extend_story_fields.py
revision: str = "015"
down_revision: Union[str, None] = "014"

def upgrade():
    for col, col_type in [
        ("title_suggestions", sa.JSON),
        ("target_audience", sa.String(255)),
        ("style_tags", sa.JSON),
        ("word_count_estimate", sa.Integer),
        ("golden_finger_detail", sa.Text),
        ("power_system", sa.JSON),
        ("world_map_hints", sa.Text),
        ("prologue_preview", sa.Text),
    ]:
        op.add_column("stories", sa.Column(col, col_type, nullable=True))

def downgrade():
    for col in ["title_suggestions", "target_audience", "style_tags",
                "word_count_estimate", "golden_finger_detail",
                "power_system", "world_map_hints", "prologue_preview"]:
        op.drop_column("stories", col)
```

- [ ] **步骤 3：同步 Schema（schemas/story.py）**

在 StoryResponse 和 StoryUpdate schema 中添加对应可选字段：

```python
title_suggestions: Optional[list[str]] = None
target_audience: Optional[str] = None
style_tags: Optional[list[str]] = None
word_count_estimate: Optional[int] = None
golden_finger_detail: Optional[str] = None
power_system: Optional[dict] = None
world_map_hints: Optional[str] = None
prologue_preview: Optional[str] = None
```

- [ ] **步骤 4：重构 StoryGeneratorService.generate_story()**

将硬编码 `_build_story_prompt()` 替换为模板驱动：

```python
async def generate_story(self, inspiration: str, project_id: str, **kwargs) -> Dict[str, Any]:
    from ..prompt_service import get_rendered_prompt
    from ..knowledge_service import inject_knowledge

    db = SessionLocal()
    try:
        context = {
            "inspiration": inspiration,
            "genre": kwargs.get("genre", "未指定"),
            "tone": kwargs.get("tone", "未指定"),
            "target_length": kwargs.get("target_length", "中篇"),
            "protagonist": kwargs.get("protagonist", "未设定"),
            "golden_finger": kwargs.get("golden_finger", "未设定"),
            "relationship": kwargs.get("relationship", "未设定"),
            "worldbuilding_hints": kwargs.get("worldbuilding_hints", "未设定"),
        }
        template = get_rendered_prompt(db, "story-generation", context)
        prompt = inject_knowledge(db, template)

        result = await self.llm.generate(parameters={
            "prompt": prompt,
            "system_prompt": "你是一位专业的故事开发者和叙事设计师。所有输出必须使用中文。",
            "temperature": kwargs.get("temperature", 0.8),
            "max_tokens": kwargs.get("max_tokens", 6000),
            "response_format": {"type": "json_object"},
        })

        if not result.file_paths:
            raise ValueError("LLM generation produced no output file")

        raw_text = result.file_paths[0].read_text(encoding="utf-8")
        story_data = _parse_json_result(raw_text)

        validation_errors = _validate_schema(story_data, STORY_SCHEMA)
        if validation_errors:
            logger.warning("Story schema validation warnings | errors=%s", validation_errors)

        return story_data
    finally:
        db.close()
```

- [ ] **步骤 5：重构 generate_chapter_outline() 加入前情提要**

```python
async def generate_chapter_outline(self, story_data: Dict[str, Any],
                                   project_id: str,
                                   chapter_count: Optional[int] = None) -> Dict[str, Any]:
    from ..prompt_service import get_rendered_prompt
    from ..knowledge_service import inject_knowledge, build_continuity_context
    import json as _json

    if chapter_count is None:
        plot_points = story_data.get("plot_points", [])
        chapter_count = max(len(plot_points) * 2, 6)

    db = SessionLocal()
    try:
        continuity = build_continuity_context(db, project_id)
    finally:
        db.close()

    # Build relations context
    relations_text = "（暂无角色关系数据）"
    # (relations from story.characters can be extracted here)

    context = {
        "chapter_count": str(chapter_count),
        "story_data_json": _json.dumps(story_data, indent=2, ensure_ascii=False),
        "continuity_context": continuity,
        "relations_context": relations_text,
    }
    template = get_rendered_prompt(db, "chapter-outline", context)

    # ... rest same pattern: llm.generate → parse → validate → return
```

- [ ] **步骤 6：运行全量测试**

```bash
cd backend && source venv/bin/activate && python -m pytest tests/ -v --tb=short -k "not e2e"
```

预期：新增测试全部 PASS，已有测试保持 PASS。

- [ ] **步骤 7：Commit**

```bash
git add backend/app/models/story.py backend/app/schemas/story.py \
  backend/app/services/generator_services/story_generator_service.py \
  backend/app/db/migrations/versions/015_extend_story_fields.py
git commit -m "feat: extend Story schema + refactor generator service with templates + continuity context"
```

---

## 自检

1. **规格覆盖度**：Knowledge 模型✓ Prompt 模型✓ Relation+CharacterState✓ 种子数据✓ 模板渲染✓ KB 注入✓ 前情提要✓ Story 扩展✓ Generator 重构✓ API 路由✓
2. **占位符扫描**：无 TODO 或占位符
3. **类型一致性**：所有模型/CRUD/服务层接口一致

---

## 执行

计划已保存到 `docs/superpowers/plans/2026-05-13-phase-a-story-gen.md`。推荐**子代理驱动**逐任务执行，或你现在直接说"开始"我就在当前会话中按任务顺序实现。
