# Ops-Video

自动生成漫剧短片的 Web 应用

## 功能特性

- **文生脚本**: 根据主题自动生成剧本
- **文生分镜**: 根据脚本生成分镜描述
- **文生图**: 根据分镜生成漫画风格图片（支持通义万相 / SiliconFlow）
- **多结果选择**: 每步骤生成多个变体，用户可选择最佳结果
- **音频合成**: TTS 语音 + BGM 背景音乐 + SFX 音效
- **视频合成**: FFmpeg 图片序列拼接 + 音频混合
- **追溯系统**: 记录所有生成参数、版本、任务历史
- **数据分析**: 视频元数据分析、项目仪表盘、JSON 报告导出
- **用户系统**: JWT 认证、角色权限、API 限流

## 技术栈

### 后端
- FastAPI (Python)
- PostgreSQL + SQLAlchemy
- Alembic (数据库迁移)
- 通义万相 DashScope (图片生成)

### 前端
- Next.js 14 (React)
- TypeScript
- Tailwind CSS
- Zustand (状态管理)
- TanStack Query (数据获取)

### 部署
- Docker + Docker Compose
- 本地服务器优先，支持云端迁移

## 快速开始

### 前置要求

- Docker & Docker Compose
- Node.js 20+ (本地开发)
- Python 3.11+ (本地开发)
- 通义万相 DashScope (图片生成，可选)

### 使用 Docker Compose 启动

```bash
# 克隆仓库
git clone https://github.com/kiddyt00/ops-video.git
cd ops-video

# 复制环境变量
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

# 启动所有服务
docker-compose up -d

# 访问应用
# 前端：http://localhost:3000
# 后端 API: http://localhost:8000
# API 文档：http://localhost:8000/docs
```

### 本地开发

```bash
# 启动 PostgreSQL
docker-compose up -d db

# 后端
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# 前端
cd frontend
npm install
npm run dev
```

### 数据库迁移

```bash
cd backend

# 升级到最新版本
alembic upgrade head

# 查看当前版本
alembic current

# 降级一个版本
alembic downgrade -1
```

## 项目结构

```
ops-video/
├── backend/              # FastAPI 后端
│   ├── app/
│   │   ├── api/         # API 路由
│   │   ├── models/      # SQLAlchemy 模型
│   │   ├── schemas/     # Pydantic Schema
│   │   ├── services/    # 业务逻辑
│   │   ├── providers/   # AI 服务 Provider
│   │   └── db/          # 数据库配置和迁移
│   └── requirements.txt
├── frontend/            # Next.js 前端
│   ├── src/
│   │   ├── app/        # Next.js App Router
│   │   ├── components/ # React 组件
│   │   ├── lib/        # 工具函数
│   │   ├── stores/     # Zustand 状态
│   │   └── types/      # TypeScript 类型
│   └── package.json
├── docker/              # Docker 配置文件
└── docker-compose.yml
```

## API 端点

- `GET /api/v1/projects` - 获取项目列表
- `POST /api/v1/projects` - 创建新项目
- `GET /api/v1/tasks` - 获取任务列表
- `POST /api/v1/tasks` - 创建新任务
- `POST /api/v1/generators/{type}/generate` - 执行生成

详细 API 文档：http://localhost:8000/docs

## 开发计划

### Phase 1: 基础架构 ✅
项目骨架、数据库模型 (Project/Task/File/VariantGroup)、Docker 配置、基础 API

### Phase 2: 核心功能 ✅
LLM 脚本/分镜生成、图片生成、Generator Services、CRUD API

### Phase 3: 工作流引擎 ✅
阶段推进/回滚、版本对比、谱系追踪、Workflow API

### Phase 4: 前端界面 (MVP) ✅
shadcn/ui 深色模式、三栏布局、项目列表/详情、工作流页面

### Phase 5: 集成测试 ✅
42 个 E2E 测试（全 CRUD + 完整工作流 + 边界条件）

### Phase 6: 音频与视频合成 ✅
TTS (edge-tts)、BGM (numpy/scipy 合成)、SFX、FFmpeg 视频拼接

### Phase 7: 前端集成测试 ✅
vitest + testing-library + E2E 工作流脚本

### Phase 8: 前端 UI 完善 ✅
VariantPicker、WorkflowProgress、深色主题、所有生成 Hooks

### Phase 9: 部署配置优化 ✅
Docker 多阶段构建、生产 compose、健康检查、环境变量模板

### Phase 10: 性能优化 ✅
Redis 缓存、JSON 结构化日志、请求中间件、前端代码分割

### Phase 11: 安全与权限 ✅
JWT 认证、角色权限、Redis 滑动窗口限流、CSP/HSTS/CORS

### Phase 12: 多 Provider 图片生成 ✅
DashScope (通义万相) + SiliconFlow (FLUX.1)，动态路由

### Phase 13: 简化 Provider ✅
移除 ComfyUI，默认使用通义万相，完善 stage_map

### Phase 14: 数据分析与报告 ✅
视频元数据分析、仪表盘、JSON 报告导出、文件类型分布图

### Phase 15: 功能完善与优化 🚧
用户项目管理、项目分享协作、参数预设模板、历史记录与回收站

## License

MIT
