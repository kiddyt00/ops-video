# Ops-Video 项目开发指南

## 工作流
- 使用 Superpowers 工作流：brainstorming -> writing-plans -> execute -> verify
- TDD：先写测试，再写实现
- 每个子任务完成后 commit + push
- 完成后运行全量测试验证

## 技术栈
- 后端：FastAPI + SQLAlchemy + PostgreSQL (测试用 SQLite)
- 前端：Next.js + React + shadcn/ui + Tailwind CSS
- 测试：后端 pytest，前端 vitest

## 项目结构
- backend/app/models/ - SQLAlchemy 模型
- backend/app/api/routes/ - API 路由
- backend/app/services/ - 业务逻辑
- backend/tests/ - 测试
- frontend/src/ - 前端代码
