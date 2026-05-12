# NovelForge 交互式故事创作 — 实现计划

> **面向 AI 代理的工作者：** 使用 TDD，每任务完成后 commit。
> 步骤使用复选框（`- [ ]`）跟踪进度。

**目标：** 将故事创作从单一灵感输入框升级为 6 步交互式向导

**架构：** 后端扩展 `_build_story_prompt()` 接收 golden_finger/protagonist/relationship/worldbuilding_hints 参数，前端新建 `StoryWizard` 组件完成 6 步交互流程

**技术栈：** Python/FastAPI + TypeScript/React/shadcn-ui

---

## 文件清单

| 文件 | 操作 | 职责 |
|------|------|------|
| `backend/app/services/generator_services/story_generator_service.py` | 修改 | 扩展 `_build_story_prompt()` |
| `backend/app/services/workflow_service.py` | 修改 | 透传新参数 |
| `frontend/src/components/story-wizard.tsx` | 创建 | 6 步向导组件 |
| `frontend/src/components/story-editor.tsx` | 修改 | 集成 StoryWizard |
| `frontend/src/types/story.ts` | 修改 | 新增 StoryWizardParams 类型 |

---

### 任务 1：后端 — 扩展 story prompt builder

**文件：**
- 修改：`backend/app/services/generator_services/story_generator_service.py:116-163`

- [ ] **步骤 1：扩展 `_build_story_prompt()` 函数**

在函数签名和 prompt 拼接中新增 4 个参数：

```python
def _build_story_prompt(inspiration: str, **kwargs) -> str:
    """Build the prompt for expanding an inspiration into a full story outline."""
    genre = kwargs.get("genre", "")
    tone = kwargs.get("tone", "")
    target_length = kwargs.get("target_length", "")
    golden_finger = kwargs.get("golden_finger", "")
    protagonist = kwargs.get("protagonist", "")
    relationship = kwargs.get("relationship", "")
    worldbuilding_hints = kwargs.get("worldbuilding_hints", "")
    extra = kwargs.get("extra_context", "")

    prompt = f"""You are a professional story developer. Expand the following inspiration into a complete story outline.

Inspiration: {inspiration}
"""
    if genre:
        prompt += f"Genre: {genre}\n"
    if tone:
        prompt += f"Tone: {tone}\n"
    if target_length:
        prompt += f"Target length: {target_length}\n"
    if golden_finger:
        prompt += f"Protagonist's special ability / golden finger: {golden_finger}\n"
    if protagonist:
        prompt += f"Protagonist profile: {protagonist}\n"
    if relationship:
        prompt += f"Character relationships: {relationship}\n"
    if worldbuilding_hints:
        prompt += f"Worldbuilding hints: {worldbuilding_hints}\n"
    if extra:
        prompt += f"Additional context: {extra}\n"

    prompt += """
Return a JSON object with the following structure:
{
  "logline": "A one-sentence summary of the story",
  "synopsis": "A detailed paragraph summarising the full story arc",
  "worldbuilding": {
    "setting": "Where the story takes place",
    "time_period": "When the story takes place",
    "rules": "Key world rules, magic systems, technology, etc."
  },
  "characters": [
    {
      "name": "Character name",
      "role": "Protagonist / Antagonist / Supporting / etc.",
      "description": "Brief character description",
      "arc": "Character arc summary"
    }
  ],
  "themes": ["Theme 1", "Theme 2", ...],
  "plot_points": [
    {"act": "Act 1", "description": "Inciting incident / setup"},
    {"act": "Act 2", "description": "Rising action / confrontation"},
    {"act": "Act 3", "description": "Climax / resolution"}
  ]
}

Return ONLY valid JSON. No markdown, no explanation."""
    return prompt
```

- [ ] **步骤 2：验证 import 无变化，运行已有测试**

```bash
cd backend && source venv/bin/activate && python -c "from app.services.generator_services.story_generator_service import _build_story_prompt; p=_build_story_prompt('test', golden_finger='上古传承', protagonist='杂役少年', relationship='单女主', worldbuilding_hints='修仙世界'); assert '上古传承' in p; assert '杂役少年' in p; assert '单女主' in p; print('OK')"
```

- [ ] **步骤 3：Commit**

```bash
git add backend/app/services/generator_services/story_generator_service.py
git commit -m "feat: _build_story_prompt 扩展 golden_finger/protagonist/relationship/worldbuilding_hints 参数"
```

---

### 任务 2：后端 — workflow 透传新参数

**文件：**
- 修改：`backend/app/services/workflow_service.py:642-663`

- [ ] **步骤 1：扩展 `_execute_inspiration_generation` 参数提取**

在 `genre`/`tone`/`target_length`/`extra_context` 之后新增提取：

```python
        golden_finger = parameters.get("golden_finger", "")
        protagonist = parameters.get("protagonist", "")
        relationship = parameters.get("relationship", "")
        worldbuilding_hints = parameters.get("worldbuilding_hints", "")

        service = StoryGeneratorService()
        story_data = await service.generate_story(
            inspiration=inspiration,
            project_id=str(task.project_id),
            genre=genre,
            tone=tone,
            target_length=target_length,
            golden_finger=golden_finger,
            protagonist=protagonist,
            relationship=relationship,
            worldbuilding_hints=worldbuilding_hints,
            extra_context=extra_context,
        )
```

- [ ] **步骤 2：快速验证**

```bash
cd backend && source venv/bin/activate && python -c "
import asyncio, sys
sys.path.insert(0, '.')
from app.services.workflow_service import WorkflowService
# Just verify import chain works with new params
print('Import OK')
"
```

- [ ] **步骤 3：Commit**

```bash
git add backend/app/services/workflow_service.py
git commit -m "feat: workflow 透传 golden_finger/protagonist/relationship/worldbuilding_hints 到 story generator"
```

---

### 任务 3：前端 — StoryWizardParams 类型定义

**文件：**
- 修改：`frontend/src/types/story.ts`

- [ ] **步骤 1：添加 StoryWizardParams 接口**

在 `story.ts` 末尾追加：

```typescript
export interface StoryWizardParams {
  inspiration: string
  genre: string
  tone: string
  target_length: string
  golden_finger: string
  protagonist: string
  relationship: string
  worldbuilding_hints: string
}

export const GENRE_OPTIONS = [
  { value: '东方玄幻', label: '东方玄幻', desc: '修仙 / 炼气 / 宗门 / 天道' },
  { value: '都市异能', label: '都市异能', desc: '现代背景 / 超能力 / 隐藏身份' },
  { value: '科幻星际', label: '科幻星际', desc: '机甲 / AI / 星际殖民' },
  { value: '古代言情', label: '古代言情', desc: '宫斗 / 江湖 / 权谋' },
  { value: '末世生存', label: '末世生存', desc: '丧尸 / 废土 / 异能觉醒' },
  { value: '游戏异界', label: '游戏异界', desc: '穿越游戏 / 系统流 / 等级打怪' },
]

export const TONE_OPTIONS = [
  { value: '热血激昂', label: '热血' },
  { value: '轻松搞笑', label: '轻松' },
  { value: '黑暗深沉', label: '黑暗' },
  { value: '悬疑惊悚', label: '悬疑' },
  { value: '温馨治愈', label: '治愈' },
]

export const GOLDEN_FINGER_OPTIONS = [
  { value: '上古传承', label: '上古传承', desc: '远古大能的功法或神器' },
  { value: '系统面板', label: '系统面板', desc: '游戏化数据面板辅助成长' },
  { value: '血脉觉醒', label: '血脉觉醒', desc: '隐藏血统逐步觉醒力量' },
  { value: '重生记忆', label: '重生记忆', desc: '带着前世记忆重新开始' },
  { value: '契约召唤', label: '契约召唤', desc: '召唤异界生物协助' },
  { value: '无金手指', label: '无金手指', desc: '纯靠智慧和努力' },
]

export const RELATIONSHIP_OPTIONS = [
  { value: '单女主', label: '单女主', desc: '专注一条感情线' },
  { value: '多女主', label: '多女主(后宫)', desc: '多条感情线并行' },
  { value: '无女主', label: '无女主(纯事业)', desc: '不涉及感情线' },
]

export const PROTAGONIST_OPTIONS = [
  { value: '杂役废柴逆袭', label: '杂役/废柴', desc: '出身低微，逆天改命' },
  { value: '世家天才陨落', label: '落难天才', desc: '曾经辉煌，跌落谷底' },
  { value: '平凡现代穿越', label: '穿越者', desc: '现代人穿越到异世界' },
  { value: '重生复仇', label: '重生者', desc: '带着记忆重新来过' },
  { value: '天命之子', label: '天命之子', desc: '生而不凡，注定成神' },
]

export const POWER_SYSTEM_OPTIONS = [
  { value: '练气修仙', label: '修仙体系', desc: '练气→筑基→金丹→元婴' },
  { value: '魔法斗气', label: '魔法斗气', desc: '魔法师/战士等级体系' },
  { value: '异能觉醒', label: '异能觉醒', desc: '现代超能力体系' },
  { value: '神话血脉', label: '神话血脉', desc: '神族/妖族血脉传承' },
]
```

- [ ] **步骤 2：验证 TypeScript 编译**

```bash
cd frontend && npx tsc --noEmit 2>&1 | head -5
```

- [ ] **步骤 3：Commit**

```bash
git add frontend/src/types/story.ts
git commit -m "feat: 添加 StoryWizardParams 类型和预设选项"
```

---

### 任务 4：前端 — StoryWizard 6步向导组件

**文件：**
- 创建：`frontend/src/components/story-wizard.tsx`

- [ ] **步骤 1：创建 StoryWizard 组件**

```tsx
'use client'

import { useState } from 'react'
import { ChevronLeft, ChevronRight, Sparkles, BookOpen, Globe, User, Zap, Heart, Check } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import {
  StoryWizardParams,
  GENRE_OPTIONS, TONE_OPTIONS, GOLDEN_FINGER_OPTIONS,
  RELATIONSHIP_OPTIONS, PROTAGONIST_OPTIONS, POWER_SYSTEM_OPTIONS,
} from '@/types/story'

const STEPS = [
  { key: 'inspiration', title: '灵感', icon: BookOpen, desc: '输入你的故事灵感' },
  { key: 'genre', title: '类型', icon: Globe, desc: '选择故事类型与基调' },
  { key: 'worldbuilding', title: '世界观', icon: Globe, desc: '设定故事的世界规则' },
  { key: 'protagonist', title: '主角', icon: User, desc: '设定主人公的背景' },
  { key: 'golden_finger', title: '金手指', icon: Zap, desc: '主角的特殊能力' },
  { key: 'relationship', title: '关系线', icon: Heart, desc: '设定感情线走向' },
] as const

interface Props {
  onComplete: (params: StoryWizardParams) => void
  isGenerating?: boolean
}

export function StoryWizard({ onComplete, isGenerating }: Props) {
  const [step, setStep] = useState(0)
  const [params, setParams] = useState<StoryWizardParams>({
    inspiration: '', genre: '', tone: '热血激昂',
    target_length: '长篇连载', golden_finger: '', protagonist: '',
    relationship: '', worldbuilding_hints: '',
  })

  const set = (key: keyof StoryWizardParams, value: string) =>
    setParams(p => ({ ...p, [key]: value }))

  const next = () => setStep(s => Math.min(s + 1, STEPS.length))
  const prev = () => setStep(s => Math.max(s - 1, 0))

  const renderStep = () => {
    switch (step) {
      case 0:
        return (
          <div>
            <label className="text-sm font-medium mb-2 block">💡 输入你的故事灵感</label>
            <p className="text-xs text-muted-foreground mb-3">一句话或一段描述都可以，AI 会帮你展开</p>
            <Textarea
              value={params.inspiration}
              onChange={e => set('inspiration', e.target.value)}
              placeholder="例如：少年林凡在青云城偶得上古星辰剑诀，踏上修仙之路，历经磨难终成剑帝..."
              rows={4}
              className="text-sm"
              autoFocus
            />
          </div>
        )

      case 1:
        return (
          <div>
            <label className="text-sm font-medium mb-2 block">📌 故事类型</label>
            <div className="grid grid-cols-2 gap-2 mb-4">
              {GENRE_OPTIONS.map(o => (
                <button key={o.value} onClick={() => set('genre', o.value)}
                  className={cn('p-3 rounded-lg border text-left transition-colors',
                    params.genre === o.value ? 'border-violet-500 bg-violet-500/10 text-violet-300' : 'border-border hover:border-violet-500/50')}>
                  <div className="text-sm font-medium">{o.label}</div>
                  <div className="text-[10px] text-muted-foreground">{o.desc}</div>
                </button>
              ))}
            </div>
            <label className="text-sm font-medium mb-2 block">🎭 故事基调</label>
            <div className="flex flex-wrap gap-2 mb-3">
              {TONE_OPTIONS.map(o => (
                <button key={o.value} onClick={() => set('tone', o.value)}
                  className={cn('px-4 py-1.5 rounded-full text-xs border transition-colors',
                    params.tone === o.value ? 'border-violet-500 bg-violet-500/10 text-violet-300' : 'border-border hover:border-violet-500/50')}>
                  {o.label}
                </button>
              ))}
            </div>
            <label className="text-sm font-medium mb-2 block">📏 篇幅</label>
            <Input value={params.target_length} onChange={e => set('target_length', e.target.value)}
              placeholder="短篇 / 中篇 / 长篇连载" className="text-sm" />
          </div>
        )

      case 2:
        return (
          <div>
            <label className="text-sm font-medium mb-2 block">🌍 世界观设定</label>
            <p className="text-xs text-muted-foreground mb-3">选择力量体系 + 补充自定义设定</p>
            <label className="text-xs text-muted-foreground mb-2 block">力量体系</label>
            <div className="grid grid-cols-2 gap-2 mb-4">
              {POWER_SYSTEM_OPTIONS.map(o => (
                <button key={o.value} onClick={() => set('worldbuilding_hints', p => p ? `${p}; ${o.value}` : o.value)}
                  className={cn('p-3 rounded-lg border text-left transition-colors',
                    params.worldbuilding_hints?.includes(o.value) ? 'border-violet-500 bg-violet-500/10 text-violet-300' : 'border-border hover:border-violet-500/50')}>
                  <div className="text-sm font-medium">{o.label}</div>
                  <div className="text-[10px] text-muted-foreground">{o.desc}</div>
                </button>
              ))}
            </div>
            <Textarea value={params.worldbuilding_hints} onChange={e => set('worldbuilding_hints', e.target.value)}
              placeholder="补充世界设定：时代背景、势力分布、特殊规则..." rows={3} className="text-sm" />
          </div>
        )

      case 3:
        return (
          <div>
            <label className="text-sm font-medium mb-2 block">👤 主角设定</label>
            <p className="text-xs text-muted-foreground mb-3">选择主角身份模板 + 补充描述</p>
            <div className="grid grid-cols-2 gap-2 mb-4">
              {PROTAGONIST_OPTIONS.map(o => (
                <button key={o.value} onClick={() => set('protagonist', o.value)}
                  className={cn('p-3 rounded-lg border text-left transition-colors',
                    params.protagonist === o.value ? 'border-violet-500 bg-violet-500/10 text-violet-300' : 'border-border hover:border-violet-500/50')}>
                  <div className="text-sm font-medium">{o.label}</div>
                  <div className="text-[10px] text-muted-foreground">{o.desc}</div>
                </button>
              ))}
            </div>
            <Textarea value={params.protagonist} onChange={e => set('protagonist', e.target.value)}
              placeholder="补充主角描述：姓名、性格、目标、秘密..." rows={3} className="text-sm" />
          </div>
        )

      case 4:
        return (
          <div>
            <label className="text-sm font-medium mb-2 block">⚡ 金手指 / 外挂</label>
            <p className="text-xs text-muted-foreground mb-3">主角的独特优势是什么？</p>
            <div className="grid grid-cols-2 gap-2 mb-4">
              {GOLDEN_FINGER_OPTIONS.map(o => (
                <button key={o.value} onClick={() => set('golden_finger', o.value)}
                  className={cn('p-3 rounded-lg border text-left transition-colors',
                    params.golden_finger === o.value ? 'border-violet-500 bg-violet-500/10 text-violet-300' : 'border-border hover:border-violet-500/50')}>
                  <div className="text-sm font-medium">{o.label}</div>
                  <div className="text-[10px] text-muted-foreground">{o.desc}</div>
                </button>
              ))}
            </div>
            <Input value={params.golden_finger} onChange={e => set('golden_finger', e.target.value)}
              placeholder="或自定义金手指描述" className="text-sm" />
          </div>
        )

      case 5:
        return (
          <div>
            <label className="text-sm font-medium mb-2 block">💕 关系线</label>
            <p className="text-xs text-muted-foreground mb-3">主角的感情线和其他重要关系</p>
            <div className="grid grid-cols-2 gap-2 mb-4">
              {RELATIONSHIP_OPTIONS.map(o => (
                <button key={o.value} onClick={() => set('relationship', o.value)}
                  className={cn('p-3 rounded-lg border text-left transition-colors',
                    params.relationship === o.value ? 'border-violet-500 bg-violet-500/10 text-violet-300' : 'border-border hover:border-violet-500/50')}>
                  <div className="text-sm font-medium">{o.label}</div>
                  <div className="text-[10px] text-muted-foreground">{o.desc}</div>
                </button>
              ))}
            </div>
            <Input value={params.relationship} onChange={e => set('relationship', e.target.value)}
              placeholder="或自定义关系描述" className="text-sm" />
          </div>
        )

      default:
        return (
          <div className="text-center py-8">
            <Check className="w-12 h-12 text-emerald-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">设定完成！</h3>
            <p className="text-sm text-muted-foreground mb-6">AI 将根据以下设定生成完整故事大纲</p>
            <div className="grid grid-cols-2 gap-2 text-left text-xs mb-6">
              <div className="p-2 rounded bg-muted/50"><b>灵感</b><br/>{params.inspiration}</div>
              <div className="p-2 rounded bg-muted/50"><b>类型</b><br/>{params.genre} · {params.tone}</div>
              <div className="p-2 rounded bg-muted/50"><b>世界观</b><br/>{params.worldbuilding_hints || '未设定'}</div>
              <div className="p-2 rounded bg-muted/50"><b>主角</b><br/>{params.protagonist || '未设定'}</div>
              <div className="p-2 rounded bg-muted/50"><b>金手指</b><br/>{params.golden_finger || '未设定'}</div>
              <div className="p-2 rounded bg-muted/50"><b>关系线</b><br/>{params.relationship || '未设定'}</div>
            </div>
            <Button onClick={() => onComplete(params)} disabled={isGenerating} size="lg" className="gap-2">
              <Sparkles className="w-4 h-4" />
              {isGenerating ? '生成中...' : '确认设定，AI 生成故事'}
            </Button>
          </div>
        )
    }
  }

  return (
    <Card className="border-dashed border-violet-500/30">
      <CardContent className="pt-6">
        {/* Step indicators */}
        <div className="flex items-center gap-1 mb-6">
          {STEPS.map((s, i) => (
            <div key={s.key} className="flex items-center gap-1 flex-1">
              <div className={cn(
                'flex-1 h-1.5 rounded-full transition-colors',
                i < step ? 'bg-violet-500' : i === step ? 'bg-violet-500/60' : 'bg-border'
              )} />
            </div>
          ))}
        </div>

        {/* Step title */}
        {step < STEPS.length && (
          <div className="flex items-center gap-2 mb-4">
            <STEPS[step].icon className="w-4 h-4 text-violet-400" />
            <span className="text-sm font-medium text-violet-300">
              {step + 1}/{STEPS.length} — {STEPS[step].desc}
            </span>
          </div>
        )}

        {/* Step content */}
        {renderStep()}

        {/* Navigation */}
        {step < STEPS.length && (
          <div className="flex justify-between mt-6 pt-4 border-t border-border">
            <Button variant="ghost" size="sm" onClick={prev} disabled={step === 0}>
              <ChevronLeft className="w-3.5 h-3.5 mr-1" />上一步
            </Button>
            <span className="text-xs text-muted-foreground self-center">{step + 1}/{STEPS.length}</span>
            {step < STEPS.length - 1 ? (
              <Button variant="outline" size="sm" onClick={next}>
                下一步<ChevronRight className="w-3.5 h-3.5 ml-1" />
              </Button>
            ) : (
              <Button size="sm" onClick={next}>
                查看汇总<ChevronRight className="w-3.5 h-3.5 ml-1" />
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
```

- [ ] **步骤 2：验证 TypeScript 编译**

```bash
cd frontend && npx tsc --noEmit 2>&1 | head -5
```

- [ ] **步骤 3：Commit**

```bash
git add frontend/src/components/story-wizard.tsx
git commit -m "feat: StoryWizard 6步交互式故事创作向导"
```

---

### 任务 5：前端 — StoryEditor 集成 StoryWizard

**文件：**
- 修改：`frontend/src/components/story-editor.tsx:433-477`

- [ ] **步骤 1：替换无故事状态的内容**

将 `{!isLoading && !story && !error && (` 分支中的旧 Card 替换为 StoryWizard：

```tsx
          {/* No story yet — Show interactive wizard */}
          {!isLoading && !story && !error && (
            <StoryWizard
              onComplete={async (wizardParams) => {
                setApiError(null)
                // Build parameters matching backend expectations
                const apiParams: Record<string, string> = {
                  inspiration: wizardParams.inspiration,
                  genre: wizardParams.genre,
                  tone: wizardParams.tone,
                  target_length: wizardParams.target_length,
                }
                if (wizardParams.golden_finger) apiParams.golden_finger = wizardParams.golden_finger
                if (wizardParams.protagonist) apiParams.protagonist = wizardParams.protagonist
                if (wizardParams.relationship) apiParams.relationship = wizardParams.relationship
                if (wizardParams.worldbuilding_hints) apiParams.worldbuilding_hints = wizardParams.worldbuilding_hints

                try {
                  const token = localStorage.getItem('ops-video-tokens')
                  const accessToken = token ? JSON.parse(token).access_token : null
                  const resp = await fetch(
                    `${process.env.NEXT_PUBLIC_API_URL || '/api/v1'}/workflow/${projectId}/advance/inspiration`,
                    {
                      method: 'POST',
                      headers: {
                        'Content-Type': 'application/json',
                        ...(accessToken ? { 'Authorization': `Bearer ${accessToken}` } : {}),
                      },
                      body: JSON.stringify({ parameters: apiParams, execute: true }),
                    }
                  )
                  if (!resp.ok) {
                    const data = await resp.json()
                    throw new Error(data.detail || '生成故事失败')
                  }
                  await refetch()
                } catch (e) {
                  setApiError(e instanceof Error ? e.message : '生成故事失败')
                }
              }}
              isGenerating={inspirationMutation.isPending || generateStoryMutation.isPending}
            />
          )}
```

并在文件顶部添加 import：
```tsx
import { StoryWizard } from './story-wizard'
```

- [ ] **步骤 2：验证 TypeScript 编译**

```bash
cd frontend && npx tsc --noEmit 2>&1 | head -10
```

- [ ] **步骤 3：Commit**

```bash
git add frontend/src/components/story-editor.tsx
git commit -m "feat: StoryEditor 集成 StoryWizard 替代单一灵感输入框"
```

---

### 任务 6：部署验证

- [ ] **步骤 1：本地构建验证**

```bash
cd frontend && npm run build 2>&1 | tail -10
```

- [ ] **步骤 2：提交并推送**

```bash
cd ~/claude-projects/ops-video && git push
```

- [ ] **步骤 3：部署到服务器**

```bash
ssh ubuntu@49.235.108.61 "cd /opt/ops-video && git pull origin novelforge && sudo docker compose -f docker-compose.prod.yml up -d --build"
```

- [ ] **步骤 4：端到端验证**

创建新项目 → 进入故事Tab → 走完6步向导 → 确认生成 → 验证故事字段已填充
