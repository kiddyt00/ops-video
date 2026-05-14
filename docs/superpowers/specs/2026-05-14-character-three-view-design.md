# 角色三视图（Character Three-View）设计规格

## 概述

在故事生成管线之外，提供一个独立的角色三视图生成工具。基于故事大纲中产出的角色卡、世界观、风格信息，自动生
成主要角色和重要配角的正面/侧面/背面三视图，作为后续所有分镜图片和视频生成的角色视觉基线。

## 设计目标

1. **独立于管线**：三视图生成不强制嵌入工作流阶段，用户可在任意时机触发
2. **一次生成，全局一致**：三视图存入 CharacterCard 后，所有下游生图自动引用
3. **覆盖主要角色**：从 story.characters 的 role 字段自动识别主角/重要配角
4. **Web 端可视化**：三图并排展示，支持查看/重生成

## 数据流

```
故事生成管线（独立）：
  灵感 → 故事大纲 → 世界观 → 核心蓝图 → 章节大纲 → 剧本 → 分镜 → 生图...

角色三视图（独立触发）：
  角色卡(name/description/traits)
  + 世界观(setting/time_period/rules)
  + 风格标签(style_tags)
        ↓
  LLM → 分角度角色外观描述
        ↓
  图片模型 × 3 → 正面/侧面/背面图
        ↓
  CharacterCard.{front/side/back}_view_url 更新
        ↓
  下游：CharacterContextBuilder 自动注入 → 分镜/生图/视频一致
```

## 角色筛选规则

从 `Story.characters[]`（JSON 数组）中筛选需要生成三视图的角色：

| role 值             | 是否生成三视图 |
|---------------------|---------------|
| 主角 / protagonist | ✅ |
| 反派 / antagonist | ✅ |
| 导师 / mentor | ✅ |
| 伙伴 / companion | ✅ |
| 配角 / supporting | ✅（10 个以内主要配角）|
| 路人 / extra | ❌ |

判断逻辑：
- `role` 包含"主角"、"反派"、"导师"、"伙伴" → 生成
- `role` 包含"配角" → 取 story.characters 中前 10 个配角生成（按出场顺序）
- 其余跳过

## API 设计

扩展现有 `/character-cards` 路由：

### 批量创建角色卡

```
POST /api/v1/projects/{pid}/character-cards/sync
```

从 `Story.characters` 读取角色列表，按 role 筛选主要角色，自动创建
CharacterCard（如已存在则跳过）。返回新创建的卡片列表。

请求体：无（从项目 story 读取）
响应：
```json
{
  "created": 3,
  "skipped": 2,
  "cards": [...]
}
```

### 触发三视图生成

```
POST /api/v1/projects/{pid}/character-cards/{cid}/three-view
```

触发单个角色的三视图生成流程：
1. 查询角色卡 + 项目 story（worldbuilding + style_tags）
2. LLM 生成分角度外观描述（正/侧/背）
3. 图片模型按角度生成 3 张图
4. 上传到 OSS/本地存储
5. 更新 CharacterCard.front_view_url / side_view_url / back_view_url

请求体：
```json
{
  "style_tags": ["写实", "古风", "仙侠"],
  "strict": true
}
```

`strict: true` 表示后续分镜生图时必须严格遵循三视图设定。
`strict: false`（默认）表示作为参考，生图时允许微调。

响应：异步任务（返回 task_id）

```
GET /api/v1/projects/{pid}/character-cards/{cid}/three-view/status
```

查询三视图生成状态。

### 批量生成三视图

```
POST /api/v1/projects/{pid}/character-cards/generate-all-three-views
```

对所有已 sync 的角色卡依次生成三视图。按角色名 → 图片模型的顺序逐个提交任务，不相互依赖。

## 数据库

已有 CharacterCard 模型已包含三视图字段：

```python
class CharacterCard(BaseModel):
    name = Column(String(255))
    description = Column(Text)
    front_view_url = Column(String(500))  # 正面图 URL
    side_view_url  = Column(String(500))  # 侧面图 URL
    back_view_url  = Column(String(500))  # 背面图 URL
    traits = Column(JSON)                 # 外观特征
    reference_images = Column(JSON)       # 额外参考图
```

无需新增模型或迁移。

## 后端服务

### CharacterThreeViewService

新增 `backend/app/services/character_three_view_service.py`

**方法**：

1. `sync_cards_from_story(project_id)` — 从 story.characters 同步创建角色卡
2. `generate_three_view(project_id, card_id, style_tags, strict)` — 单角色三视图生成
3. `generate_all_three_views(project_id)` — 批量生成
4. `_build_character_description_prompt(card, worldbuilding, style_tags)` — LLM 角度描述 prompt
5. `_dispatch_image_generation(angle_description, angle)` — 按角度生图

### LLM Prompt 模板

```
你是一位专业的角色设计师。请为以下角色生成正/侧/背三个角度的外观描述。

角色名: {name}
角色设定: {description}
外貌特征: {traits}
世界观: {worldbuilding.setting} / {worldbuilding.time_period}
风格: {style_tags}

请提供三个角度的描述，每个角度包含：
- 发型、发色
- 脸型、五官
- 服装（正面/侧面/背面细节不同）
- 配饰
- 体型特征

输出 JSON:
{
  "front": "...",
  "side": "...",
  "back": "..."
}
```

### 图片模型 Prompt

复用已有的图片 Provider（Wanx / SiliconFlow），prompt 结构：

```
{angle_description}, {style_tags}, {worldbuilding.setting},
正面/侧面/背面全身照, 角色设计图, 白色背景, 高清
```

## Web 前端

### ThreeViewCard 组件

新建 `frontend/src/components/three-view-card.tsx`

布局：
```
┌──────────────────────────────────────────────┐
│  角色名                    [角色定位 Badge]   │
│                                              │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐      │
│  │  正面    │  │  侧面    │  │  背面    │      │
│  │  img    │  │  img    │  │  img    │      │
│  │  front  │  │  side   │  │  back   │      │
│  └─────────┘  └─────────┘  └─────────┘      │
│                                              │
│  [生成三视图] 或 [重新生成]                   │
│  角色描述: ...                                │
└──────────────────────────────────────────────┘
```

- 三张图统一高度，等比缩放
- 图未生成时显示占位图 + 生成按钮
- 每张图可点击放大（使用已有 artifact-viewer 组件）
- loading spinner 按角色独立（不阻塞其他角色）

### ThreeViewGallery 组件

新建 `frontend/src/components/three-view-gallery.tsx`

在角色卡页面中展示所有角色三视图的网格布局：
```
┌───────────┐ ┌───────────┐ ┌───────────┐
│ 角色A      │ │ 角色B      │ │ 角色C      │
│ 三视图     │ │ 三视图     │ │ 三视图     │
│ [已生成]   │ │ [未生成]   │ │ [已生成]   │
└───────────┘ └───────────┘ └───────────┘
        ┌───────────┐
        │ 角色D      │
        │ 三视图     │
        │ [生成中...]│
        └───────────┘
```

### 角色卡页面增强

修改 `frontend/src/components/character-card-manager.tsx`：
- 角色卡片展示区集成 ThreeViewCard
- 新增「从故事同步角色」按钮（调用 /sync 端点）
- 新增「批量生成三视图」按钮
- 三视图区域可折叠/展开

### 角色卡 Tab 调整

在项目详情页 `page.tsx` 的 Tab 中，characters tab 内容更新为展示角色三视图的画廊视图而非列表视图。

## 下游一致性保障

三视图写入 CharacterCard 后，现有 CharacterContextBuilder 已自动读取卡片数据注入生图 prompt。无需额外改动。

enhancement：当 `strict=true` 时，`enrich_storyboard_prompt()` 可在 prompt 尾部追加：

```
【角色一致性要求】角色"{name}"必须严格按照以下角色设计图创作：
正面参考: {front_view_url}
侧面参考: {side_view_url}
背面参考: {back_view_url}
不得改变外观设计。
```

## 实现范围

### 后端（5 项）
1. `backend/app/services/character_three_view_service.py` — 核心服务
2. 修改 `backend/app/api/routes/character_cards.py` — 新增 3 个端点
3. LLM prompt 模板注册到 prompt 系统
4. 单元测试：`backend/tests/test_character_three_view.py`
5. 集成测试：三视图生成 + sync + 批量

### 前端（4 项）
1. `frontend/src/components/three-view-card.tsx`
2. `frontend/src/components/three-view-gallery.tsx`
3. 修改 `character-card-manager.tsx` — 集成三视图
4. `frontend/src/hooks/use-character-three-view.ts` — API hook

## 非范围

- 不修改工作流阶段（STAGE_ORDER）
- 不修改 TaskStage 枚举
- 不修改数据库模型
- 不修改 CharacterContextBuilder（只读消费端）
