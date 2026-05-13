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
| 🖼️ 生图 | 生成漫画风格图片 | Wanx2.6 (通义万相) |
| 🎵 配音 | TTS 旁白 + BGM + 音效 | edge-tts + 音频合成 |
| 🎬 成片 | 图片序列 + 音频合成视频 | FFmpeg |

### 故事创作增强

- **知识库注入** — 6 个内置知识库（姓名生成/地名库/朝代模板/修仙设定/科幻设定/叙事结构），通过 `@KB{name=...}` 注入提示词
- **StoryWizard 向导** — 6 步故事设定（灵感→类型→世界观→主角→金手指→关系线）
- **Schema 扩展** — 书名建议、目标读者、力量体系、楔子预览等 8 个可选字段
- **提示词模板** — 可编辑的模板系统，支持 `$variable` + 知识库注入

### 情节连贯性保障

- **角色状态追踪** — 每章记录每个角色的生死/位置/势力状态
- **前情提要注入** — 生成新章节时自动组装前情提要，防止角色复活/瞬间移动等矛盾
- **角色关系图** — mentor_of/rival_of/lover_of 等关系存储和查询
- **自动记忆提取** — 剧本/分镜生成后自动解析角色状态变化

### 生成体验

- **SSE 流式生成** — AI 边生成边推送，实时显示内容
- **GenerationPanel** — 浮动面板，打字机效果展示，支持暂停/继续/反馈
- **多结果选择** — 每步骤生成多个变体，用户选择最佳
- **全自动模式** — "全部生成"一键跑完所有阶段

### 系统功能

- **用户系统** — JWT 认证、角色权限（管理员/用户）
- **AI 模型管理** — 数据库驱动，Web 后台配置 LLM/图片模型
- **知识库管理** — 自定义知识库 CRUD
- **Neo4j 图数据库** — 可选，默认 SQLite，切换 `GRAPH_PROVIDER=neo4j`
- **参数预设** — 保存和复用生成参数
- **项目分享与回收站**
- **追溯系统** — 记录所有生成参数、版本、任务历史

---

## 技术栈

### 后端
- FastAPI (Python 3.11)
- PostgreSQL + SQLAlchemy + Alembic
- Neo4j (可选图数据库)
- Redis (缓存/限流)
- SQLite (测试环境)

### 前端
- Next.js 14 (React) + TypeScript
- Tailwind CSS + shadcn/ui
- TanStack Query (数据获取)
- SSE (Server-Sent Events) 流式

### AI/Provider
- DashScope (通义万相 wan2.6 — 图片生成)
- OpenAI 兼容 API (LLM)
- edge-tts (语音合成)
- FFmpeg (视频拼接合成)

### 部署
- Docker + Docker Compose
- 支持 Windows/Linux 部署

---

## 项目结构

```
ops-video/
├── backend/
│   ├── app/
│   │   ├── api/              # API 路由
│   │   │   └── routes/       # 模块化路由
│   │   ├── models/           # SQLAlchemy 模型 (14个)
│   │   ├── schemas/          # Pydantic Schema
│   │   ├── services/         # 业务逻辑
│   │   │   ├── generator_services/  # 各阶段生成器
│   │   │   ├── graph/              # GraphProvider 抽象
│   │   │   ├── workflow_service.py  # 工作流引擎
│   │   │   └── memory_extractor.py  # 自动记忆提取
│   │   ├── providers/        # AI Provider (LLM/Wanx/TTS)
│   │   ├── core/             # 配置/日志/Redis
│   │   └── db/               # 数据库配置+迁移+种子数据
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/              # Next.js App Router
│       ├── components/       # React 组件
│       ├── hooks/            # 自定义 Hook (含 useEventStream)
│       ├── lib/              # API 客户端 + 工具函数
│       └── types/            # TypeScript 类型
├── docker/                   # Dockerfile + nginx 配置
├── docs/                     # 文档
│   ├── user-manual.md        # 用户手册
│   └── superpowers/          # 开发规格/计划
└── docker-compose.prod.yml   # 生产部署
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

首次启动自动：建表 → 种子 6 个知识库 → 种子 2 个提示词模板。

---

## 开发计划

### ✅ Phase A — 故事生成重构 + 知识库系统
知识库系统（6 个种子数据）、提示词模板引擎、角色关系 + 状态追踪（防情节矛盾）、Story Schema 扩展（8 个字段）

### ✅ Phase B — 流式生成体验
SSE 流式端点、GenerationPanel 打字机面板、useEventStream hook、自动记忆提取

### ✅ Neo4j 图数据库
GraphProvider 抽象接口、SQLiteProvider + Neo4jProvider、配置开关

### 🔲 Phase C — 前端体验优化（计划中）
- 统一生成入口（故事 Tab 融合前 3 阶段）
- 线性向导模式 / 引导层
- 更流畅的多章操作

---

## 开发

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

## License

MIT
