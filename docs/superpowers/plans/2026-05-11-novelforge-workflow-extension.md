# NovelForge 工作流扩展实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。

**目标：** 在现有视频生成工作流前增加小说创作阶段：一句话灵感 → 故事大纲 → 章节规划 → 剧本 → 分镜 → 图片 → 音频 → 视频

**架构：** 新增 Story 模型和 StoryGeneratorService，在 TaskStage 枚举中增加 INSPIRATION、STORY、CHAPTER_OUTLINE 阶段，工作流支持从任意阶段开始

**技术栈：** FastAPI + SQLAlchemy + Next.js + React

**依赖关系：**
```
17.1.1 数据模型 (Story) → 17.1.2 迁移 → 17.1.3 API → 17.1.4 Generator → 17.1.5 Workflow → 17.1.6 前端
```

---

## 任务 17.1.1：Story 数据模型

**文件：**
- 创建：`backend/app/models/story.py`
- 修改：`backend/app/models/__init__.py`
- 修改：`backend/app/models/project.py`（增加 relationship）

```python
# backend/app/models/story.py
"""Story model - long-form story creation for video series"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSON as PGJSON
from .guid_type import GUID
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum


class StoryStatus(str, enum.Enum):
    """Story status enumeration"""
    DRAFT = "draft"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Story(BaseModel):
    """Story model - represents a long-form story"""
    
    __tablename__ = "stories"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        GUID(),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Story content
    inspiration = Column(Text, nullable=True)           # One-line inspiration
    logline = Column(Text, nullable=True)               # One-line story line
    synopsis = Column(Text, nullable=True)              # Story synopsis
    worldbuilding = Column(JSON, nullable=True, default=dict)  # World settings
    characters = Column(JSON, nullable=True, default=list)     # Character list
    themes = Column(JSON, nullable=True, default=list)         # Themes
    plot_points = Column(JSON, nullable=True, default=list)    # Key plot points
    
    # Chapter outline
    chapter_outline = Column(JSON, nullable=True, default=list)  # Chapter summaries
    
    # Status
    status = Column(SQLEnum(StoryStatus), default=StoryStatus.DRAFT, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    project = relationship("Project", back_populates="stories")
    
    def __repr__(self):
        return f"<Story(id={self.id}, project_id={self.project_id}, status='{self.status}')>"
```

```python
# backend/app/models/project.py - 增加 relationship
stories = relationship("Story", back_populates="project", cascade="all, delete-orphan")
```

- [ ] **步骤 1：创建 Story 模型文件**
- [ ] **步骤 2：更新 __init__.py 导出**
- [ ] **步骤 3：更新 Project 模型 relationship**
- [ ] **步骤 4：验证导入 python -c "from app.models.story import Story; print('OK')"**
- [ ] **步骤 5：Commit**

```bash
git add backend/app/models/story.py backend/app/models/__init__.py backend/app/models/project.py
git commit -m "feat: add Story model for long-form story creation"
```

---

## 任务 17.1.2：数据库迁移

**文件：**
- 创建：`backend/app/db/migrations/versions/012_add_stories.py`

```python
# backend/app/db/migrations/versions/012_add_stories.py
"""add stories table

Revision ID: 012
Revises: 011
Create Date: 2026-05-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '012'
down_revision = '011'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'stories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('inspiration', sa.Text, nullable=True),
        sa.Column('logline', sa.Text, nullable=True),
        sa.Column('synopsis', sa.Text, nullable=True),
        sa.Column('worldbuilding', postgresql.JSON, nullable=True),
        sa.Column('characters', postgresql.JSON, nullable=True),
        sa.Column('themes', postgresql.JSON, nullable=True),
        sa.Column('plot_points', postgresql.JSON, nullable=True),
        sa.Column('chapter_outline', postgresql.JSON, nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table('stories')
```

- [ ] **步骤 1：创建迁移文件**
- [ ] **步骤 2：Commit**

---

## 任务 17.1.3：Story API

**文件：**
- 创建：`backend/app/schemas/story.py`
- 创建：`backend/app/db/story_crud.py`
- 创建：`backend/app/api/routes/stories.py`
- 修改：`backend/app/main.py`（注册路由）

```python
# backend/app/schemas/story.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class StoryBase(BaseModel):
    inspiration: Optional[str] = None
    logline: Optional[str] = None
    synopsis: Optional[str] = None
    worldbuilding: Optional[Dict[str, Any]] = None
    characters: Optional[List[Dict[str, Any]]] = None
    themes: Optional[List[str]] = None
    plot_points: Optional[List[Dict[str, Any]]] = None
    chapter_outline: Optional[List[Dict[str, Any]]] = None


class StoryCreate(StoryBase):
    project_id: UUID


class StoryUpdate(BaseModel):
    inspiration: Optional[str] = None
    logline: Optional[str] = None
    synopsis: Optional[str] = None
    worldbuilding: Optional[Dict[str, Any]] = None
    characters: Optional[List[Dict[str, Any]]] = None
    themes: Optional[List[str]] = None
    plot_points: Optional[List[Dict[str, Any]]] = None
    chapter_outline: Optional[List[Dict[str, Any]]] = None
    status: Optional[str] = None


class StoryResponse(StoryBase):
    id: UUID
    project_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

```python
# backend/app/db/story_crud.py
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from ..models.story import Story
from ..schemas.story import StoryCreate, StoryUpdate


class StoryCRUD:
    def create(self, db: Session, story_in: StoryCreate) -> Story:
        story = Story(**story_in.model_dump())
        db.add(story)
        db.commit()
        db.refresh(story)
        return story
    
    def get_by_project(self, db: Session, project_id: UUID) -> Optional[Story]:
        return db.query(Story).filter(Story.project_id == project_id).first()
    
    def get(self, db: Session, story_id: UUID) -> Optional[Story]:
        return db.query(Story).filter(Story.id == story_id).first()
    
    def update(self, db: Session, story_id: UUID, story_in: StoryUpdate) -> Optional[Story]:
        story = self.get(db, story_id)
        if not story:
            return None
        update_data = story_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(story, key, value)
        db.commit()
        db.refresh(story)
        return story
    
    def delete(self, db: Session, story_id: UUID) -> bool:
        story = self.get(db, story_id)
        if not story:
            return False
        db.delete(story)
        db.commit()
        return True


story_crud = StoryCRUD()
```

```python
# backend/app/api/routes/stories.py
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ...db.session import get_db
from ...db.story_crud import story_crud
from ...schemas.story import StoryCreate, StoryUpdate, StoryResponse

router = APIRouter(prefix="/projects/{project_id}/stories", tags=["stories"])


@router.get("", response_model=Optional[StoryResponse])
def get_story(project_id: UUID, db: Session = Depends(get_db)):
    """获取项目下的故事"""
    story = story_crud.get_by_project(db, project_id)
    if not story:
        return None
    return story


@router.post("", response_model=StoryResponse, status_code=status.HTTP_201_CREATED)
def create_story(project_id: UUID, story_in: StoryCreate, db: Session = Depends(get_db)):
    """创建故事"""
    if story_in.project_id != project_id:
        raise HTTPException(status_code=400, detail="project_id mismatch")
    
    existing = story_crud.get_by_project(db, project_id)
    if existing:
        raise HTTPException(status_code=409, detail="Story already exists for this project")
    
    return story_crud.create(db, story_in)


@router.put("", response_model=StoryResponse)
def update_story(project_id: UUID, story_in: StoryUpdate, db: Session = Depends(get_db)):
    """更新故事"""
    story = story_crud.get_by_project(db, project_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    return story_crud.update(db, story.id, story_in)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_story(project_id: UUID, db: Session = Depends(get_db)):
    """删除故事"""
    story = story_crud.get_by_project(db, project_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    story_crud.delete(db, story.id)
```

- [ ] **步骤 1：创建 schemas/story.py**
- [ ] **步骤 2：创建 db/story_crud.py**
- [ ] **步骤 3：创建 api/routes/stories.py**
- [ ] **步骤 4：注册路由到 main.py**
- [ ] **步骤 5：验证 import**
- [ ] **步骤 6：Commit**

---

## 任务 17.1.4：Story Generator Service

**文件：**
- 创建：`backend/app/services/generator_services/story_generator_service.py`
- 修改：`backend/app/config.py`（可选，增加 story 相关配置）

```python
# backend/app/services/generator_services/story_generator_service.py
"""Story Generator Service - expands inspiration into full story"""
import json
from typing import Any, Dict, Optional
from pathlib import Path

from ...config import settings, STORAGE_DIRS
from ...providers.llm_provider import llm_provider
from ...core.logging_config import get_logger

logger = get_logger(__name__)


STORY_SCHEMA = {
    "type": "object",
    "properties": {
        "logline": {"type": "string", "description": "One-line story summary"},
        "synopsis": {"type": "string", "description": "Story synopsis (300-500 words)"},
        "worldbuilding": {
            "type": "object",
            "properties": {
                "setting": {"type": "string"},
                "time_period": {"type": "string"},
                "rules": {"type": "array", "items": {"type": "string"}}
            }
        },
        "characters": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "role": {"type": "string"},
                    "description": {"type": "string"},
                    "motivation": {"type": "string"}
                },
                "required": ["name", "role"]
            }
        },
        "themes": {"type": "array", "items": {"type": "string"}},
        "plot_points": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "act": {"type": "string"},
                    "event": {"type": "string"},
                    "description": {"type": "string"}
                }
            }
        }
    },
    "required": ["logline", "synopsis", "characters"]
}


CHAPTER_OUTLINE_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "chapter_number": {"type": "integer"},
            "title": {"type": "string"},
            "summary": {"type": "string"},
            "key_scenes": {"type": "array", "items": {"type": "string"}},
            "characters": {"type": "array", "items": {"type": "string"}},
            "duration": {"type": "number", "description": "Estimated duration in seconds"}
        },
        "required": ["chapter_number", "title", "summary"]
    }
}


class StoryGeneratorService:
    """Generates story from inspiration"""
    
    def __init__(self):
        self.stories_dir = STORAGE_DIRS.get("stories", settings.storage_path / "stories")
        self.stories_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate_story(self, inspiration: str, project_id: str, **kwargs) -> Dict[str, Any]:
        """Generate story from inspiration"""
        prompt = self._build_story_prompt(inspiration)
        
        try:
            result = await llm_provider.generate(
                prompt=prompt,
                system_prompt="你是一个专业的故事创作者。请根据用户的灵感创作一个完整的故事大纲。返回 JSON 格式。",
                response_format={"type": "json_object"}
            )
            
            story_data = self._parse_json_result(result)
            self._validate_schema(story_data, STORY_SCHEMA)
            
            return {
                "success": True,
                "data": story_data,
                "inspiration": inspiration
            }
            
        except Exception as e:
            logger.error(f"Story generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_chapter_outline(
        self, 
        story_data: Dict[str, Any], 
        chapter_count: int = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate chapter outline from story"""
        prompt = self._build_chapter_prompt(story_data, chapter_count)
        
        try:
            result = await llm_provider.generate(
                prompt=prompt,
                system_prompt="你是一个专业的剧本结构设计师。请将故事划分为适合视频改编的章节。返回 JSON 数组格式。",
                response_format={"type": "json_object"}
            )
            
            chapters = self._parse_json_result(result)
            self._validate_schema(chapters, CHAPTER_OUTLINE_SCHEMA)
            
            return {
                "success": True,
                "data": chapters
            }
            
        except Exception as e:
            logger.error(f"Chapter outline generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _build_story_prompt(self, inspiration: str) -> str:
        return f"""请将以下灵感扩展为完整的故事大纲：

灵感：{inspiration}

请返回 JSON 格式，包含：
- logline: 一句话故事线（20字以内）
- synopsis: 故事梗概（300-500字）
- worldbuilding: 世界观设定（setting, time_period, rules）
- characters: 主要人物列表（name, role, description, motivation）
- themes: 主题列表
- plot_points: 关键情节点（act, event, description）

确保内容适合改编为 3-5 分钟的短视频系列。"""
    
    def _build_chapter_prompt(self, story_data: dict, chapter_count: int = None) -> str:
        count_str = f"{chapter_count}章" if chapter_count else "合适的章数"
        
        return f"""请将以下故事划分为{count_str}，适合视频改编：

故事梗概：{story_data.get('synopsis', '')}
人物：{story_data.get('characters', [])}
情节点：{story_data.get('plot_points', [])}

每章返回：
- chapter_number: 章节号
- title: 章节标题
- summary: 本章摘要（100字）
- key_scenes: 关键场景列表
- characters: 出场人物
- duration: 预估时长（秒）

返回 JSON 数组格式。"""
    
    def _parse_json_result(self, result: str) -> Dict:
        # Remove markdown code blocks if present
        if result.startswith("```json"):
            result = result[7:]
        if result.endswith("```"):
            result = result[:-3]
        return json.loads(result.strip())
    
    def _validate_schema(self, data: Dict, schema: Dict):
        # Basic validation - can be enhanced with jsonschema library
        if "required" in schema:
            for field in schema["required"]:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
```

- [ ] **步骤 1：创建 story_generator_service.py**
- [ ] **步骤 2：验证 import**
- [ ] **步骤 3：Commit**

---

## 任务 17.1.5：工作流集成

**文件：**
- 修改：`backend/app/models/task.py`（增加 TaskStage）
- 修改：`backend/app/services/workflow_service.py`（增加阶段处理）

```python
# backend/app/models/task.py - 修改 TaskStage
class TaskStage(str, Enum):
    """Task stage enumeration"""
    INSPIRATION = "inspiration"
    STORY = "story"
    CHAPTER_OUTLINE = "chapter_outline"
    SCRIPT = "script"
    STORYBOARD = "storyboard"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
```

```python
# backend/app/services/workflow_service.py - 增加阶段处理
# 在 ADVANCE_ORDER 中增加新阶段
ADVANCE_ORDER = [
    TaskStage.INSPIRATION,
    TaskStage.STORY,
    TaskStage.CHAPTER_OUTLINE,
    TaskStage.SCRIPT,
    TaskStage.STORYBOARD,
    TaskStage.IMAGE,
    TaskStage.AUDIO,
    TaskStage.VIDEO,
]

# 在 _handle_stage 方法中增加：
async def _handle_stage(self, stage, project, task, parameters):
    if stage == TaskStage.INSPIRATION:
        return await self._handle_inspiration(project, parameters)
    elif stage == TaskStage.STORY:
        return await self._handle_story(project, parameters)
    elif stage == TaskStage.CHAPTER_OUTLINE:
        return await self._handle_chapter_outline(project, parameters)
    # ... existing stages
```

- [ ] **步骤 1：更新 TaskStage 枚举**
- [ ] **步骤 2：更新 workflow_service**
- [ ] **步骤 3：编写阶段处理逻辑**
- [ ] **步骤 4：Commit**

---

## 任务 17.1.6：前端故事创作界面

**文件：**
- 创建：`frontend/src/types/story.ts`
- 创建：`frontend/src/lib/api/stories.ts`
- 创建：`frontend/src/hooks/use-stories.ts`
- 创建：`frontend/src/components/story-editor.tsx`
- 修改：`frontend/src/app/projects/[id]/page.tsx`（增加"故事" tab）

```typescript
// frontend/src/types/story.ts
export interface Story {
  id: string;
  project_id: string;
  inspiration?: string;
  logline?: string;
  synopsis?: string;
  worldbuilding?: Record<string, any>;
  characters?: Array<{
    name: string;
    role: string;
    description?: string;
    motivation?: string;
  }>;
  themes?: string[];
  plot_points?: Array<{
    act: string;
    event: string;
    description: string;
  }>;
  chapter_outline?: Array<{
    chapter_number: number;
    title: string;
    summary: string;
    key_scenes: string[];
    characters: string[];
    duration: number;
  }>;
  status: 'draft' | 'completed' | 'archived';
  created_at: string;
  updated_at: string;
}
```

- [ ] **步骤 1：创建类型定义**
- [ ] **步骤 2：创建 API client**
- [ ] **步骤 3：创建 React Query hooks**
- [ ] **步骤 4：创建故事编辑器组件**
- [ ] **步骤 5：集成到项目详情页**
- [ ] **步骤 6：验证 npm run build**
- [ ] **步骤 7：Commit**

---

## 执行总结

| 任务 | 内容 | 优先级 | 依赖 | 预计耗时 |
|------|------|--------|------|---------|
| 17.1.1 | Story 数据模型 | P0 | 无 | 30m |
| 17.1.2 | 数据库迁移 012 | P0 | 17.1.1 | 15m |
| 17.1.3 | Story API | P0 | 17.1.2 | 1h |
| 17.1.4 | Story Generator Service | P0 | 17.1.3 | 1.5h |
| 17.1.5 | 工作流集成 | P1 | 17.1.4 | 1h |
| 17.1.6 | 前端故事界面 | P2 | 17.1.5 | 2h |
