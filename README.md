# Ops-Video

AI 漫剧/短剧自动生成平台。输入创意灵感，自动完成故事创作→剧本→分镜→生图→配音→成片的全流程。

**在线体验：** `http://49.235.108.61:8081`

---

## 功能特性

### 核心管线（8 阶段）

| 阶段 | 功能 | AI 引擎 |
|------|------|---------|
| 💡 灵感 | 创意发散，生成故事方向 | LLM |
| 📖 故事 | 完整故事大纲 + 世界观 + 角色 | LLM + 知识库注入 |
| 📑 章节大纲 | 拆解为多章节结构 + 前情提要 | LLM + 角色状态追踪 |
| 📝 剧本 | 创作漫剧剧本 | LLM |
| 🎬 分镜 | 拆解为视觉分镜 + 镜头语言 | LLM |
| 🖼️ 生图 | 生成漫画风格图片 | Wanx2.6 / SiliconFlow FLUX.1 |
| 🎵 配音 | TTS 旁白 + BGM + 音效 | edge-tts + 音频合成 |
| 🎬 成片 | 图片序列 + 音频合成视频 | FFmpeg |

### 故事创作增强

- **StoryWizard 交互式向导** — 6 步故事设定（灵感→类型→世界观→主角→金手指→关系线），含书名建议、目标读者、力量体系、楔子预览等扩展字段
- **知识库注入** — 6 个内置知识库（姓名生成/地名库/朝代模板/修仙设定/科幻设定/叙事结构），通过 `@KB{name=...}` 注入提示词
- **提示词模板** — 可编辑的模板系统，支持 `$variable` + 知识库注入，加载失败自动回退到硬编码 prompt
- **Chapter 模型** — 独立章节实体，每章独立管线推进，含 status/current_stage/video_file_id 字段

### 情节连贯性保障

- **角色状态追踪** — 每章记录每个角色的生死/位置/势力状态
- **前情提要注入** — 生成新章节时自动组装前情提要，防止角色复活/瞬间移动等矛盾
- **角色关系图** — mentor_of/rival_of/lover_of 等关系存储和查询（支持 SQLite/Neo4j 双后端）
- **角色上下文注入** — CharacterContextBuilder 将角色卡信息自动注入图片生成 prompt，确保角色外观一致
- **自动记忆提取** — 剧本/分镜生成后自动解析角色状态变化，非阻塞设计

### 生成体验

- **SSE 流式生成** — AI 边生成边推送，实时显示内容
- **GenerationPanel** — 浮动面板，打字机效果展示，支持暂停/继续/反馈
- **多结果选择与变体** — 每步骤生成多个变体，用户选择最佳，支持版本对比和谱系追踪
- **全自动模式** — "全部生成"一键跑完所有阶段

### 系统功能

- **用户系统** — JWT 认证 + RefreshToken 轮换、角色权限（管理员/用户）
- **AI 模型管理** — 数据库驱动，Web 后台管理 LLM/图片模型，支持启用/禁用/测试
- **多 Provider 路由** — ProviderRouter 三级路由策略：项目级覆盖 → 数据库活跃模型 → 硬编码回退
- **知识库管理** — 自定义知识库 CRUD
- **角色卡管理** — 三视图角色卡存储，支持角色一致性预览
- **存储管理** — S3 / OSS / COS / MinIO 等多云存储配置，支持测试连接
- **Neo4j 图数据库** — 可选，默认 SQLite，切换 `GRAPH_PROVIDER=neo4j`
- **OSS 自动上传** — 图片/视频生成后自动上传到配置的云存储
- **参数预设** — 保存和复用生成参数
- **项目分享与回收站**
- **追溯系统** — 记录所有生成参数、版本、任务历史
- **数据分析仪表盘** — 项目统计、阶段成功率、视频分析等
- **主题切换** — 深色/浅色/跟随系统
- **时区自动检测** — 自动识别用户时区并显示
- **未登录自动跳转** — 内部页面访问自动重定向到登录页
- **多 Clip 视频拼接** — I2VComposer 支持多个片段按顺序拼接 + 转场效果
- **尾帧延长** — WanVideoProvider 提取尾帧作为参考图生成续段

---

## 技术栈

### 后端
- FastAPI (Python 3.11)
- PostgreSQL + SQLAlchemy + Alembic
- Neo4j (可选图数据库，默认 SQLite)
- Redis (缓存/限流)
- SQLite (测试环境)

### 前端
- Next.js 14 (React) + TypeScript
- Tailwind CSS + shadcn/ui
- TanStack Query (数据获取)
- Zustand (状态管理)
- SSE (Server-Sent Events) 流式

### AI/Provider
- DashScope (通义万相 wan2.6 — 图片生成)
- SiliconFlow (FLUX.1 — 图片生成，兼容 OpenAI API)
- WanVideo (图生视频)
- OpenAI 兼容 API (LLM)
- edge-tts (语音合成)
- FFmpeg (视频拼接合成)

### 部署
- Docker + Docker Compose (多阶段构建)
- GitHub Actions CI/CD
- 生产环境 Nginx 反向代理 + 健康检查

---

## 项目结构

```
ops-video/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/           # 20 个模块化路由
│   │   │   │   ├── auth.py       # JWT 认证
│   │   │   │   ├── projects.py   # 项目管理
│   │   │   │   ├── stories.py    # 故事 CRUD
│   │   │   │   ├── chapters.py   # 章节 CRUD
│   │   │   │   ├── tasks.py      # 任务管理
│   │   │   │   ├── workflow.py   # 工作流引擎
│   │   │   │   ├── generators.py # 8 阶段生成器
│   │   │   │   ├── ai_models.py  # AI 模型管理
│   │   │   │   ├── presets.py    # 参数预设
│   │   │   │   ├── knowledge.py  # 知识库管理
│   │   │   │   ├── character_cards.py    # 角色卡
│   │   │   │   ├── storage_providers.py  # 存储配置
│   │   │   │   ├── providers.py  # Provider 路由信息
│   │   │   │   ├── relations.py  # 角色关系
│   │   │   │   ├── analytics.py  # 数据分析
│   │   │   │   ├── files.py / users.py / variants.py
│   │   │   │   └── ...
│   │   │   └── deps.py / deps_auth.py
│   │   ├── models/               # 17 个 SQLAlchemy 模型
│   │   │   ├── project.py / task.py / file.py
│   │   │   ├── story.py / chapter.py
│   │   │   ├── character_card.py / relation.py
│   │   │   ├── ai_model.py / parameter_preset.py
│   │   │   ├── knowledge.py / prompt.py / user.py
│   │   │   ├── storage_provider.py / project_share.py
│   │   │   └── base.py / guid_type.py
│   │   ├── schemas/              # Pydantic Schema
│   │   ├── services/
│   │   │   ├── generator_services/  # 8 阶段生成器
│   │   │   ├── workflow_service.py    # 工作流引擎
│   │   │   ├── character_context.py   # 角色上下文注入
│   │   │   ├── memory_extractor.py    # 自动记忆提取
│   │   │   ├── provider_router.py     # Provider 路由引擎
│   │   │   ├── prompt_service.py      # 提示词模板引擎
│   │   │   ├── knowledge_service.py
│   │   │   ├── traceability_service.py
│   │   │   ├── i2v_composer.py        # 多 clip 拼接
│   │   │   ├── video_analyzer.py
│   │   │   ├── tts_service.py / bgm_service.py / sfx_service.py
│   │   │   ├── graph/                 # SQLite/Neo4j 双后端
│   │   │   └── storyboard_parser.py
│   │   ├── providers/            # AI Provider
│   │   │   ├── llm_provider.py
│   │   │   ├── wanx_provider.py
│   │   │   ├── wan_video_provider.py
│   │   │   ├── siliconflow_provider.py
│   │   │   └── base_provider.py  # 基类 + OSS 自动上传
│   │   ├── core/                 # 配置/日志/Redis/安全
│   │   └── db/                   # 数据库 + 迁移 + 种子数据
│   └── tests/                    # 258 个测试
├── frontend/
│   └── src/
│       ├── app/                  # Next.js App Router
│       │   ├── page.tsx          # 首页（项目总览）
│       │   ├── login/            # 登录页
│       │   ├── models/           # AI 模型管理
│       │   ├── users/            # 用户管理
│       │   ├── storage/          # 存储管理
│       │   └── projects/         # 项目详情 / 章节详情
│       ├── components/           # 30+ React 组件
│       ├── hooks/                # 17 个自定义 Hook
│       ├── lib/                  # API 客户端 + 工具函数
│       └── types/                # TypeScript 类型定义
├── docker/                       # Dockerfile + nginx 配置
├── docs/                         # 文档
├── .github/workflows/deploy.yml  # CI/CD 自动部署
└── docker-compose.prod.yml       # 生产部署
```

---

## 快速部署

```bash
git clone https://github.com/kiddyt00/ops-video.git
cd ops-video

# 启动所有服务
docker compose -f docker-compose.prod.yml up -d --build

# 运行数据库迁移
docker compose -f docker-compose.prod.yml exec -T backend alembic upgrade head

# 访问
# http://localhost:8081
```

首次启动自动：建表 → 种子知识库 → 种子提示词模板。

---

## 已上线功能

- 全自动 8 阶段一键生成（灵感→故事→章节大纲→剧本→分镜→生图→配音→成片）
- 交互式 StoryWizard 6 步故事创作向导
- SSE 流式生成 + 打字机效果
- 多 Provider 路由（Wanx / SiliconFlow / LLM 自动切换）
- AI 模型 Web 后台管理
- 角色卡管理与一致性注入
- 存储供应商配置管理（S3/OSS/COS/MinIO）
- 角色关系图 + 状态追踪（SQLite/Neo4j）
- 用户角色权限管理（JWT）
- 知识库 + 提示词模板系统
- 主题切换（深色/浅色/跟随系统）
- 时区自动检测与显示
- 数据分析仪表盘
- 项目分享与回收站

---

## 快速开发

```bash
# 后端
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
DATABASE_URL=sqlite:///./dev.db alembic upgrade head
uvicorn app.main:app --reload

# 前端
cd frontend
npm install
npm run dev
```

---

## 测试

```bash
# 后端（258 个测试）
cd backend
python -m pytest tests/ -x --timeout=60

# 前端
cd frontend
npm test
```

---

## License

MIT
