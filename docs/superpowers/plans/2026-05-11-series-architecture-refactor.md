# 短剧架构重构与功能补齐实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 将 ops-video 从"单短片项目"重构为"短剧多章节项目"，新增角色卡管理、OSS 网络存储管理、多 clip 视频拼接等核心功能

**架构：** Project 升级为短剧容器，挂载角色卡和多个章节（Task），每个章节独立走完 script→storyboard→image→audio→video 管线，角色卡在 Project 级别共享，所有云端生成制品自动持久化到 OSS

**技术栈：** FastAPI + SQLAlchemy + PostgreSQL + 阿里云 OSS SDK + FFmpeg + Next.js + React

**依赖关系图：**
```
Phase 15.1 数据模型 (CharacterCard, StorageProvider)
    ↓
Phase 15.2 数据库迁移 (010, 011)
    ↓
Phase 15.3 API 层 (角色卡 CRUD, 存储管理 CRUD+测试)
    ↓
Phase 15.4 OSS 核心服务 (上传/下载/签名 URL)
    ↓
Phase 15.5 Provider 改造 (自动下载云端URL→上传OSS)
    ↓
Phase 15.6 视频合成重构 (多 clip 拼接)
    ↓
Phase 15.7 Task 层级改造 (章节子任务)
    ↓
Phase 15.8 前端 (角色卡面板 + 存储管理 + 章节视图)
    ↓
Phase 15.9 全链路测试 + 文档
    ↓
Phase 16 尾帧延长 (可选，后续)
```

---

## Phase 15.1：数据模型层

### 任务 1.1：CharacterCard 模型

**文件：**
- 创建：`backend/app/models/character_card.py`
- 修改：`backend/app/models/__init__.py`
- 修改：`backend/app/models/project.py`（增加 relationship）

```python
# backend/app/models/character_card.py
"""Character Card model - project-level character consistency"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .guid_type import GUID
from .base import BaseModel


class CharacterCard(BaseModel):
    """角色卡 - 存储角色三视图和描述，供所有章节生成时引用"""
    
    __tablename__ = "character_cards"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        GUID(),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # 角色信息
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)  # 外观描述，注入到 prompt
    
    # 三视图（存储 OSS URL）
    front_image_url = Column(String(500), nullable=True)  # 正面图
    side_image_url = Column(String(500), nullable=True)   # 侧面图
    back_image_url = Column(String(500), nullable=True)   # 背面图
    
    # 角色卡本地文件路径（兼容旧版）
    front_image_path = Column(String(500), nullable=True)
    side_image_path = Column(String(500), nullable=True)
    back_image_path = Column(String(500), nullable=True)
    
    # 使用频率统计
    usage_count = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    project = relationship("Project", back_populates="character_cards")
    
    def __repr__(self):
        return f"<CharacterCard(id={self.id}, name='{self.name}')>"
```

```python
# backend/app/models/__init__.py - 增加导出
from .character_card import CharacterCard
```

```python
# backend/app/models/project.py - 增加 relationship
# 在 Project 类中添加：
character_cards = relationship(
    "CharacterCard", 
    back_populates="project", 
    cascade="all, delete-orphan"
)
```

- [ ] **步骤 1：创建 CharacterCard 模型文件**
- [ ] **步骤 2：更新 __init__.py 导出**
- [ ] **步骤 3：更新 Project 模型 relationship**
- [ ] **步骤 4：运行 python -c "from app.models.character_card import CharacterCard; print('OK')"**
- [ ] **步骤 5：Commit**

```bash
git add backend/app/models/character_card.py backend/app/models/__init__.py backend/app/models/project.py
git commit -m "feat: add CharacterCard model for project-level character consistency"
```

---

### 任务 1.2：StorageProvider 模型

**文件：**
- 创建：`backend/app/models/storage_provider.py`
- 修改：`backend/app/models/__init__.py`

```python
# backend/app/models/storage_provider.py
"""Storage Provider model - cloud storage configuration"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from .guid_type import GUID
from .base import BaseModel


class StorageProvider(BaseModel):
    """网络存储提供商配置"""
    
    __tablename__ = "storage_providers"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)  # "阿里云-主"
    provider_type = Column(String(50), nullable=False)  # aliyun_oss / aws_s3 / tencent_cos
    
    # 认证信息（加密存储）
    access_key = Column(String(500), nullable=False)
    secret_key = Column(String(500), nullable=False)
    
    # 存储配置
    bucket = Column(String(100), nullable=False)
    region = Column(String(50), nullable=True)
    endpoint = Column(String(200), nullable=True)  # 自定义域名
    cdn_url = Column(String(200), nullable=True)   # CDN 加速域名
    
    # 状态
    is_active = Column(Boolean, default=False, nullable=False)  # 当前激活
    is_encrypted = Column(Boolean, default=False, nullable=False)
    
    # 测试记录
    last_test_status = Column(String(20), nullable=True)  # success/failed
    last_test_at = Column(DateTime, nullable=True)
    last_test_latency_ms = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<StorageProvider(id={self.id}, name='{self.name}', type='{self.provider_type}')>"
```

- [ ] **步骤 1：创建 StorageProvider 模型文件**
- [ ] **步骤 2：更新 __init__.py 导出**
- [ ] **步骤 3：验证导入**
- [ ] **步骤 4：Commit**

```bash
git add backend/app/models/storage_provider.py backend/app/models/__init__.py
git commit -m "feat: add StorageProvider model for cloud storage management"
```

---

### 任务 1.3：扩展 Project settings schema

**文件：**
- 修改：`backend/app/schemas/project.py`（增加 style_preset 字段）

```python
# backend/app/schemas/project.py - 在 ProjectCreate/Update 中增加：
style_preset: Optional[dict] = Field(
    default=None,
    description="风格预设：画风、分辨率、TTS声音、视频比例等"
)
# 示例：{"style": "cyberpunk", "resolution": "1080x1920", "aspect_ratio": "9:16", "tts_voice": "zh-CN-XiaoxiaoNeural"}
```

- [ ] **步骤 1：更新 Project schemas**
- [ ] **步骤 2：Commit**

```bash
git add backend/app/schemas/project.py
git commit -m "feat: add style_preset to project schemas"
```

---

## Phase 15.2：数据库迁移

### 任务 2.1：迁移 010 - character_cards 表

**文件：**
- 创建：`backend/app/db/migrations/versions/010_add_character_cards.py`

```python
# backend/app/db/migrations/versions/010_add_character_cards.py
"""add character_cards table

Revision ID: 010
Revises: 009
Create Date: 2026-05-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'character_cards',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('front_image_url', sa.String(500), nullable=True),
        sa.Column('side_image_url', sa.String(500), nullable=True),
        sa.Column('back_image_url', sa.String(500), nullable=True),
        sa.Column('front_image_path', sa.String(500), nullable=True),
        sa.Column('side_image_path', sa.String(500), nullable=True),
        sa.Column('back_image_path', sa.String(500), nullable=True),
        sa.Column('usage_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_character_cards_project_id', 'character_cards', ['project_id'])


def downgrade():
    op.drop_table('character_cards')
```

- [ ] **步骤 1：创建迁移文件**
- [ ] **步骤 2：运行 alembic upgrade head 验证（本地测试用 SQLite 跳过）**
- [ ] **步骤 3：Commit**

---

### 任务 2.2：迁移 011 - storage_providers 表

**文件：**
- 创建：`backend/app/db/migrations/versions/011_add_storage_providers.py`

```python
# backend/app/db/migrations/versions/011_add_storage_providers.py
"""add storage_providers table

Revision ID: 011
Revises: 010
Create Date: 2026-05-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'storage_providers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('provider_type', sa.String(50), nullable=False),
        sa.Column('access_key', sa.String(500), nullable=False),
        sa.Column('secret_key', sa.String(500), nullable=False),
        sa.Column('bucket', sa.String(100), nullable=False),
        sa.Column('region', sa.String(50), nullable=True),
        sa.Column('endpoint', sa.String(200), nullable=True),
        sa.Column('cdn_url', sa.String(200), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_encrypted', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('last_test_status', sa.String(20), nullable=True),
        sa.Column('last_test_at', sa.DateTime, nullable=True),
        sa.Column('last_test_latency_ms', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table('storage_providers')
```

- [ ] **步骤 1：创建迁移文件**
- [ ] **步骤 2：Commit**

---

## Phase 15.3：API 层

### 任务 3.1：角色卡 CRUD API

**文件：**
- 创建：`backend/app/api/routes/character_cards.py`
- 创建：`backend/app/schemas/character_card.py`
- 创建：`backend/app/db/character_card_crud.py`
- 修改：`backend/app/main.py`（注册路由）

```python
# backend/app/schemas/character_card.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class CharacterCardBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    front_image_url: Optional[str] = None
    side_image_url: Optional[str] = None
    back_image_url: Optional[str] = None


class CharacterCardCreate(CharacterCardBase):
    project_id: UUID


class CharacterCardUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    front_image_url: Optional[str] = None
    side_image_url: Optional[str] = None
    back_image_url: Optional[str] = None


class CharacterCardResponse(CharacterCardBase):
    id: UUID
    project_id: UUID
    usage_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

```python
# backend/app/db/character_card_crud.py
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from ..models.character_card import CharacterCard
from ..schemas.character_card import CharacterCardCreate, CharacterCardUpdate


class CharacterCardCRUD:
    def create(self, db: Session, card_in: CharacterCardCreate) -> CharacterCard:
        card = CharacterCard(**card_in.model_dump())
        db.add(card)
        db.commit()
        db.refresh(card)
        return card
    
    def get_by_project(self, db: Session, project_id: UUID) -> List[CharacterCard]:
        return db.query(CharacterCard).filter(
            CharacterCard.project_id == project_id
        ).all()
    
    def get(self, db: Session, card_id: UUID) -> Optional[CharacterCard]:
        return db.query(CharacterCard).filter(CharacterCard.id == card_id).first()
    
    def update(self, db: Session, card_id: UUID, card_in: CharacterCardUpdate) -> Optional[CharacterCard]:
        card = self.get(db, card_id)
        if not card:
            return None
        update_data = card_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(card, key, value)
        db.commit()
        db.refresh(card)
        return card
    
    def delete(self, db: Session, card_id: UUID) -> bool:
        card = self.get(db, card_id)
        if not card:
            return False
        db.delete(card)
        db.commit()
        return True


character_card_crud = CharacterCardCRUD()
```

```python
# backend/app/api/routes/character_cards.py
from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ...db.session import get_db
from ...db.character_card_crud import character_card_crud
from ...schemas.character_card import (
    CharacterCardCreate, CharacterCardUpdate, CharacterCardResponse
)

router = APIRouter(prefix="/projects/{project_id}/character-cards", tags=["character-cards"])


@router.get("", response_model=List[CharacterCardResponse])
def list_cards(project_id: UUID, db: Session = Depends(get_db)):
    """列出项目下所有角色卡"""
    return character_card_crud.get_by_project(db, project_id)


@router.post("", response_model=CharacterCardResponse, status_code=status.HTTP_201_CREATED)
def create_card(project_id: UUID, card_in: CharacterCardCreate, db: Session = Depends(get_db)):
    """创建角色卡"""
    if card_in.project_id != project_id:
        raise HTTPException(status_code=400, detail="project_id mismatch")
    return character_card_crud.create(db, card_in)


@router.get("/{card_id}", response_model=CharacterCardResponse)
def get_card(project_id: UUID, card_id: UUID, db: Session = Depends(get_db)):
    """获取角色卡详情"""
    card = character_card_crud.get(db, card_id)
    if not card or card.project_id != project_id:
        raise HTTPException(status_code=404, detail="Character card not found")
    return card


@router.put("/{card_id}", response_model=CharacterCardResponse)
def update_card(project_id: UUID, card_id: UUID, card_in: CharacterCardUpdate, db: Session = Depends(get_db)):
    """更新角色卡"""
    card = character_card_crud.get(db, card_id)
    if not card or card.project_id != project_id:
        raise HTTPException(status_code=404, detail="Character card not found")
    return character_card_crud.update(db, card_id, card_in)


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(project_id: UUID, card_id: UUID, db: Session = Depends(get_db)):
    """删除角色卡"""
    card = character_card_crud.get(db, card_id)
    if not card or card.project_id != project_id:
        raise HTTPException(status_code=404, detail="Character card not found")
    character_card_crud.delete(db, card_id)
```

```python
# backend/app/main.py - 在路由注册处添加：
from .api.routes import character_cards
app.include_router(character_cards.router, prefix="/api/v1")
```

- [ ] **步骤 1：创建 schemas/character_card.py**
- [ ] **步骤 2：创建 db/character_card_crud.py**
- [ ] **步骤 3：创建 api/routes/character_cards.py**
- [ ] **步骤 4：注册路由到 main.py**
- [ ] **步骤 5：验证 import python -c "from app.api.routes.character_cards import router; print('OK')"**
- [ ] **步骤 6：Commit**

---

### 任务 3.2：存储管理 CRUD API + 连接测试

**文件：**
- 创建：`backend/app/api/routes/storage_providers.py`
- 创建：`backend/app/schemas/storage_provider.py`
- 创建：`backend/app/db/storage_provider_crud.py`

```python
# backend/app/schemas/storage_provider.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class StorageProviderBase(BaseModel):
    name: str = Field(..., max_length=100)
    provider_type: str  # aliyun_oss / aws_s3 / tencent_cos
    bucket: str
    region: Optional[str] = None
    endpoint: Optional[str] = None
    cdn_url: Optional[str] = None


class StorageProviderCreate(StorageProviderBase):
    access_key: str
    secret_key: str


class StorageProviderUpdate(BaseModel):
    name: Optional[str] = None
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    bucket: Optional[str] = None
    region: Optional[str] = None
    endpoint: Optional[str] = None
    cdn_url: Optional[str] = None


class StorageProviderResponse(StorageProviderBase):
    id: UUID
    is_active: bool
    is_encrypted: bool
    last_test_status: Optional[str]
    last_test_at: Optional[datetime]
    last_test_latency_ms: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class StorageTestResult(BaseModel):
    success: bool
    message: str
    latency_ms: Optional[float] = None
```

```python
# backend/app/db/storage_provider_crud.py
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from ..models.storage_provider import StorageProvider
from ..schemas.storage_provider import StorageProviderCreate, StorageProviderUpdate


class StorageProviderCRUD:
    def create(self, db: Session, provider_in: StorageProviderCreate) -> StorageProvider:
        provider = StorageProvider(**provider_in.model_dump())
        db.add(provider)
        db.commit()
        db.refresh(provider)
        return provider
    
    def get_all(self, db: Session) -> List[StorageProvider]:
        return db.query(StorageProvider).order_by(StorageProvider.created_at.desc()).all()
    
    def get(self, db: Session, provider_id: UUID) -> Optional[StorageProvider]:
        return db.query(StorageProvider).filter(StorageProvider.id == provider_id).first()
    
    def get_active(self, db: Session) -> Optional[StorageProvider]:
        return db.query(StorageProvider).filter(StorageProvider.is_active == True).first()
    
    def update(self, db: Session, provider_id: UUID, provider_in: StorageProviderUpdate) -> Optional[StorageProvider]:
        provider = self.get(db, provider_id)
        if not provider:
            return None
        update_data = provider_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(provider, key, value)
        db.commit()
        db.refresh(provider)
        return provider
    
    def delete(self, db: Session, provider_id: UUID) -> bool:
        provider = self.get(db, provider_id)
        if not provider:
            return False
        db.delete(provider)
        db.commit()
        return True
    
    def activate(self, db: Session, provider_id: UUID) -> Optional[StorageProvider]:
        # 先停用所有
        db.query(StorageProvider).update({StorageProvider.is_active: False})
        # 再激活目标
        provider = self.get(db, provider_id)
        if provider:
            provider.is_active = True
            db.commit()
            db.refresh(provider)
        return provider
    
    def update_test_result(self, db: Session, provider_id: UUID, success: bool, latency_ms: float):
        provider = self.get(db, provider_id)
        if provider:
            from datetime import datetime
            provider.last_test_status = "success" if success else "failed"
            provider.last_test_at = datetime.utcnow()
            provider.last_test_latency_ms = int(latency_ms)
            db.commit()


storage_provider_crud = StorageProviderCRUD()
```

```python
# backend/app/api/routes/storage_providers.py
from uuid import UUID
from typing import List
import time
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ...db.session import get_db
from ...db.storage_provider_crud import storage_provider_crud
from ...schemas.storage_provider import (
    StorageProviderCreate, StorageProviderUpdate, 
    StorageProviderResponse, StorageTestResult
)

router = APIRouter(prefix="/storage-providers", tags=["storage-providers"])


@router.get("", response_model=List[StorageProviderResponse])
def list_providers(db: Session = Depends(get_db)):
    return storage_provider_crud.get_all(db)


@router.post("", response_model=StorageProviderResponse, status_code=status.HTTP_201_CREATED)
def create_provider(provider_in: StorageProviderCreate, db: Session = Depends(get_db)):
    return storage_provider_crud.create(db, provider_in)


@router.get("/{provider_id}", response_model=StorageProviderResponse)
def get_provider(provider_id: UUID, db: Session = Depends(get_db)):
    provider = storage_provider_crud.get(db, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Storage provider not found")
    return provider


@router.put("/{provider_id}", response_model=StorageProviderResponse)
def update_provider(provider_id: UUID, provider_in: StorageProviderUpdate, db: Session = Depends(get_db)):
    provider = storage_provider_crud.update(db, provider_id, provider_in)
    if not provider:
        raise HTTPException(status_code=404, detail="Storage provider not found")
    return provider


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_provider(provider_id: UUID, db: Session = Depends(get_db)):
    if not storage_provider_crud.delete(db, provider_id):
        raise HTTPException(status_code=404, detail="Storage provider not found")


@router.post("/{provider_id}/test", response_model=StorageTestResult)
async def test_connection(provider_id: UUID, db: Session = Depends(get_db)):
    """测试存储连接"""
    from ...core.oss_service import test_storage_connection
    
    provider = storage_provider_crud.get(db, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Storage provider not found")
    
    start = time.time()
    try:
        result = await test_storage_connection(provider)
        latency = (time.time() - start) * 1000
        storage_provider_crud.update_test_result(db, provider_id, result.success, latency)
        return StorageTestResult(
            success=result.success,
            message=result.message,
            latency_ms=round(latency, 1)
        )
    except Exception as e:
        latency = (time.time() - start) * 1000
        storage_provider_crud.update_test_result(db, provider_id, False, latency)
        return StorageTestResult(success=False, message=str(e), latency_ms=round(latency, 1))


@router.post("/{provider_id}/activate", response_model=StorageProviderResponse)
def activate_provider(provider_id: UUID, db: Session = Depends(get_db)):
    """设为当前激活存储"""
    provider = storage_provider_crud.activate(db, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Storage provider not found")
    return provider
```

- [ ] **步骤 1：创建 schemas/storage_provider.py**
- [ ] **步骤 2：创建 db/storage_provider_crud.py**
- [ ] **步骤 3：创建 api/routes/storage_providers.py**
- [ ] **步骤 4：注册路由到 main.py**
- [ ] **步骤 5：Commit**

---

## Phase 15.4：OSS 核心服务

### 任务 4.1：OSS 服务抽象层

**文件：**
- 创建：`backend/app/core/oss_service.py`
- 修改：`backend/app/config.py`（增加 OSS 配置项）

```python
# backend/app/config.py - 增加：
# OSS 存储
OSS_ENABLED: bool = False
OSS_PROVIDER: str = "aliyun"  # aliyun / aws / tencent
OSS_ACCESS_KEY: str = ""
OSS_SECRET_KEY: str = ""
OSS_BUCKET: str = ""
OSS_REGION: str = "oss-cn-hangzhou"
OSS_ENDPOINT: str = ""
OSS_CDN_URL: str = ""  # CDN 加速域名
```

```python
# backend/app/core/oss_service.py
"""OSS Service - Cloud storage abstraction layer"""
import os
import uuid
import httpx
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
from ..models.storage_provider import StorageProvider


class TestResult:
    def __init__(self, success: bool, message: str):
        self.success = success
        self.message = message


class OSSService:
    """OSS 服务 - 支持多云存储"""
    
    def __init__(self, provider: StorageProvider):
        self.provider = provider
        self._client = None
    
    def _get_client(self):
        """懒加载客户端"""
        if self._client is None:
            if self.provider.provider_type == "aliyun_oss":
                import oss2
                auth = oss2.Auth(self.provider.access_key, self.provider.secret_key)
                endpoint = self.provider.endpoint or f"https://{self.provider.region}.aliyuncs.com"
                self._client = oss2.Bucket(auth, endpoint, self.provider.bucket)
            elif self.provider.provider_type == "aws_s3":
                import boto3
                self._client = boto3.client(
                    's3',
                    aws_access_key_id=self.provider.access_key,
                    aws_secret_access_key=self.provider.secret_key,
                    endpoint_url=self.provider.endpoint,
                    region_name=self.provider.region
                )
            # 腾讯云 COS 可类似扩展
        return self._client
    
    async def upload(self, local_path: Path, prefix: str = "ops-video/") -> str:
        """上传文件，返回公开 URL"""
        key = f"{prefix}{uuid.uuid4().hex}_{local_path.name}"
        
        if self.provider.provider_type == "aliyun_oss":
            client = self._get_client()
            client.put_object_from_file(key, str(local_path))
        
        elif self.provider.provider_type == "aws_s3":
            client = self._get_client()
            client.upload_file(str(local_path), self.provider.bucket, key)
        
        # 返回 URL
        if self.provider.cdn_url:
            return f"{self.provider.cdn_url}/{key}"
        elif self.provider.endpoint:
            return f"https://{self.provider.bucket}.{self.provider.endpoint}/{key}"
        else:
            return f"https://{self.provider.bucket}.oss-{self.provider.region}.aliyuncs.com/{key}"
    
    async def download_url_to_local(self, url: str, local_path: Path) -> Path:
        """从 URL 下载到本地"""
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.write_bytes(resp.content)
        return local_path
    
    async def generate_signed_url(self, key: str, expires_hours: int = 24) -> str:
        """生成临时访问 URL"""
        if self.provider.provider_type == "aliyun_oss":
            client = self._get_client()
            return client.sign_url('GET', key, expires_hours * 3600)
        elif self.provider.provider_type == "aws_s3":
            client = self._get_client()
            return client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.provider.bucket, 'Key': key},
                ExpiresIn=expires_hours * 3600
            )
    
    def delete(self, key: str) -> bool:
        """删除文件"""
        try:
            if self.provider.provider_type == "aliyun_oss":
                client = self._get_client()
                client.delete_object(key)
            elif self.provider.provider_type == "aws_s3":
                client = self._get_client()
                client.delete_object(Bucket=self.provider.bucket, Key=key)
            return True
        except Exception:
            return False


async def test_storage_connection(provider: StorageProvider) -> TestResult:
    """测试存储连接"""
    try:
        service = OSSService(provider)
        if provider.provider_type == "aliyun_oss":
            client = service._get_client()
            # 尝试列出 1 个对象
            list(client.list_objects(max_keys=1))
            return TestResult(success=True, message="连接成功")
        elif provider.provider_type == "aws_s3":
            client = service._get_client()
            client.list_objects_v2(Bucket=provider.bucket, MaxKeys=1)
            return TestResult(success=True, message="连接成功")
        else:
            return TestResult(success=False, message=f"Unsupported provider: {provider.provider_type}")
    except Exception as e:
        return TestResult(success=False, message=str(e))
```

- [ ] **步骤 1：更新 config.py 增加 OSS 配置**
- [ ] **步骤 2：创建 oss_service.py**
- [ ] **步骤 3：验证 import python -c "from app.core.oss_service import OSSService; print('OK')"**
- [ ] **步骤 4：Commit**

---

## Phase 15.5：Provider 改造 - 云端 URL 自动持久化

### 任务 5.1：WanxProvider 改造

**文件：**
- 修改：`backend/app/providers/wanx_provider.py`

```python
# 在 WanxProvider.generate() 返回结果前增加：
# 原代码返回 result.file_paths（本地路径）
# 改造后：如果有活跃 OSS，上传到 OSS 并设置 result.oss_url

from ..core.oss_service import OSSService
from ..db.session import get_db
from ..db.storage_provider_crud import storage_provider_crud

# 在 generate 方法中，生成成功后：
if settings.OSS_ENABLED:
    db = next(get_db())
    active_storage = storage_provider_crud.get_active(db)
    if active_storage:
        oss = OSSService(active_storage)
        oss_url = await oss.upload(file_path, prefix="images/")
        # 记录到 result
        result.oss_urls.append(oss_url)
```

- [ ] **步骤 1：修改 wanx_provider.py 增加 OSS 上传逻辑**
- [ ] **步骤 2：同样修改 wan_video_provider.py**
- [ ] **步骤 3：更新 GenerationResult schema 增加 oss_urls 字段**
- [ ] **步骤 4：测试验证**
- [ ] **步骤 5：Commit**

---

## Phase 15.6：视频合成重构 - 多 clip 拼接

### 任务 6.1：I2VComposer 重写

**文件：**
- 修改：`backend/app/services/i2v_composer.py`

```python
# 核心改动：compose() 方法改为遍历所有 panels
async def compose_episode(
    self,
    panels: List[Dict[str, Any]],
    storyboard: List[Dict],
    bgm_path: Optional[Path] = None,
    tts_paths: List[Path] = None,
    sfx_paths: List[Path] = None,
    resolution: tuple = (1080, 1920),
    fps: int = 24,
) -> Path:
    """多分镜→多clip→拼接成片"""
    
    # Step 1: 为每个 panel 生成对应时长的 clip
    clips = []
    for i, panel in enumerate(panels):
        clip = await self._generate_panel_clip(
            panel=panel,
            storyboard_panel=storyboard[i] if i < len(storyboard) else {},
            target_duration=panel.get("duration", 5),
        )
        clips.append(clip)
    
    # Step 2: FFmpeg concat 所有 clips（可加 crossfade）
    final_video = self._concat_clips_with_transition(clips, transition="crossfade", duration=0.5)
    
    # Step 3: 混音（TTS + BGM + SFX）
    return self._mix_audio(final_video, bgm_path, tts_paths or [], sfx_paths or [])
```

- [ ] **步骤 1：分析现有 i2v_composer.py 结构**
- [ ] **步骤 2：重写 compose_episode 方法**
- [ ] **步骤 3：新增 _generate_panel_clip 辅助方法**
- [ ] **步骤 4：新增 _concat_clips_with_transition 方法**
- [ ] **步骤 5：更新 _mix_audio 方法适配多 clip**
- [ ] **步骤 6：编写测试**
- [ ] **步骤 7：Commit**

---

## Phase 15.7：Task 层级改造

### 任务 7.1：Task 支持章节标识

**文件：**
- 修改：`backend/app/models/task.py`（增加 chapter_number 字段）
- 修改：`backend/app/schemas/task.py`

```python
# task.py 增加：
chapter_number = Column(Integer, nullable=True)  # 第几章
is_chapter = Column(Boolean, default=False, nullable=False)  # 是否为章节级任务
```

- [ ] **步骤 1：更新 Task 模型**
- [ ] **步骤 2：更新 Task schemas**
- [ ] **步骤 3：创建迁移 012_add_chapter_fields.py**
- [ ] **步骤 4：Commit**

---

## Phase 15.8：前端层

### 任务 8.1：角色卡管理面板

**文件：**
- 创建：`frontend/src/components/character-card-manager.tsx`
- 修改：`frontend/src/app/projects/[id]/page.tsx`

- [ ] **步骤 1：创建角色卡管理组件**
- [ ] **步骤 2：集成到项目详情页**
- [ ] **步骤 3：三视图上传功能**
- [ ] **步骤 4：Commit**

### 任务 8.2：存储管理页面

**文件：**
- 创建：`frontend/src/app/storage/page.tsx`
- 创建：`frontend/src/lib/api/storage.ts`

- [ ] **步骤 1：创建 storage API client**
- [ ] **步骤 2：创建存储管理页面**
- [ ] **步骤 3：连接测试 UI**
- [ ] **步骤 4：激活/切换存储 UI**
- [ ] **步骤 5：Commit**

### 任务 8.3：章节列表视图

**文件：**
- 修改：`frontend/src/components/workflow-waterfall.tsx`
- 修改：`frontend/src/app/projects/[id]/page.tsx`

- [ ] **步骤 1：更新章节列表展示**
- [ ] **步骤 2：多章节切换**
- [ ] **步骤 3：每章独立进度条**
- [ ] **步骤 4：Commit**

---

## Phase 15.9：全链路测试 + 文档

### 任务 9.1：集成测试

**文件：**
- 创建：`backend/tests/test_character_cards.py`
- 创建：`backend/tests/test_storage_providers.py`
- 修改：`backend/tests/test_e2e_manga.py`（适配章节模式）

- [ ] **步骤 1：编写角色卡 CRUD 测试**
- [ ] **步骤 2：编写存储管理测试**
- [ ] **步骤 3：编写多 clip 视频合成测试**
- [ ] **步骤 4：更新 E2E 测试**
- [ ] **步骤 5：运行全量测试 python -m pytest tests/ -v**
- [ ] **步骤 6：Commit**

### 任务 9.2：更新 PROGRESS.md

**文件：**
- 修改：`PROGRESS.md`

- [ ] **步骤 1：更新开发进度文档**
- [ ] **步骤 2：Commit**

---

## Phase 16：尾帧延长（后续）

### 任务 16.1：WanVideoProvider extend() 方法

- [ ] **步骤 1：实现尾帧提取**
- [ ] **步骤 2：实现 extend API 调用**
- [ ] **步骤 3：场景识别（同 scene_id 连续 panels 启用尾帧链）**
- [ ] **步骤 4：测试验证**
- [ ] **步骤 5：Commit**

---

## 执行总结

| Phase | 内容 | 优先级 | 依赖 | 预计耗时 |
|-------|------|--------|------|---------|
| 15.1 | 数据模型 | P0 | 无 | 1h |
| 15.2 | 数据库迁移 | P0 | 15.1 | 30m |
| 15.3 | API 层 | P0 | 15.2 | 2h |
| 15.4 | OSS 服务 | P0 | 15.1 | 1h |
| 15.5 | Provider 改造 | P1 | 15.4 | 1.5h |
| 15.6 | 视频多 clip 拼接 | P1 | 15.5 | 2h |
| 15.7 | Task 章节标识 | P1 | 15.1 | 30m |
| 15.8 | 前端 | P2 | 15.3 | 4h |
| 15.9 | 测试+文档 | P2 | 15.1-15.8 | 2h |
| 16.x | 尾帧延长 | P3 | 15.6 | 2h |

---

**计划已完成并保存到 `docs/superpowers/plans/2026-05-11-series-architecture-refactor.md`。两种执行方式：**

**1. 子代理驱动（推荐）** - 每个任务调度一个新的子代理，任务间进行审查，快速迭代

**2. 内联执行** - 在当前会话中使用 executing-plans 执行任务，批量执行并设有检查点

**选哪种方式？**