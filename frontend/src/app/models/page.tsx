'use client'

import { useState } from 'react'
import { Settings, Cpu, ChevronDown, ChevronRight, Loader2, AlertCircle } from 'lucide-react'
import { AppShell } from '@/components/app-shell'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

interface GeneratorInfo {
  name: string
  type: string
  description: string
  parameters: Record<string, { type: string; required: boolean; default?: string | number | boolean; description: string }>
}

async function fetchGenerators(): Promise<GeneratorInfo[]> {
  const { data } = await api.get<GeneratorInfo[]>('/generators')
  return data
}

const TYPE_ICONS: Record<string, string> = {
  llm: '🧠',
  wanx: '🎨',
  tts: '🔊',
  bgm: '🎵',
  video: '🎬',
}

const TYPE_LABELS: Record<string, string> = {
  llm: '大语言模型',
  wanx: '通义万相',
  tts: '语音合成',
  bgm: '背景音乐',
  video: '视频合成',
}

export default function ModelsPage() {
  const { data: generators, isLoading, error } = useQuery({
    queryKey: ['generators'],
    queryFn: fetchGenerators,
  })

  const [expanded, setExpanded] = useState<Record<string, boolean>>({})

  const toggle = (name: string) => {
    setExpanded(prev => ({ ...prev, [name]: !prev[name] }))
  }

  return (
    <AppShell>
      <ScrollArea className="h-full">
        <div className="p-6 max-w-4xl mx-auto">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-semibold flex items-center gap-2">
              <Settings className="w-6 h-6" />
              模型管理
            </h2>
            <span className="text-sm text-muted-foreground">
              {generators?.length ?? 0} 个生成器
            </span>
          </div>

          {error && (
            <div className="flex items-start gap-2 text-sm text-destructive bg-destructive/10 rounded-md p-3 mb-4">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>加载模型信息失败</span>
            </div>
          )}

          {isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-24 w-full" />
              ))}
            </div>
          ) : generators && generators.length > 0 ? (
            <div className="space-y-3">
              {generators.map(gen => {
                const isExpanded = expanded[gen.name]
                return (
                  <Card key={gen.name}>
                    <CardHeader
                      className="pb-2 cursor-pointer hover:bg-muted/50 transition-colors"
                      onClick={() => toggle(gen.name)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          {isExpanded ? (
                            <ChevronDown className="w-5 h-5 text-muted-foreground shrink-0" />
                          ) : (
                            <ChevronRight className="w-5 h-5 text-muted-foreground shrink-0" />
                          )}
                          <div>
                            <CardTitle className="text-base flex items-center gap-2">
                              <span className="text-lg">{TYPE_ICONS[gen.type] ?? '⚙️'}</span>
                              {gen.name}
                            </CardTitle>
                            <CardDescription className="text-xs">{gen.description}</CardDescription>
                          </div>
                        </div>
                        <Badge variant="outline" className="text-xs">
                          {TYPE_LABELS[gen.type] ?? gen.type}
                        </Badge>
                      </div>
                    </CardHeader>
                    {isExpanded && gen.parameters && Object.keys(gen.parameters).length > 0 && (
                      <CardContent className="pt-4">
                        <h4 className="text-sm font-semibold mb-2">参数</h4>
                        <div className="space-y-2">
                          {Object.entries(gen.parameters).map(([key, param]) => (
                            <div key={key} className="flex items-start justify-between py-2 border-t border-border">
                              <div>
                                <p className="text-sm font-medium">{key}</p>
                                <p className="text-xs text-muted-foreground">{param.description}</p>
                              </div>
                              <div className="text-right shrink-0 ml-4">
                                <Badge variant="secondary" className="text-xs">{param.type}</Badge>
                                {param.default !== undefined && (
                                  <p className="text-xs text-muted-foreground mt-1">
                                    默认: {String(param.default)}
                                  </p>
                                )}
                                {param.required && (
                                  <Badge className="text-xs mt-1" variant="destructive">必填</Badge>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    )}
                  </Card>
                )
              })}
            </div>
          ) : (
            <div className="text-center py-20">
              <Settings className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">暂无模型数据</p>
            </div>
          )}
        </div>
      </ScrollArea>
    </AppShell>
  )
}
