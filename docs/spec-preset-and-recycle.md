# 设计规格：预设模板 + 回收站

## 功能1：生成参数预设模板（阶段级）

### 后端

**数据库迁移**：
- 新建 `preset_templates` 表：
  - id (UUID, PK)
  - name (String 100, not null)
  - description (Text, nullable)
  - stage (String 50, not null) — 对应 script/storyboard/image/audio/video
  - parameters (JSON, not null) — 存储该阶段的参数键值对
  - is_system (Boolean, default false) — 系统预设不可删除
  - created_at, updated_at (继承 BaseModel)

**API 路由** `/api/v1/presets`：
- `GET /` — 列表（支持 `?stage=xxx` 过滤）
- `POST /` — 创建（name, description, stage, parameters）
- `PUT /{id}` — 更新（系统预设不可改）
- `DELETE /{id}` — 删除（系统预设不可删）
- `POST /{id}/apply` — 应用预设到项目（可选，也可前端直接传 parameters）

**系统预设数据**（迁移脚本插入，is_system=true）：

1. 日系漫画标准
   - script: {style: manga, language: zh}
   - image: {style: 日系赛璐璐, resolution: 512x768}
   - audio: {voice: zh-CN-XiaoxiaoNeural, speed: 1.0, bgm_style: cheerful}
   - video: {fps: 24, resolution: 720p, transition: fade}

2. 宫崎骏/吉卜力
   - script: {style: manga, language: zh}
   - image: {style: 吉卜力, resolution: 1024x1024}
   - audio: {voice: zh-CN-XiaoyiNeural, speed: 0.9, bgm_style: ambient}
   - video: {fps: 24, resolution: 720p, transition: fade}

3. 赛博朋克
   - script: {style: realistic, language: zh}
   - image: {style: 赛博朋克, resolution: 768x512}
   - audio: {voice: zh-CN-YunxiNeural, speed: 1.1, bgm_style: dramatic}
   - video: {fps: 30, resolution: 1080p, transition: slide}

4. 短视频快节奏
   - script: {style: manga, language: zh}
   - image: {style: Q版萌系, resolution: 512x768}
   - audio: {voice: zh-CN-YunxiNeural, speed: 1.3, bgm_style: cheerful}
   - video: {fps: 30, resolution: 720p, transition: zoom}

5. 电影质感
   - script: {style: realistic, language: zh}
   - image: {style: 厚涂电影风, resolution: 1024x1024}
   - audio: {voice: zh-CN-YunjianNeural, speed: 0.9, bgm_style: dramatic}
   - video: {fps: 24, resolution: 1080p, transition: fade}

6. 国风水墨
   - script: {style: manga, language: zh}
   - image: {style: 国风水墨, resolution: 768x512}
   - audio: {voice: zh-CN-XiaoxiaoNeural, speed: 1.0, bgm_style: ambient}
   - video: {fps: 24, resolution: 720p, transition: fade}

**文件结构**：
- `backend/app/models/preset_template.py` — 模型
- `backend/app/api/routes/presets.py` — 路由
- `backend/app/db/migrations/003_add_preset_templates.py` — 迁移脚本
- `backend/tests/test_presets.py` — 测试（CRUD + 系统预设保护）

### 前端

**新增文件**：
- `frontend/src/types/preset.ts` — 类型定义
- `frontend/src/lib/api/presets.ts` — API 客户端
- `frontend/src/hooks/use-presets.ts` — React Query hooks
- `frontend/src/components/preset-selector.tsx` — 预设选择器（下拉菜单）
- `frontend/src/components/preset-manager.tsx` — 预设管理弹窗（CRUD）

**UI 改动**：
- `frontend/src/components/parameter-panel.tsx` — 顶部加预设选择器
- 选择预设后自动填充表单值
- 预设管理弹窗：列出预设，系统预设只读，用户预设可编辑/删除

---

## 功能2：历史记录 + 回收站

### 后端

**模型改动**：
- `backend/app/models/project.py` — Project 加 `deleted_at` 字段（DateTime, nullable）

**API 改动** `backend/app/api/routes/projects.py`：
- `GET /api/v1/projects` — 默认过滤 `deleted_at IS NULL`，支持 `?include_deleted=true`
- `PATCH /api/v1/projects/{id}/restore` — 恢复（deleted_at = NULL）
- `DELETE /api/v1/projects/{id}/permanent` — 永久删除（硬删除）
- 现有 `DELETE /{id}` — 改为软删除（设置 deleted_at = now()）

**定时清理**：
- 在 `app/core/cleanup.py` 新增清理函数
- lifespan startup 中注册定时任务（或 cron job）
- 删除 `deleted_at > 30天` 的项目

**测试**：
- `backend/tests/test_soft_delete.py` — 软删除/恢复/永久删除/自动清理

### 前端

**改动文件**：
- `frontend/src/types/project.ts` — Project 加 `deleted_at?: string`
- `frontend/src/lib/api/projects.ts` — 加 restore / permanentDelete 方法，列表加 include_deleted 参数
- `frontend/src/hooks/use-projects.ts` — 加 showDeleted 状态和对应 API 调用
- `frontend/src/app/projects/page.tsx` — 列表页加"显示已删除"开关
- 已删除项目灰显（opacity-50），操作栏变为"恢复"和"永久删除"
- 永久删除前弹出二次确认（危险警告）

---

## 实现要求

1. 先写测试（TDD），再写实现
2. 每个子任务完成后 commit + push
3. 所有测试必须通过（后端 pytest，前端 npm test）
4. 数据库迁移要兼容 SQLite（测试用）和 PostgreSQL（生产用）
5. 遵循现有代码风格（SQLAlchemy ORM, FastAPI, React + shadcn/ui）
6. 完成后运行全量测试验证
