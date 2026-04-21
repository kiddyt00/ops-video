'use client'

import { cn } from '@/lib/utils'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Play, RefreshCw, Settings } from 'lucide-react'
import { type TaskStage } from '@/types/task'

interface ParameterPanelProps {
  className?: string
  stage?: TaskStage | null
  parameters?: Record<string, unknown>
  onGenerate?: () => void
  onAdvance?: () => void
  onRollback?: () => void
  canGenerate?: boolean
  canAdvance?: boolean
  children?: React.ReactNode
}

const STAGE_LABELS: Record<string, string> = {
  script: '脚本生成',
  storyboard: '分镜生成',
  image: '图片生成',
  audio: '音频生成',
  video: '视频合成',
}

export function ParameterPanel({
  className,
  stage,
  parameters,
  onGenerate,
  onAdvance,
  onRollback,
  canGenerate = false,
  canAdvance = false,
  children,
}: ParameterPanelProps) {
  return (
    <div className={cn('w-72 border-l border-border bg-muted/20 flex flex-col shrink-0', className)}>
      <div className="p-3 border-b border-border">
        <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">参数面板</h3>
      </div>
      <ScrollArea className="flex-1">
        <div className="p-3 space-y-3">
          {stage && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">{STAGE_LABELS[stage] || stage}</CardTitle>
                <CardDescription>当前阶段操作</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {onGenerate && (
                  <Button size="sm" className="w-full" onClick={onGenerate} disabled={!canGenerate}>
                    <Play className="w-3.5 h-3.5 mr-1.5" />
                    生成
                  </Button>
                )}
                {onAdvance && (
                  <Button
                    size="sm"
                    variant="secondary"
                    className="w-full"
                    onClick={onAdvance}
                    disabled={!canAdvance}
                  >
                    推进到下一阶段
                  </Button>
                )}
                {onRollback && (
                  <Button size="sm" variant="outline" className="w-full" onClick={onRollback}>
                    <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
                    回退
                  </Button>
                )}
              </CardContent>
            </Card>
          )}

          {parameters && Object.keys(parameters).length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-1.5">
                  <Settings className="w-3.5 h-3.5" />
                  参数
                </CardTitle>
              </CardHeader>
              <CardContent>
                <dl className="space-y-2">
                  {Object.entries(parameters).map(([key, value]) => (
                    <div key={key} className="flex justify-between text-xs">
                      <dt className="text-muted-foreground">{key}</dt>
                      <dd className="font-mono truncate max-w-[140px]">
                        {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                      </dd>
                    </div>
                  ))}
                </dl>
              </CardContent>
            </Card>
          )}

          {children}
        </div>
      </ScrollArea>
    </div>
  )
}
