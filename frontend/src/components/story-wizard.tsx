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
  { key: 'inspiration' as const, title: '灵感', icon: BookOpen, desc: '输入你的故事灵感' },
  { key: 'genre' as const, title: '类型', icon: Globe, desc: '选择故事类型与基调' },
  { key: 'worldbuilding' as const, title: '世界观', icon: Globe, desc: '设定故事的世界规则' },
  { key: 'protagonist' as const, title: '主角', icon: User, desc: '设定主人公的背景' },
  { key: 'golden_finger' as const, title: '金手指', icon: Zap, desc: '主角的特殊能力' },
  { key: 'relationship' as const, title: '关系线', icon: Heart, desc: '设定感情线走向' },
]

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

  const chipBtn = (value: string, current: string, label: string, desc?: string, full = false) => (
    <button key={value} onClick={() => set('genre' in params ? 'genre' : 'golden_finger', value)}
      className={cn(
        full ? 'p-3 rounded-lg border text-left' : 'px-4 py-1.5 rounded-full text-xs border',
        'transition-colors',
        current === value
          ? 'border-violet-500 bg-violet-500/10 text-violet-300'
          : 'border-border hover:border-violet-500/50 text-muted-foreground'
      )}>
      <div className="text-sm font-medium">{label}</div>
      {desc && <div className="text-[10px] text-muted-foreground">{desc}</div>}
    </button>
  )

  const renderStep = () => {
    switch (step) {
      case 0:
        return (
          <div>
            <label className="text-sm font-medium mb-2 block">💡 输入你的故事灵感</label>
            <p className="text-xs text-muted-foreground mb-3">一句话或一段描述都可以，AI 会帮你展开为完整故事大纲</p>
            <Textarea value={params.inspiration} onChange={e => set('inspiration', e.target.value)}
              placeholder="例如：少年林凡在青云城偶得上古星辰剑诀，踏上修仙之路，历经磨难终成剑帝..." rows={4} autoFocus />
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
              placeholder="短篇 / 中篇 / 长篇连载" />
          </div>
        )

      case 2:
        return (
          <div>
            <label className="text-sm font-medium mb-2 block">🌍 世界观设定</label>
            <p className="text-xs text-muted-foreground mb-3">选择力量体系 + 补充自定义设定</p>
            <label className="text-xs text-muted-foreground mb-2 block">力量体系（可多选）</label>
            <div className="grid grid-cols-2 gap-2 mb-4">
              {POWER_SYSTEM_OPTIONS.map(o => (
                <button key={o.value} onClick={() => {
                  const current = params.worldbuilding_hints
                  set('worldbuilding_hints', current.includes(o.value) ? current.replace(o.value, '').replace(';;', ';').trim() : (current ? `${current};${o.value}` : o.value))
                }}
                  className={cn('p-3 rounded-lg border text-left transition-colors',
                    params.worldbuilding_hints?.includes(o.value) ? 'border-violet-500 bg-violet-500/10 text-violet-300' : 'border-border hover:border-violet-500/50')}>
                  <div className="text-sm font-medium">{o.label}</div>
                  <div className="text-[10px] text-muted-foreground">{o.desc}</div>
                </button>
              ))}
            </div>
            <Textarea value={params.worldbuilding_hints} onChange={e => set('worldbuilding_hints', e.target.value)}
              placeholder="补充世界设定：时代背景、势力分布、特殊规则..." rows={3} />
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
              placeholder="补充主角描述：姓名、性格、目标、秘密..." rows={3} />
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
              placeholder="或自定义金手指描述" />
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
              placeholder="或自定义关系描述" />
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
              <div className="p-2 rounded bg-muted/50"><b>类型/基调</b><br/>{params.genre} · {params.tone}</div>
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
        <div className="flex items-center gap-1 mb-6">
          {STEPS.map((_, i) => (
            <div key={i} className="flex items-center gap-1 flex-1">
              <div className={cn('flex-1 h-1.5 rounded-full transition-colors',
                i < step ? 'bg-violet-500' : i === step ? 'bg-violet-500/60' : 'bg-border')} />
            </div>
          ))}
        </div>

        {step < STEPS.length && (
          <div className="flex items-center gap-2 mb-4">
            {(() => { const Icon = STEPS[step].icon; return <Icon className="w-4 h-4 text-violet-400" /> })()}
            <span className="text-sm font-medium text-violet-300">{step + 1}/{STEPS.length} — {STEPS[step].desc}</span>
          </div>
        )}

        {renderStep()}

        {step < STEPS.length && (
          <div className="flex justify-between mt-6 pt-4 border-t border-border">
            <Button variant="ghost" size="sm" onClick={prev} disabled={step === 0}>
              <ChevronLeft className="w-3.5 h-3.5 mr-1" />上一步
            </Button>
            <span className="text-xs text-muted-foreground self-center">{step + 1}/{STEPS.length}</span>
            {step < STEPS.length - 1 ? (
              <Button variant="outline" size="sm" onClick={next}>下一步<ChevronRight className="w-3.5 h-3.5 ml-1" /></Button>
            ) : (
              <Button size="sm" onClick={next}>查看汇总<ChevronRight className="w-3.5 h-3.5 ml-1" /></Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
