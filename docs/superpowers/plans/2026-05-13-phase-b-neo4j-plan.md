# Phase B + Neo4j 实现计划

**目标：** 流式生成（SSE + GenerationPanel 打字机）+ Neo4j 图数据库支持

**两个子项目独立，可并行执行。**

---

## 子项目 A：流式生成 + 生成面板（Phase B）

### A1 — SSE 流式端点（后端）

**文件：** `backend/app/providers/llm_provider.py` / `backend/app/api/routes/workflow.py`

- `llm_provider.py` 新增 `generate_stream()` 方法，用 `httpx.AsyncClient.stream()` 逐 token 推送
- `workflow.py` 新增 `POST /api/v1/workflow/stream/{project_id}/advance/{stage}` 返回 `text/event-stream`
- 事件格式：`event: thinking|instruction|partial|complete|error`，`data: {...}`
- 复用现有 `advance_stage()` 逻辑，但将 LLM 调用替换为流式，实时推送进度

### A2 — GenerationPanel + SSE Hook（前端）

**文件：** `frontend/src/hooks/use-event-stream.ts` / `frontend/src/components/generation-panel.tsx` / `frontend/src/components/workflow-waterfall.tsx`

- `use-event-stream.ts`: 用 `ReadableStream` 解析 SSE，返回 `{events, startStream, isStreaming}`
- `generation-panel.tsx`: 浮动面板，显示 thinking/partial/error 消息流，有暂停/继续/停止按钮
- `workflow-waterfall.tsx`: 点击"开始生成"时弹出面板，完成后面板收

### A3 — 自动记忆提取

**文件：** `backend/app/services/memory_extractor.py`

- 生成成功后自动调用 LLM（qwen-turbo）解析文本，提取角色位置/状态/关系变化
- 自动创建 CharacterState + Relation 记录

---

## 子项目 B：Neo4j GraphProvider

### B1 — 抽象接口 + SQLite 包装

**文件：** `backend/app/services/graph/__init__.py` / `sqlite_provider.py`

- `GraphProvider` ABC：`get_relations()`, `create_relation()`, `get_character_state()`, `save_character_state()`, `get_continuity_context()`
- `SQLiteGraphProvider`：包装现有 `relation_crud` + `character_state_crud`
- `settings.py` 加 `GRAPH_PROVIDER` 配置

### B2 — Neo4j 实现

**文件：** `backend/app/services/graph/neo4j_provider.py` / `docker-compose.prod.yml`

- `Neo4jGraphProvider`：用 `neo4j` async driver，节点类型 `Character/Location/Organization`
- Docker Compose 加 neo4j 注释服务
- `requirements.txt` 加 `neo4j` 依赖

---

## 执行

不需要 TDD 逐步骤。直接用子代理并行推进三个主线：
1. SSE 后端（~15min）
2. 前端面板（~30min）
3. Neo4j（~20min）
4. 自动记忆提取作为收尾（~10min）
