# Ops-Video 开发进度与后续任务

## 已完成

### Phase 1: 基础架构 ✅
- 项目骨架（FastAPI + Next.js + PostgreSQL）
- 数据库 Schema（Project, Task, File, VariantGroup, TaskStatusLog）
- Docker 配置
- **Commit**: `1cab5d5`

### Phase 2: 核心功能 ✅
- Project/Task/File/Variant CRUD API
- LLM Provider（脚本/分镜生成）
- ComfyUI Provider（图片生成）
- Generator Services
- **Commit**: `f54dc61`

### Phase 3: 工作流引擎 ✅
- Workflow Service（阶段推进/回滚）
- Traceability Service（版本对比/谱系追踪）
- Workflow API（advance, rollback, compare, lineage）
- 18 个基础测试
- **Commit**: `3c94c39`

### Phase 4: 前端界面 (MVP) ✅
- shadcn/ui + Tailwind CSS + Dark Mode
- 三栏布局（左侧阶段导航 / 中间画布 / 右侧参数面板）
- 项目列表页面（创建 / 删除 / 卡片展示）
- 项目详情/工作流页面（任务列表 / 工作流状态 / 阶段推进）
- API 客户端层（Axios + React Query Hooks）
- **Commit**: `e390c70`

### Phase 5: 集成测试 ✅
- 42 个端到端集成测试（in-memory SQLite + TestClient）
  - 项目/任务/文件/变体 CRUD 全覆盖
  - 完整工作流测试（script → storyboard → image → audio → video）
  - 变体选择与对比测试
  - 文件谱系追踪测试
  - 边界条件与错误处理测试
- 修复 workflow_service 中 variant_group_crud 类型错误
- 修复 File/VariantGroup 模型外键歧义
- **Commit**: `773d08e`

### Phase 6: 音频与视频合成 ✅
- TTS 服务（edge-tts，支持多声音/速率/面板批量合成）
- BGM 服务（numpy/scipy 合成，支持 ambient/dramatic/cheerful/sad 情绪）
- SFX 服务（numpy/scipy 合成，支持 whoosh/impact/sparkle/wind/rain/thunder）
- 视频合成服务（FFmpeg：图片→视频片段→拼接→音频混合→最终输出）
- Generators API 注册 tts/bgm/video_composer
- 41 个测试覆盖所有新服务
- **Commit**: `3a260af`

### Phase 7: 前端集成测试和端到端联调 ✅
- 前端测试框架（vitest + testing-library）
- API 集成测试（覆盖所有 frontend hooks）
- E2E 工作流测试脚本（backend/tests/test_e2e_workflow.py）
- 测试脚本支持跳过视频合成、保存结果等功能
- **Commit**: `bfa869c`

### Phase 8: 前端 UI 完善和功能集成 ✅
- **变体选择器组件** (`VariantPicker`): 多结果对比和选择
- **工作流进度可视化** (`WorkflowProgress`): 阶段状态可视化
- **深色模式优化**:
  - 紫色主题色 (#6366f1)
  - 成功/警告颜色变量
  - 自定义滚动条样式
  - 更好的对比度和可读性
- **后端 API 集成**:
  - use-generators hook（所有生成器类型）
  - useGenerateScript/Storyboard/Image
  - useGenerateTTS/BGM, useComposeVideo
- **Commit**: `4290df5`

### Phase 9: 部署配置优化 ✅
- **Docker 多阶段构建**:
  - 后端：builder + runtime 两阶段，减小镜像体积
  - 前端：deps + builder + runner 三阶段，独立用户运行
  - 开发 Dockerfile 支持热重载
- **环境变量管理**:
  - backend/.env.example：完整的后端配置模板
  - frontend/.env.example：前端配置模板
  - 密钥管理：生产环境密码通过环境变量注入
- **生产环境配置**:
  - Next.js standalone output + 独立用户运行
  - Uvicorn 4 workers 并发
  - docker-compose.prod.yml：生产配置（健康检查、重启策略）
  - docker-compose.yml：开发配置（热重载、debug 日志）
- **健康检查**:
  - 后端：/health 端点检查
  - 前端：wget 检查
  - PostgreSQL: pg_isready 检查
- **Commit**: `853e409`

### Phase 10: 性能优化与监控 ✅
- **Redis 缓存集成**:
  - Redis 客户端封装（app/core/redis.py）
  - 缓存装饰器用于函数结果缓存
  - 启动/关闭生命周期管理
- **结构化日志系统**:
  - JSON 格式日志（python-json-logger）
  - 自定义 Formatter（时间戳、位置信息）
  - Request 中间件（X-Request-ID、X-Process-Time）
  - 日志轮转（10MB，5 个备份）
- **健康检查增强**:
  - /health: 综合状态检查（数据库、Redis）
  - /ready: 就绪探针（k8s 适用）
  - 降级状态支持
- **前端代码分割**:
  - Dynamic import 工具（lib/dynamic-import.ts）
  - Next.js 配置：removeConsole、optimizePackageImports
- **Commit**: 本次

### Phase 11: 安全与权限管理 ✅
- **JWT 认证系统**:
  - User 模型（email/username/password/role）
  - RefreshToken 模型用于 Token 轮换
  - JWT 工具：Token 生成/解码、密码哈希
  - 认证路由：/register, /login, /refresh, /me, /logout
- **路由权限保护**:
  - get_current_user 依赖注入
  - get_current_admin_user 管理员专属
  - require_role 装饰器工厂
  - 可选用户认证支持
- **API Rate Limiting**:
  - 基于 Redis 的滑动窗口限流
  - 每用户或每 IP 维度限制
  - 60 请求/分钟默认，100 爆发
  - X-RateLimit-* 响应头
- **安全中间件**:
  - 安全 Headers（CSP, HSTS, X-Frame-Options）
  - XSS 防护中间件
  - 严格 CORS 配置
  - SQL 注入模式检测
- **数据库迁移**:
  - 002_add_users.py: users, refresh_tokens 表
- **Commit**: `c75fef7`

### Phase 12: 多 provider 图片生成 ✅
- 支持 ComfyUI/DashScope/SiliconFlow 三provider
- 通义万相（DashScope）集成
- FLUX.1 (SiliconFlow) 集成
- **Commit**: `18ad73c`

### Phase 13: 移除 ComfyUI，默认 DashScope ✅
- 移除 ComfyUI provider 依赖
- 默认使用 DashScope Wanx
- 简化配置
- **Commit**: `e50fe68`

### Phase 14: 数据分析与报告 ✅
- **视频分析服务** (`backend/app/services/video_analyzer.py`):
  - 使用 mutagen 库分析视频元数据
  - 提取时长、帧率、分辨率、编码格式
  - 自动计算帧数
  - 文件创建时自动分析
- **分析 API 路由** (`backend/app/api/routes/analytics.py`):
  - `GET /api/v1/analytics/projects/{id}/stats` - 项目统计
  - `GET /api/v1/analytics/projects/{id}/dashboard` - 仪表盘数据
  - `GET /api/v1/analytics/projects/{id}/report` - JSON 报告导出
  - `GET /api/v1/analytics/projects/{id}/videos` - 视频详情
  - `POST /api/v1/analytics/files/{id}/analyze` - 手动分析视频
- **前端仪表盘** (`frontend/src/components/dashboard.tsx`):
  - 项目概览卡片（任务总数、完成率、文件数、存储）
  - 视频统计卡片（总时长、总帧数、帧率、分辨率）
  - 阶段进度条（各阶段成功率）
  - 文件类型分布图
  - 最近任务列表
- **导出功能**:
  - JSON 格式报告下载
  - MP4 视频下载（已有端点）
- **前端 Hook** (`frontend/src/hooks/use-analytics.ts`):
  - useProjectStats
  - useDashboardData
  - useExportReport
  - useAnalyzeVideo
- **Commit**: `b3c0036`

### Phase 15: 功能完善与优化 ✅

#### Phase 15.1: CharacterCard 和 StorageProvider 模型 ✅
- CharacterCard 模型（角色名、描述、图片 URL、项目关联）
- StorageProvider 模型（类型、配置、是否默认、项目关联）
- SQLAlchemy ORM 定义 + Pydantic Schema
- **新增文件**:
  - `backend/app/models/character_card.py`
  - `backend/app/models/storage_provider.py`
  - `backend/app/schemas/character_card.py`
  - `backend/app/schemas/storage_provider.py`
- **Commit**: `0856d11`

#### Phase 15.2: 数据库迁移 010, 011 ✅
- Alembic migration 010: character_cards 表
- Alembic migration 011: storage_providers 表
- 外键关联、索引、默认值
- **新增文件**:
  - `backend/app/db/migrations/versions/010_add_character_cards.py`
  - `backend/app/db/migrations/versions/011_add_storage_providers.py`
- **Commit**: `0856d11`

#### Phase 15.3: 角色卡和存储管理 CRUD API ✅
- CharacterCard CRUD（创建/查询/更新/删除）
- StorageProvider CRUD（创建/查询/更新/删除/设默认）
- 路由注册到 FastAPI
- **新增文件**:
  - `backend/app/api/routes/character_cards.py`
  - `backend/app/api/routes/storage_providers.py`
  - `backend/app/db/character_card_crud.py`
  - `backend/app/db/storage_provider_crud.py`
- **修改文件**:
  - `backend/app/main.py`
- **Commit**: `e382e92`

#### Phase 15.4: OSS 核心服务 ✅
- OSS Service 抽象层（支持多云存储）
- 上传/下载/删除/列表操作
- 配置驱动（Endpoint, Access Key, Bucket）
- **新增文件**:
  - `backend/app/core/oss_service.py`
- **Commit**: `d67e34d`

#### Phase 15.5: Provider 自动上传 OSS ✅
- BaseProvider 集成 OSS 自动上传
- WanVideoProvider / WanxProvider 生成文件后自动上传
- 上传失败降级处理
- **修改文件**:
  - `backend/app/providers/base_provider.py`
  - `backend/app/providers/wan_video_provider.py`
  - `backend/app/providers/wanx_provider.py`
- **Commit**: `78fee6f`

#### Phase 15.6: 多 clip 视频拼接引擎 ✅
- I2VComposer 多 clip 拼接引擎
- 支持多个片段按顺序拼接
- 转场效果支持
- 17 个测试覆盖拼接逻辑
- **新增文件**:
  - `backend/app/services/i2v_composer.py`
  - `backend/tests/test_i2v_composer.py`
- **Commit**: `3a7057b`

#### Phase 15.7: Task 章节标识 ✅
- Task 模型增加 chapter 字段
- 章节维度的任务分组和查询
- **Commit**: 包含在 Phase 15.3 API 更新中

#### Phase 15.8: 前端（角色卡面板、存储管理、章节视图） ✅

##### Phase 15.8.1: 角色卡管理面板
- CharacterCardManager 组件
- 角色卡列表/创建/编辑/删除
- use-character-cards hook
- **新增文件**:
  - `frontend/src/components/character-card-manager.tsx`
  - `frontend/src/hooks/use-character-cards.ts`
  - `frontend/src/lib/api/character-cards.ts`
  - `frontend/src/types/character-card.ts`
- **Commit**: `b868b43`

##### Phase 15.8.2: 存储管理页面
- 存储管理页面（/storage）
- 存储 Provider 列表/创建/配置
- 导航栏入口
- **新增文件**:
  - `frontend/src/app/storage/page.tsx`
  - `frontend/src/hooks/use-storage.ts`
  - `frontend/src/lib/api/storage.ts`
- **修改文件**:
  - `frontend/src/components/app-shell.tsx`
  - `.gitignore`
- **Commit**: `b73c5b2`

##### Phase 15.8.3: 章节列表和详情页
- 章节列表视图（chapters-list 组件）
- 章节详情页（/projects/[id]/chapters/[chapterId]）
- use-chapters hook + chapters API 客户端
- **新增文件**:
  - `frontend/src/components/chapters-list.tsx`
  - `frontend/src/hooks/use-chapters.ts`
  - `frontend/src/lib/api/chapters.ts`
  - `frontend/src/types/chapter.ts`
  - `frontend/src/app/projects/[id]/chapters/[chapterId]/page.tsx`
- **修改文件**:
  - `frontend/src/app/projects/[id]/page.tsx`
  - `frontend/src/hooks/index.ts`
  - `frontend/src/types/index.ts`
- **Commit**: `f99956d`

#### Phase 15.9: 集成测试（21 个新测试通过） ✅
- CharacterCard 集成测试（7 个）: 创建/查询/更新/删除/关联查询
- StorageProvider 集成测试（14 个）: CRUD/默认设置/配置验证
- I2VComposer 单元测试（17 个）: 拼接/转场/输出验证
- Phase 15 新增测试总计 38 个（21 个集成 + 17 个单元）
- 项目总测试数: 217
- **新增文件**:
  - `backend/tests/test_character_cards.py` (305 行)
  - `backend/tests/test_storage_providers.py` (356 行)
- **Commit**: `572daaa`

---

## 待完成

### Phase 16: 尾帧延长 ✅
- **WanVideoProvider extend() 方法**:
  - `extract_last_frame(clip_path)` — FFmpeg `-sseof -1` 提取尾帧
  - `extend(prev_clip_path, prompt, duration)` — 尾帧作为参考图生成续段
  - 复用现有下载 + OSS 上传管线
- **I2VComposer 场景识别与尾帧链**:
  - `group_panels_by_scene()` — 解析 storyboard scene_id，无 scene_id 时按连续性推断
  - 同一 scene 的连续 panels：首帧 generate() → 后续 extend() 链式生成
  - 不同 scene 之间独立 generate()
  - `compose_episode_with_tail_extend()` 新方法与原有 `compose_episode()` 并存
- **14 个测试覆盖**:
  - 尾帧提取（真实 FFmpeg）
  - extend() mock 测试
  - 场景分组（单/多 scene、空、边界）
  - 尾帧链端到端（单 scene 链、多 scene、无 scene_id 降级）
- **新增文件**:
  - `backend/tests/test_tail_frame_extend.py` (450+ 行)
- **修改文件**:
  - `backend/app/providers/wan_video_provider.py`
  - `backend/app/services/i2v_composer.py`
- **Commit**: `b39d3de`

### Phase 17: NovelForge 工作流扩展 ✅
- **灵感→故事→章节→剧本→分镜→图片→音频→视频完整工作流**
- **Story 数据模型**:
  - `Story` 模型：inspiration, logline, synopsis, worldbuilding, characters, themes, plot_points, chapter_outline
  - `StoryStatus` 枚举：draft/completed/archived
  - Project 与 Story 一对多关系
- **数据库迁移**:
  - `012_add_stories.py` — stories 表
- **Story API**:
  - `GET/POST/PUT/DELETE /api/v1/projects/{project_id}/story`
  - StoryCRUD 完整实现
- **StoryGeneratorService**:
  - `generate_story()` — 灵感扩展为完整故事大纲
  - `generate_chapter_outline()` — 故事划分为章节
  - JSON Schema 校验（STORY_SCHEMA, CHAPTER_OUTLINE_SCHEMA）
  - 更新 llm_provider 支持 response_format
- **工作流集成**:
  - TaskStage 新增 INSPIRATION, STORY, CHAPTER_OUTLINE
  - STAGE_ORDER 更新：INSPIRATION → STORY → CHAPTER_OUTLINE → SCRIPT → ...
  - 新增阶段处理方法：_execute_inspiration_generation, _execute_story_generation, _execute_chapter_outline_generation
- **前端故事界面**:
  - Story 编辑器组件（logline, synopsis, worldbuilding, characters 可编辑）
  - AI 生成栏（灵感输入 → 生成故事 → 生成章节）
  - 章节大纲列表编辑
  - 项目详情页新增"故事" tab
- **新增文件**:
  - `backend/app/models/story.py`
  - `backend/app/db/migrations/versions/012_add_stories.py`
  - `backend/app/schemas/story.py`
  - `backend/app/db/story_crud.py`
  - `backend/app/api/routes/stories.py`
  - `backend/app/services/generator_services/story_generator_service.py`
  - `frontend/src/types/story.ts`
  - `frontend/src/lib/api/stories.ts`
  - `frontend/src/hooks/use-stories.ts`
  - `frontend/src/components/story-editor.tsx`
- **修改文件**:
  - `backend/app/models/task.py` (TaskStage 扩展)
  - `backend/app/services/workflow_service.py` (阶段处理)
  - `backend/app/providers/llm_provider.py` (response_format 支持)
  - `frontend/src/app/projects/[id]/page.tsx` (故事 tab)
- **Commit 范围**: `fbd71b9` → `addf242` (6 commits)

### Phase 18: LLM 配置数据库化 ✅
- **架构改进**：LLM Provider 从数据库读取模型配置，替代硬编码环境变量
- **AIModel 模型扩展**：
  - 新增 `is_active` 字段（每个类别只有一个活跃模型）
  - 数据库迁移 `013_add_ai_model_is_active.py`
- **ai_model_crud 增强**：
  - `get_active(category)` — 获取活跃模型
  - `activate(model_id)` — 激活模型（同类别其他自动停用）
  - `toggle()` 标记为 deprecated
- **LLMProvider 重构**：
  - 移除 `settings.LLM_API_KEY` 等硬编码 fallback
  - `async _load_model_config()` — 每次调用动态从数据库加载
  - 无活跃模型时抛出明确错误提示
- **API 路由更新**：
  - `/toggle` 端点改为 activate 语义
  - 新增 `/activate` 端点作为显式别名
- **config.py 清理**：删除 `LLM_API_KEY`, `LLM_API_BASE_URL`, `LLM_MODEL`
- **修改文件**：
  - `backend/app/models/ai_model.py`
  - `backend/app/db/ai_model_crud.py`
  - `backend/app/providers/llm_provider.py`
  - `backend/app/config.py`
  - `backend/app/api/routes/ai_models.py`
  - `backend/app/db/migrations/versions/013_add_ai_model_is_active.py`
- **Commit**: `a004edc`

### Phase 19: 技术债务清理 ✅
- **datetime.utcnow() 弃用修复**:
  - 5 个文件：logging_config.py, security.py, user_crud.py, storage_provider_crud.py
  - `datetime.utcnow()` → `datetime.now(timezone.utc)`
  - `fromtimestamp()` 添加 `tz=timezone.utc` 修复时区比较
- **SQLite FK 依赖循环**:
  - file.py: parent_file_id + selected_file_id 添加 `use_alter=True`
- **预设模板完善**:
  - 模型添加 `is_system` 字段
  - API 系统预设保护（修改/删除 403）
  - 23 套系统预设种子（6 风格 × 3-4 阶段）
  - `main.py` 启动时自动种子
- **CharacterCard + StorageProvider 模型对齐**:
  - 重写模型匹配 migration 010/011
  - 添加 `StorageProviderType` 枚举
  - 修复 `models/__init__.py` 导入链
- **依赖安装**: oss2, boto3, edge-tts
- **Commit**: `008f0b8`

### Phase 20: 待定
- 前端预设选择器 + 管理器组件
- 前端项目回收站（软删除 UI）
- LoRA 角色一致性
- 多 Provider 路由

---

## 快速开始

### 开发模式

```bash
# 克隆项目
git clone git@github.com:kiddyt00/ops-video.git
cd ops-video

# 使用 Docker Compose 启动开发环境
docker-compose up -d

# 后端（本地开发）
cd backend
uv venv .venv && source .venv/bin/activate
uv pip install -r requirements.txt pytest
python -m pytest tests/ -v
uvicorn app.main:app --reload

# 前端（本地开发）
cd ../frontend
npm install
npm run dev
```

### 生产部署

```bash
# 使用生产配置启动
docker-compose -f docker-compose.prod.yml up -d --build

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f
```

---

## 开发规范

1. **每个子任务完成后立即 commit + push**
2. **验证先于提交**: `python -m pytest tests/ -v` 或 `npm run test`
3. **Superpowers 工作流**: brainstorming → plan → execute → verify
4. **项目目录**: `~/claude-projects/ops-video/`

---

## 当前状态

- **GitHub**: https://github.com/kiddyt00/ops-video
- **最新 Commit**: `008f0b8` - Phase 19 技术债务清理
- **分支**: main + novelforge（当前活跃）
- **总测试数**: 231+ (preset 11 passed)
- **已完成阶段**: Phase 1 ~ Phase 19
- **下一阶段**: Phase 20 - 前端预设 + 回收站
