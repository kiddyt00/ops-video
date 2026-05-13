# Phase B: 流式生成体验 + Neo4j 图数据库

**日期**: 2026-05-13

## 范围

两个独立子系统，可并行实现：

| 子系统 | 改动面 | 优先级 |
|--------|--------|--------|
| SSE 流式生成 | 后端+前端 | P0 |
| GenerationPanel 打字机 | 前端 | P0 |
| 自动记忆提取 | 后端 | P1 |
| Neo4j GraphProvider | 后端+配置 | P1 |

---

## 一、SSE 流式生成端点

当前模式：`POST .../advance/script` — 阻塞等待 60-120s → 返回结果

改为新增流式端点：

```
POST /api/v1/workflow/stream/{project_id}/advance/{stage}
```

返回 `text/event-stream`，每帧推送：

```
event: thinking
data: {"text": "正在构思剧本大纲..."}

event: instruction
data: {"op": "set", "path": "/title", "value": "第一章"}

event: partial
data: {"field": "synopsis", "text": "少年林凡在青云城...", "progress": 0.3}

event: complete
data: {"task_id": "...", "stage": "script"}

event: error  
data: {"message": "API 调用失败"}
```

### 后端实现

修改 `llm_provider.py`，新增流式方法：

```python
async def generate_stream(self, parameters: dict) -> AsyncIterator[dict]:
    """流式生成，逐 token 推送"""
    async with httpx.AsyncClient(timeout=180.0) as client:
        async with client.stream("POST", url, json=body, headers=headers) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    yield json.loads(line[6:])
```

在 `workflow.py` 路由中新增 SSE 端点，代理 LLM 流到 SSE 事件流。

### 前端实现

```typescript
// useEventStream hook
function useEventStream(projectId: string, stage: TaskStage) {
  const [events, setEvents] = useState<SSEEvent[]>([])
  
  const startStream = async (params?: Record<string, unknown>) => {
    const resp = await fetch(`/api/v1/workflow/stream/${projectId}/advance/${stage}`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ parameters: params, execute: true }),
    })
    const reader = resp.body.getReader()
    // 逐块解析 SSE 事件
  }
  
  return { events, startStream, isStreaming }
}
```

---

## 二、GenerationPanel 组件

参考 NovelForge 的 `GenerationPanel.vue`，在 React 中实现：

- 浮动面板（可拖拽，可最小化）
- 消息流：thinking / action / partial / error / system 类型
- 打字机效果：partial 事件逐字追加到显示区域
- 控制按钮：暂停 / 继续 / 停止 / 重新生成
- 输入框：可在生成过程中发反馈指令
- 进度条：显示当前阶段完成百分比

组件位置：`frontend/src/components/generation-panel.tsx`

与 WorkflowWaterfall 的集成：点击"开始生成"时弹出面板，生成完成后面板收起并刷新数据。

---

## 三、自动记忆提取

在 `workflow_service.py` 中，`advance_stage()` 生成成功后自动调用新服务：

**新文件**: `backend/app/services/memory_extractor.py`

```python
class MemoryExtractor:
    """自动从生成结果中提取角色状态和关系"""
    
    async def extract_from_script(self, project_id: str, script_data: dict):
        """从剧本中解析角色行为、位置变化、状态变更"""
        # 用 LLM 解析剧本文本 → 提取每个角色的状态变化
        # 调用 character_state_crud.create()
```

**提取时机**: 每个阶段生成成功后，如果该阶段包含文本内容（script / storyboard / chapter_outline）

用便宜模型（qwen-turbo）做解析，不要用主生成模型。

---

## 四、Neo4j GraphProvider

### 抽象接口

```python
# app/services/graph/__init__.py
class GraphProvider(ABC):
    async def get_relations(self, project_id: str) -> list[Relation]: ...
    async def create_relation(self, project_id: str, **kwargs) -> Relation: ...
    async def get_character_state(self, project_id: str, character: str) -> CharacterState: ...
    async def save_character_state(self, project_id: str, **kwargs) -> CharacterState: ...
    async def get_continuity_context(self, project_id: str) -> str: ...
```

### 实现

- `SQLiteGraphProvider`: 包装当前 `relation_crud` + `character_state_crud` + `knowledge_service.build_continuity_context`
- `Neo4jGraphProvider`: 用 `neo4j` Python driver，节点类型 `Character`/`Location`/`Organization`，关系类型直接映射现有 relation_type

### 配置

```python
# settings.py
GRAPH_PROVIDER: str = os.getenv("GRAPH_PROVIDER", "sqlite")  # sqlite | neo4j
NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password")
```

### Docker Compose

```yaml
# docker-compose.prod.yml 添加（注释状态，默认不启动）
# neo4j:
#   image: neo4j:5-community
#   environment:
#     NEO4J_AUTH: neo4j/password
#   ports:
#     - "7687:7687"
#   volumes:
#     - neo4j_data:/data
```

### 测试

- `tests/test_graph_provider.py` — 测试抽象接口
- `tests/test_graph_neo4j.py` — 仅当 `GRAPH_PROVIDER=neo4j` 时运行

---

## 五、文件变更清单

### Phase B 文件

| 文件 | 操作 |
|------|------|
| `backend/app/providers/llm_provider.py` | 修改 — 新增 `generate_stream()` |
| `backend/app/api/routes/workflow.py` | 修改 — 新增 SSE 流式端点 |
| `backend/app/services/memory_extractor.py` | 新建 |
| `frontend/src/hooks/use-event-stream.ts` | 新建 |
| `frontend/src/components/generation-panel.tsx` | 新建 |
| `frontend/src/components/story-editor.tsx` | 修改 — 接入流式 |
| `frontend/src/components/workflow-waterfall.tsx` | 修改 — 集成面板 |
| `backend/tests/test_memory_extractor.py` | 新建 |
| `backend/tests/test_sse_endpoint.py` | 新建 |

### Neo4j 文件

| 文件 | 操作 |
|------|------|
| `backend/app/services/graph/__init__.py` | 新建 — 抽象接口 |
| `backend/app/services/graph/sqlite_provider.py` | 新建 — SQLite 实现 |
| `backend/app/services/graph/neo4j_provider.py` | 新建 — Neo4j 实现 |
| `backend/app/core/config.py` | 修改 — 新增 GRAPH_* 配置 |
| `docker-compose.prod.yml` | 修改 — Neo4j 注释服务 |
| `requirements.txt` | 修改 — 添加 neo4j driver |
| `backend/tests/test_graph_provider.py` | 新建 |
