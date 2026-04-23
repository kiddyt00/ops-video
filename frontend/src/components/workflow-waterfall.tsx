'use client'

import { useState } from 'react'
import { ChevronDown, ChevronRight, Play, Loader2, CheckCircle2, AlertCircle, Circle, ArrowDown } from 'lucide-react'
import { cn, formatRelativeTime } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { ScrollArea } from '@/components/ui/scroll-area'
import { ParameterPanel } from '@/components/parameter-panel'
import { MediaPreviews } from '@/components/media-previews'
import { ArtifactViewer } from '@/components/artifact-viewer'
import { type TaskStage, type Task } from '@/types/task'
import type { FileRecord } from '@/lib/api/files'

const STAGES: { key: TaskStage; label: string; description: string }[] = [
  { key: 'script', label: '脚本', description: '使用 LLM 生成漫剧脚本' },
  { key: 'storyboard', label: '分镜', description: '根据脚本生成分镜描述' },
  { key: 'image', label: '图片', description: '根据分镜生成图片' },
  { key: 'audio', label: '音频', description: '生成配音和音效' },
  { key: 'video', label: '视频', description: '合成最终视频' },
]

const STATUS_CONFIG: Record<string, { label: string; icon: typeof Circle; color: string; bg: string }> = {
  completed: { label: '已完成', icon: CheckCircle2, color: 'text-green-500', bg: 'bg-green-500/10 border-green-500/30' },
  running: { label: '运行中', icon: Loader2, color: 'text-blue-500', bg: 'bg-blue-500/10 border-blue-500/30' },
  failed: { label: '失败', icon: AlertCircle, color: 'text-red-500', bg: 'bg-red-500/10 border-red-500/30' },
  pending: { label: '未开始', icon: Circle, color: 'text-muted-foreground', bg: 'bg-muted/10 border-border' },
  cancelled: { label: '已取消', icon: AlertCircle, color: 'text-gray-500', bg: 'bg-gray-500/10 border-gray-500/30' },
}

interface WorkflowWaterfallProps {
  projectId: string
  tasks?: Task[]
  files?: FileRecord[]
  workflowStatus?: {
    current_stage: string | null
    stages: { stage: string; status: string }[]
  }
  onGenerate: (stage: TaskStage, params: Record<string, unknown>) => void
  onAdvance: () => void
  isLoading?: boolean
}

export function WorkflowWaterfall({
  projectId,
  tasks,
  files,
  workflowStatus,
  onGenerate,
  onAdvance,
  isLoading,
}: WorkflowWaterfallProps) {
  const [expandedStage, setExpandedStage] = useState<TaskStage | null>(null)

  const stageMap = new Map(workflowStatus?.stages.map(s => [s.stage, s.status]) ?? [])
  const currentStage = workflowStatus?.current_stage as TaskStage | null

  const getStageStatus = (stageKey: string): string => {
    const task = tasks?.find(t => t.stage === stageKey)
    if (task) return task.status
    return stageMap.get(stageKey) ?? 'pending'
  }

  const toggleStage = (stage: TaskStage) => {
    setExpandedStage(prev => prev === stage ? null : stage)
  }

  if (isLoading) {
    return (
      <ScrollArea className="h-full">
        <div className="p-6 max-w-2xl mx-auto space-y-4">
          {STAGES.map((_, i) => (
            <div key={i}>
              <Card className="h-16 animate-pulse bg-muted" />
              {i < STAGES.length - 1 && (
                <div className="flex items-center justify-center py-2">
                  <ArrowDown className="w-5 h-5 text-muted-foreground/30" />
                </div>
              )}
            </div>
          ))}
        </div>
      </ScrollArea>
    )
  }

  return (
    <div className="flex h-full">
      {/* Waterfall list */}
      <ScrollArea className="flex-1">
        <div className="p-6 max-w-2xl mx-auto">
          {STAGES.map(({ key, label, description }, index) => {
            const status = getStageStatus(key)
            const statusConf = STATUS_CONFIG[status] ?? STATUS_CONFIG.pending
            const StatusIcon = statusConf.icon
            const isExpanded = expandedStage === key
            const isCurrent = currentStage === key
            const task = tasks?.find(t => t.stage === key)

            return (
              <div key={key}>
                {/* Stage card */}
                <Card
                  className={cn(
                    'cursor-pointer transition-all hover:shadow-md border',
                    statusConf.bg,
                    isExpanded && 'ring-1 ring-primary/20 shadow-md',
                    isCurrent && 'ring-2 ring-blue-500/30',
                  )}
                  onClick={() => toggleStage(key)}
                >
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {isExpanded ? (
                          <ChevronDown className="w-5 h-5 text-muted-foreground shrink-0" />
                        ) : (
                          <ChevronRight className="w-5 h-5 text-muted-foreground shrink-0" />
                        )}
                        <div>
                          <CardTitle className="text-base flex items-center gap-2">
                            {label}
                            <StatusIcon className={cn('w-4 h-4', statusConf.color, status === 'running' && 'animate-spin')} />
                          </CardTitle>
                          <CardDescription className="text-xs">{description}</CardDescription>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="text-xs">
                          {statusConf.label}
                        </Badge>
                        {task && task.started_at && (
                          <span className="text-xs text-muted-foreground">
                            {formatRelativeTime(task.started_at)}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Error message */}
                    {task?.error_message && (
                      <p className="text-xs text-destructive mt-1 ml-8">{task.error_message}</p>
                    )}
                  </CardHeader>
                </Card>

                {/* Expanded detail area */}
                {isExpanded && (
                  <div className="ml-8 mt-2 mb-2">
                    <Card>
                      <CardContent className="pt-4">
                        {/* Task info */}
                        {task ? (
                          <div className="space-y-2 mb-4">
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-muted-foreground">生成器</span>
                              <span>{task.generator_type}</span>
                            </div>
                            {task.started_at && (
                              <div className="flex items-center justify-between text-sm">
                                <span className="text-muted-foreground">开始时间</span>
                                <span>{new Date(task.started_at).toLocaleString('zh-CN')}</span>
                              </div>
                            )}
                            {task.completed_at && (
                              <div className="flex items-center justify-between text-sm">
                                <span className="text-muted-foreground">完成时间</span>
                                <span>{new Date(task.completed_at).toLocaleString('zh-CN')}</span>
                              </div>
                            )}
                          </div>
                        ) : (
                          <p className="text-sm text-muted-foreground mb-4">尚未创建此阶段任务，点击下方按钮开始生成</p>
                        )}

                        <Separator className="my-3" />

                        {/* Actions */}
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation()
                              onGenerate(key, {})
                            }}
                            disabled={status === 'running'}
                          >
                            <Play className="w-3.5 h-3.5 mr-1.5" />
                            {task ? '重新生成' : '生成'}
                          </Button>
                          {status === 'completed' && isCurrent && (
                            <Button size="sm" variant="secondary" onClick={(e) => { e.stopPropagation(); onAdvance() }}>
                              推进到下一阶段
                            </Button>
                          )}
                        </div>
                      </CardContent>
                    </Card>

                    {/* Parameter panel inline */}
                    <Card className="mt-2">
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm">参数设置</CardTitle>
                        <CardDescription>配置 {label} 阶段的生成参数</CardDescription>
                      </CardHeader>
                      <CardContent className="pt-0">
                        <ParameterPanel
                          stage={key}
                          onGenerate={(params) => onGenerate(key, params)}
                          onAdvance={status === 'completed' && isCurrent ? onAdvance : undefined}
                          canGenerate={true}
                          canAdvance={status === 'completed' && isCurrent}
                        />
                      </CardContent>
                    </Card>

                    {/* Artifacts */}
                    {files && files.length > 0 && (
                      <ArtifactViewer stage={key} files={files} />
                    )}
                  </div>
                )}

                {/* Arrow connector */}
                {index < STAGES.length - 1 && (
                  <div className="flex items-center justify-center py-2">
                    <ArrowDown className={cn(
                      'w-5 h-5',
                      status === 'completed' ? 'text-green-500' : 'text-muted-foreground/30'
                    )} />
                  </div>
                )}
              </div>
            )
          })}

          {/* Generated files preview */}
          {files && files.length > 0 && (
            <div className="mt-6">
              <MediaPreviews projectId={projectId} />
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  )
}
