# NovelForge 交互式故事创作 — 设计规格

> 创建时间: 2026-05-12
> 状态: 已确认

## 目标

将故事创作从"单一灵感输入框"升级为"6步交互式向导"，引导用户逐步定义故事框架，AI 根据完整设定生成精准的故事大纲。

## 用户流程

```
进入项目详情 → 默认打开"故事"Tab
  ↓
无故事数据 → 显示 6 步创作向导
  ↓
Step 1: 灵感输入 (文本)
Step 2: 故事类型 + 基调 (Chip 选择)
Step 3: 世界观设定 (时代/体系/自定义)
Step 4: 主角设定 (身份/性格/自定义)
Step 5: 金手指类型 (传承/系统/血脉/重生/无)
Step 6: 关系线 (单女主/后宫/无女主 + 其他关系)
  ↓
汇总确认页 → 展示所有选择 → 可回退修改
  ↓
确认 → POST /api/v1/workflow/{id}/advance/inspiration
  ↓
AI 返回 → 自动填充 Story 所有字段
```

## 后端改动

### 1. `_build_story_prompt()` 扩展

文件: `backend/app/services/generator_services/story_generator_service.py:116-163`

新增参数:
- `golden_finger` — 金手指类型描述
- `protagonist` — 主角设定描述
- `relationship` — 关系线描述
- `worldbuilding_hints` — 世界观提示

所有新参数拼入 prompt 的 "Additional context" 区域。

### 2. `_execute_inspiration_generation()` 透传

文件: `backend/app/services/workflow_service.py:642-663`

从 parameters 中提取新字段，传递给 service.generate_story()。

## 前端改动

### 1. 新组件: StoryWizard

文件: `frontend/src/components/story-wizard.tsx`

6 步向导组件，每步包含:
- Chip 选项（预设）
- 自定义文本输入
- 上一步/下一步导航
- 进度指示器

### 2. StoryEditor 集成

文件: `frontend/src/components/story-editor.tsx`

修改 `!isLoading && !story && !error` 分支:
- 旧: 单一灵感输入框
- 新: 渲染 `<StoryWizard>` 组件

### 3. 类型扩展

文件: `frontend/src/types/story.ts`

新增 `StoryWizardParams` 接口。

## 数据流

```
用户选择 → StoryWizard state
  ↓
汇总确认 → 组装 parameters
  ↓
POST /workflow/{id}/advance/inspiration
  body: {
    parameters: {
      inspiration: "...",
      genre: "...",
      tone: "...",
      target_length: "...",
      golden_finger: "...",
      protagonist: "...",
      relationship: "...",
      worldbuilding_hints: "..."
    }
  }
  ↓
后端 _execute_inspiration_generation → service.generate_story(**params)
  ↓
_build_story_prompt() 拼接所有参数 → LLM 生成 JSON
  ↓
解析 JSON → 填充 Logline/Synopsis/Worldbuilding/Characters/PlotPoints
  ↓
前端 refetch → StoryEditor 展示已填充的字段
```

## 预设选项

### 类型 (genre)
东方玄幻 | 都市异能 | 科幻星际 | 古代言情 | 末世生存 | 游戏异界

### 基调 (tone)
热血激昂 | 轻松搞笑 | 黑暗深沉 | 悬疑惊悚 | 温馨治愈

### 金手指 (golden_finger)
上古传承 | 系统面板 | 血脉觉醒 | 重生记忆 | 契约召唤 | 无金手指

### 关系线 (relationship)
单女主 | 多女主(后宫) | 无女主(纯事业) | BL/GL

### 主角身份 (protagonist.background)
杂役/废柴 | 世家少爷 | 散修 | 现代穿越者 | 重生者

### 力量体系 (worldbuilding_hints.power)
练气修仙 | 魔法斗气 | 异能觉醒 | 科技改造 | 神话血脉

## 测试

- 后端: 验证 `_build_story_prompt()` 在新参数传入时正确拼接
- 前端: 验证 StoryWizard 各步骤渲染正确、导航和状态管理正确
