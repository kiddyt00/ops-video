'use client'

import { cn } from '@/lib/utils'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import {
  FileText,
  ImageIcon,
  Image,
  Music,
  Video,
  CheckCircle2,
  Circle,
  Loader2,
  AlertCircle,
} from 'lucide-react'

interface Stage {
  stage: string
  status: string
  completed_tasks: number
  total_tasks: number
  can_proceed: boolean
}

interface WorkflowProgressProps {
  stages: Stage[]
  currentStage?: string | null
  compact?: boolean
}

const STAGE_CONFIG: Record<string, { label: string; icon: React.ComponentType<{ className?: string }> }> = {
  script: { label: '脚本', icon: FileText },
  storyboard: { label: '分镜', icon: ImageIcon },
  image: { label: '图片', icon: Image },
  audio: { label: '音频', icon: Music },
  video: { label: '视频', icon: Video },
}

const STATUS_CONFIG: Record<string, { color: string; label: string; icon?: React.ComponentType<{ className?: string }> }> = {
  pending: { color: 'text-muted-foreground', label: '待执行', icon: Circle },
  running: { color: 'text-blue-500', label: '运行中', icon: Loader2 },
  completed: { color: 'text-green-500', label: '已完成', icon: CheckCircle2 },
  failed: { color: 'text-red-500', label: '失败', icon: AlertCircle },
}

export function WorkflowProgress({ stages, currentStage, compact = false }: WorkflowProgressProps) {
  const totalStages = stages.length
  const completedCount = stages.filter((s) => s.status === 'completed').length
  const overallProgress = (completedCount / totalStages) * 100

  if (compact) {
    return (
      <div className="flex items-center gap-2">
        {stages.map((stage, index) => {
          const config = STAGE_CONFIG[stage.stage]
          const Icon = config?.icon || Circle
          const statusConfig = STATUS_CONFIG[stage.status]
          const StatusIcon = statusConfig?.icon || Circle

          return (
            <div key={stage.stage} className="flex items-center">
              <div
                className={cn(
                  'w-8 h-8 rounded-full flex items-center justify-center border-2 transition-colors',
                  stage.status === 'completed' && 'border-green-500 bg-green-500/10',
                  stage.status === 'running' && 'border-blue-500 bg-blue-500/10',
                  stage.status === 'pending' && 'border-muted bg-muted/10',
                  stage.status === 'failed' && 'border-red-500 bg-red-500/10'
                )}
                title={`${config?.label}: ${statusConfig?.label}`}
              >
                <StatusIcon className={cn('w-4 h-4', statusConfig?.color, stage.status === 'running' && 'animate-spin')} />
              </div>
              {index < stages.length - 1 && (
                <div
                  className={cn(
                    'w-8 h-0.5 mx-1',
                    stage.status === 'completed' ? 'bg-green-500' : 'bg-muted'
                  )}
                />
              )}
            </div>
          )
        })}
      </div>
    )
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-sm">工作流进度</CardTitle>
            <CardDescription>
              {completedCount} / {totalStages} 阶段完成
            </CardDescription>
          </div>
          <Badge variant={completedCount === totalStages ? 'default' : 'secondary'}>
            {Math.round(overallProgress)}%
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Overall progress bar */}
        <Progress value={overallProgress} className="h-2" />

        {/* Stage details */}
        <div className="space-y-3">
          {stages.map((stage, index) => {
            const config = STAGE_CONFIG[stage.stage]
            const Icon = config?.icon || Circle
            const statusConfig = STATUS_CONFIG[stage.status]
            const StatusIcon = statusConfig?.icon || Circle
            const isCurrentStage = currentStage === stage.stage

            return (
              <div
                key={stage.stage}
                className={cn(
                  'flex items-center gap-3 p-2 rounded-lg transition-colors',
                  isCurrentStage && 'bg-muted/50 border border-muted'
                )}
              >
                {/* Stage icon */}
                <div
                  className={cn(
                    'w-10 h-10 rounded-lg flex items-center justify-center',
                    stage.status === 'completed' && 'bg-green-500/10',
                    stage.status === 'running' && 'bg-blue-500/10',
                    stage.status === 'pending' && 'bg-muted',
                    stage.status === 'failed' && 'bg-red-500/10'
                  )}
                >
                  <Icon
                    className={cn(
                      'w-5 h-5',
                      stage.status === 'completed' && 'text-green-500',
                      stage.status === 'running' && 'text-blue-500',
                      stage.status === 'pending' && 'text-muted-foreground',
                      stage.status === 'failed' && 'text-red-500',
                      stage.status === 'running' && 'animate-spin'
                    )}
                  />
                </div>

                {/* Stage info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">{config?.label}</span>
                    {isCurrentStage && (
                      <Badge variant="outline" className="h-5 text-xs">
                        当前阶段
                      </Badge>
                    )}
                  </div>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <StatusIcon className={cn('w-3 h-3', statusConfig?.color, stage.status === 'running' && 'animate-spin')} />
                      {statusConfig?.label}
                    </span>
                    {stage.total_tasks > 0 && (
                      <>
                        <span>•</span>
                        <span>{stage.completed_tasks}/{stage.total_tasks} 任务</span>
                      </>
                    )}
                  </div>
                </div>

                {/* Progress indicator for current stage */}
                {stage.status === 'running' && stage.total_tasks > 0 && (
                  <div className="w-24">
                    <Progress
                      value={(stage.completed_tasks / stage.total_tasks) * 100}
                      className="h-1.5"
                    />
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
