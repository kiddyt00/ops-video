'use client'

import { useState } from 'react'
import {
  Brain, Paintbrush, Mic, Music, Clapperboard,
  Sparkles, ChevronDown, ChevronRight, CheckCircle2,
  FlaskConical, AlertCircle, Cpu, Zap, Layers, Wand2
} from 'lucide-react'
import { AppShell } from '@/components/app-shell'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { cn } from '@/lib/utils'

// ─── Types ────────────────────────────────────────────────────────────

interface GeneratorInfo {
  name: string
  type: string
  description: string
  parameters: Record<string, { type: string; required: boolean; default?: string | number | boolean; description: string }>
}

interface ModelCategory {
  id: string
  label: string
  description: string
  icon: typeof Brain
  color: string
  bgColor: string
  borderColor: string
  textColor: string
  badgeColor: string
  generators: GeneratorInfo[]
}

// ─── Model providers info (static, editable) ──────────────────────────

interface ProviderInfo {
  name: string
  models: { name: string; description: string; recommended?: boolean }[]
  status: 'active' | 'mock' | 'unavailable'
}

const PROVIDERS: Record<string, ProviderInfo> = {
  llm: {
    name: 'DashScope 通义千问',
    models: [
      { name: 'qwen-plus', description: '均衡性能，适合剧本/分镜生成', recommended: true },
      { name: 'qwen-max', description: '最强能力，适合复杂剧情', recommended: false },
      { name: 'qwen-turbo', description: '高速响应，适合快速迭代', recommended: false },
    ],
    status: 'mock',
  },
  wanx: {
    name: '通义万相 Wanx',
    models: [
      { name: 'wan2.6-t2i', description: '文生图旗舰模型', recommended: true },
      { name: 'wanx-v1', description: '稳定版本，兼容性好', recommended: false },
    ],
    status: 'mock',
  },
  tts: {
    name: 'Edge TTS',
    models: [
      { name: 'zh-CN-XiaoxiaoNeural', description: '女声·温柔', recommended: true },
      { name: 'zh-CN-YunxiNeural', description: '男声·沉稳', recommended: false },
      { name: 'zh-CN-XiaoyiNeural', description: '女声·活泼', recommended: false },
    ],
    status: 'active',
  },
  bgm: {
    name: 'SciPy 合成引擎',
    models: [
      { name: 'ambient', description: '氛围音乐' },
      { name: 'dramatic', description: '戏剧化配乐' },
      { name: 'cheerful', description: '轻快欢快' },
    ],
    status: 'active',
  },
  video: {
    name: 'FFmpeg 引擎',
    models: [
      { name: 'H.264/AAC', description: '标准 MP4 输出' },
    ],
    status: 'active',
  },
}

// ─── API ──────────────────────────────────────────────────────────────

async function fetchGenerators(): Promise<GeneratorInfo[]> {
  const { data } = await api.get<GeneratorInfo[]>('/generators')
  return data
}

// ─── Category Config ──────────────────────────────────────────────────

const CATEGORY_CONFIG: Record<string, Omit<ModelCategory, 'generators'>> = {
  llm: {
    id: 'llm', label: '大语言模型', description: '剧本创作与分镜拆解',
    icon: Brain, color: '#6366f1', bgColor: 'bg-violet-500/5', borderColor: 'border-violet-500/20',
    textColor: 'text-violet-400', badgeColor: 'bg-violet-500/10 text-violet-400 border-violet-500/20',
  },
  wanx: {
    id: 'wanx', label: '文生图', description: '根据分镜描述生成漫画图片',
    icon: Paintbrush, color: '#f59e0b', bgColor: 'bg-amber-500/5', borderColor: 'border-amber-500/20',
    textColor: 'text-amber-400', badgeColor: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  },
  tts: {
    id: 'tts', label: '文生音频', description: '将文字转为自然语音旁白',
    icon: Mic, color: '#10b981', bgColor: 'bg-emerald-500/5', borderColor: 'border-emerald-500/20',
    textColor: 'text-emerald-400', badgeColor: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  },
  bgm: {
    id: 'bgm', label: '音乐生成', description: '自动生成背景音乐与音效',
    icon: Music, color: '#ec4899', bgColor: 'bg-pink-500/5', borderColor: 'border-pink-500/20',
    textColor: 'text-pink-400', badgeColor: 'bg-pink-500/10 text-pink-400 border-pink-500/20',
  },
  video: {
    id: 'video', label: '视频合成', description: '图片+音频+时间轴 → 最终视频',
    icon: Clapperboard, color: '#06b6d4', bgColor: 'bg-cyan-500/5', borderColor: 'border-cyan-500/20',
    textColor: 'text-cyan-400', badgeColor: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
  },
}

const STATUS_MAP: Record<string, { label: string; className: string }> = {
  active: { label: '已接入', className: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30' },
  mock: { label: 'Mock', className: 'bg-amber-500/15 text-amber-400 border-amber-500/30' },
  unavailable: { label: '未配置', className: 'bg-red-500/15 text-red-400 border-red-500/30' },
}

// ─── Main Page ────────────────────────────────────────────────────────

export default function ModelsPage() {
  const { data: generators, isLoading, error } = useQuery({
    queryKey: ['generators'],
    queryFn: fetchGenerators,
  })

  const [expandedCategory, setExpandedCategory] = useState<string | null>(null)
  const [expandedProvider, setExpandedProvider] = useState<string | null>(null)

  // Group generators by type
  const categories = generators
    ? Object.entries(CATEGORY_CONFIG).map(([type, config]) => ({
        ...config,
        generators: generators.filter(g => g.type === type),
      })).filter(c => c.generators.length > 0)
    : []

  return (
    <AppShell>
      <ScrollArea className="h-full">
        <div className="p-6 max-w-5xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-xl bg-primary/10 ring-1 ring-primary/20 flex items-center justify-center">
                <Cpu className="w-5 h-5 text-primary" />
              </div>
              <div>
                <h2 className="text-2xl font-bold">模型中心</h2>
                <p className="text-sm text-muted-foreground">管理 AI 模型接入与配置</p>
              </div>
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="flex items-start gap-2 text-sm text-red-400 bg-red-500/10 rounded-xl p-3.5 mb-6">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>加载模型信息失败</span>
            </div>
          )}

          {/* Loading */}
          {isLoading ? (
            <div className="grid gap-4 md:grid-cols-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <Card key={i}><CardHeader><Skeleton className="h-5 w-32" /><Skeleton className="h-4 w-48 mt-2" /></CardHeader></Card>
              ))}
            </div>
          ) : (
            <div className="space-y-10">
              {/* ─── Category Groups ──────────────────────────────── */}
              {categories.map(category => (
                <section key={category.id}>
                  {/* Category Header */}
                  <div className={cn(
                    'flex items-center gap-4 mb-4 p-4 rounded-2xl border cursor-pointer transition-all duration-200',
                    category.bgColor, category.borderColor,
                    expandedCategory === category.id && 'ring-1'
                  )}
                  onClick={() => setExpandedCategory(expandedCategory === category.id ? null : category.id)}
                  >
                    <div
                      className="w-12 h-12 rounded-xl flex items-center justify-center shrink-0"
                      style={{ backgroundColor: category.color + '15' }}
                    >
                      <category.icon className="w-6 h-6" style={{ color: category.color }} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="text-lg font-semibold flex items-center gap-2">
                        {category.label}
                        <Badge className={cn('text-[10px]', category.badgeColor)}>
                          {category.generators.length} 个模型
                        </Badge>
                      </h3>
                      <p className="text-sm text-muted-foreground">{category.description}</p>
                    </div>
                    {expandedCategory === category.id ? (
                      <ChevronDown className="w-5 h-5 text-muted-foreground shrink-0" />
                    ) : (
                      <ChevronRight className="w-5 h-5 text-muted-foreground shrink-0" />
                    )}
                  </div>

                  {/* Expanded Details */}
                  {expandedCategory === category.id && (
                    <div className="space-y-4 pl-4 ml-6 border-l-2" style={{ borderColor: category.color + '20' }}>
                      {/* Provider Info */}
                      {PROVIDERS[category.id] && (() => {
                        const provider = PROVIDERS[category.id]
                        const status = STATUS_MAP[provider.status]
                        return (
                          <div>
                            <div
                              className="flex items-center gap-3 p-3 rounded-xl hover:bg-muted/30 cursor-pointer transition-colors"
                              onClick={() => setExpandedProvider(expandedProvider === category.id ? null : category.id)}
                            >
                              <Layers className="w-4 h-4 text-muted-foreground shrink-0" />
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2">
                                  <span className="text-sm font-medium">{provider.name}</span>
                                  <Badge className={cn('text-[10px]', status.className)}>{status.label}</Badge>
                                </div>
                                <p className="text-xs text-muted-foreground mt-0.5">
                                  {provider.status === 'mock' ? '需要配置 API Key 才能使用真实服务' : '本地引擎，无需额外配置'}
                                </p>
                              </div>
                              {expandedProvider === category.id ? (
                                <ChevronDown className="w-4 h-4 text-muted-foreground" />
                              ) : (
                                <ChevronRight className="w-4 h-4 text-muted-foreground" />
                              )}
                            </div>

                            {expandedProvider === category.id && (
                              <div className="ml-9 space-y-1.5 mt-2 mb-4">
                                {provider.models.map(m => (
                                  <div key={m.name} className="flex items-center gap-3 px-3 py-2 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors">
                                    <Wand2 className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
                                    <div className="flex-1 min-w-0">
                                      <span className="text-sm font-mono">{m.name}</span>
                                      {m.recommended && (
                                        <Badge className="ml-2 text-[9px] bg-primary/10 text-primary border-primary/20">推荐</Badge>
                                      )}
                                    </div>
                                    <span className="text-xs text-muted-foreground hidden sm:block">{m.description}</span>
                                    {category.id === 'llm' && provider.status === 'mock' && (
                                      <FlaskConical className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                                    )}
                                    {provider.status === 'active' && (
                                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                                    )}
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        )
                      })()}

                      {/* Generator cards */}
                      {category.generators.map(gen => (
                        <Card key={gen.name} className="border-border/50 bg-muted/10">
                          <CardHeader className="pb-3">
                            <div className="flex items-center justify-between">
                              <div>
                                <CardTitle className="text-sm flex items-center gap-2">
                                  <Sparkles className="w-3.5 h-3.5" style={{ color: category.color }} />
                                  {gen.name}
                                </CardTitle>
                                <CardDescription className="text-xs mt-1">{gen.description}</CardDescription>
                              </div>
                              <Badge variant="outline" className="text-[10px]">{gen.type}</Badge>
                            </div>
                          </CardHeader>
                          {gen.parameters && Object.keys(gen.parameters).length > 0 && (
                            <CardContent className="pt-0">
                              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                                {Object.entries(gen.parameters).map(([key, param]) => (
                                  <div key={key} className="px-2.5 py-1.5 rounded-lg bg-background/50 border border-border/30">
                                    <p className="text-xs font-medium">{key}</p>
                                    <p className="text-[10px] text-muted-foreground truncate">{param.description}</p>
                                    {param.required && (
                                      <Badge className="text-[9px] mt-1 bg-red-500/10 text-red-400 border-red-500/20">必填</Badge>
                                    )}
                                  </div>
                                ))}
                              </div>
                            </CardContent>
                          )}
                        </Card>
                      ))}
                    </div>
                  )}
                </section>
              ))}
            </div>
          )}

          {/* Legend */}
          <div className="mt-12 pt-6 border-t border-border/50">
            <p className="text-xs text-muted-foreground mb-3">图例</p>
            <div className="flex flex-wrap gap-3">
              {Object.entries(CATEGORY_CONFIG).map(([id, cfg]) => (
                <div key={id} className="flex items-center gap-2 text-xs text-muted-foreground">
                  <div className="w-3 h-3 rounded" style={{ backgroundColor: cfg.color + '30' }} />
                  <span>{cfg.label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </ScrollArea>
    </AppShell>
  )
}
