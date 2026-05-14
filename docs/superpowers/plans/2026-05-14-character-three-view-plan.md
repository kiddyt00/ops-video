# 角色三视图（Character Three-View）实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 在现有 CharacterCard 上实现三视图生成服务 + API + 前端展示

**架构：**
- 后端新增 CharacterThreeViewService，负责从 story 同步角色卡、调用 LLM 生成角度描述、调用图片模型生成三张视图图
- API 扩展现有 /character-cards 路由，新增 sync / three-view / batch 端点
- 前端新增 ThreeViewCard 组件 + ThreeViewGallery 组件，在角色卡管理页面集成三视图画廊视图

**技术栈：** FastAPI + SQLAlchemy + LLM/Image Providers (Wanx/SiliconFlow), Next.js + shadcn/ui + TanStack Query

---

### 任务 1：CharacterThreeViewService 核心服务

**文件：**
- 创建：`backend/app/services/character_three_view_service.py`
- 创建：`backend/tests/test_character_three_view.py`
- 参考：`backend/app/services/character_context.py`（角色卡查询模式）
- 参考：`backend/app/services/generator_services/image_generator_service.py`（图片生成模式）

**步骤：**

- [ ] **编写失败的测试** — service 初始化 + sync_cards_from_story（4个测试用例）
- [ ] **运行测试确认失败**
- [ ] **实现 CharacterThreeViewService.sync_cards_from_story**
- [ ] **运行测试确认通过**
- [ ] **Commit**

- [ ] **编写测试** — generate_three_view（mock LLM + ImageProvider）
- [ ] **运行测试确认失败**
- [ ] **实现 generate_three_view + _build_angle_prompt**
- [ ] **运行测试确认通过**
- [ ] **编写测试 — generate_all_three_views**
- [ ] **实现 generate_all_three_views**
- [ ] **运行全部测试 + Commit**

---

### 任务 2：API 端点

**文件：**
- 修改：`backend/app/api/routes/character_cards.py`
- 追加：`backend/tests/test_character_three_view.py`（API 测试）

**步骤：**

- [ ] **编写测试** — sync / three-view / batch 三个端点
- [ ] **实现 API 端点**（sync、/{card_id}/three-view、/generate-all-three-views）
- [ ] **运行测试确认通过**
- [ ] **Commit**

---

### 任务 3：前端 API hooks

**文件：**
- 修改：`frontend/src/lib/api/character-cards.ts`
- 创建：`frontend/src/hooks/use-character-three-view.ts`

**步骤：**

- [ ] **扩展 API 客户端** — 追加 sync / generateThreeView / generateAllThreeViews
- [ ] **创建 hooks** — useSyncCharacterCards / useGenerateThreeView / useGenerateAllThreeViews
- [ ] **Commit**

---

### 任务 4：ThreeViewCard 组件

**文件：**
- 创建：`frontend/src/components/three-view-card.tsx`

**步骤：**

- [ ] **创建 ThreeViewCard 组件** — 三图并排 + 生成按钮 + 描述
- [ ] **Commit**

---

### 任务 5：ThreeViewGallery + CharacterCardManager 集成

**文件：**
- 创建：`frontend/src/components/three-view-gallery.tsx`
- 修改：`frontend/src/components/character-card-manager.tsx`

**步骤：**

- [ ] **创建 ThreeViewGallery 组件** — 网格布局 + 同步按钮 + 批量生成按钮
- [ ] **集成到 CharacterCardManager** — 画廊视图 + 表单三视图 URL 改为可选
- [ ] **Commit**

---

### 任务 6：最终验证

**文件：**
- 验证：`backend/app/main.py`

**步骤：**

- [ ] **确认路由已注册** — 新端点在现有 character_cards 路由上扩展
- [ ] **运行全量测试**
- [ ] **最终 Commit + Push** — CI/CD 自动部署
