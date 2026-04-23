'use client'

import { cn } from '@/lib/utils'
import { CheckCircle2, Circle, Loader2, AlertCircle } from 'lucide-react'

const STAGES = [
  { key: 'script', label: '脚本' },
  { key: 'storyboard', label: '分镜' },
  { key: 'image', label: '图片' },
  { key: 'audio', label: '音频' },
  { key: 'video', label: '视频' },
]

const STATUS_CONFIG: Record<string, { label: string; icon: React.ComponentType<{ className?: string }> }> = {
  completed: { label: '已完成', icon: CheckCircle2 },
  running: { label: '运行中', icon: Loader2 },
  failed: { label: '失败', icon: AlertCircle },
  pending: { label: '未开始', icon: Circle },
}

interface WorkflowStepperProps {
  stages?: { stage: string; status: string }[]
  currentStage?: string | null
}

export function WorkflowStepper({ stages, currentStage }: WorkflowStepperProps) {
  const stageMap = new Map(stages?.map(s => [s.stage, s.status]) ?? [])
  const completedCount = stages?.filter(s => s.status === 'completed').length ?? 0

  return (
    <div className="py-4">
      <div className="flex items-center justify-between px-4 mb-2">
        <span className="text-sm text-muted-foreground">
          进度 {completedCount} / {STAGES.length} 阶段完成
        </span>
      </div>
      <div className="flex items-center px-4">
        {STAGES.map(({ key, label }, index) => {
          const status = stageMap.get(key) ?? 'pending'
          const isCurrent = currentStage === key
          const isCompleted = status === 'completed'
          const isFailed = status === 'failed'
          const isRunning = status === 'running'
          const isPending = status === 'pending'
          const statusConf = STATUS_CONFIG[status]
          const Icon = statusConf?.icon ?? Circle

          return (
            <div key={key} className="flex items-center flex-1 min-w-0">
              <div className="flex flex-col items-center gap-1 relative">
                <div
                  className={cn(
                    'w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all shrink-0',
                    isCompleted && 'border-green-500 bg-green-500/10',
                    isRunning && 'border-blue-500 bg-blue-500/10',
                    isFailed && 'border-red-500 bg-red-500/10',
                    isPending && 'border-muted bg-muted/10',
                    isCurrent && 'ring-2 ring-blue-500/30 ring-offset-2 ring-offset-background animate-pulse',
                  )}
                  title={`${label}: ${statusConf?.label}`}
                >
                  <Icon
                    className={cn(
                      'w-5 h-5',
                      isCompleted && 'text-green-500',
                      isRunning && 'text-blue-500',
                      isFailed && 'text-red-500',
                      isPending && 'text-muted-foreground',
                      isRunning && 'animate-spin',
                    )}
                  />
                </div>
                <span className={cn(
                  'text-xs font-medium truncate max-w-[60px] text-center',
                  isCompleted && 'text-green-500',
                  isRunning && 'text-blue-500',
                  isFailed && 'text-red-500',
                  isPending && 'text-muted-foreground',
                )}>
                  {label}
                </span>
              </div>

              {/* Connector line */}
              {index < STAGES.length - 1 && (
                <div
                  className={cn(
                    'flex-1 h-0.5 mx-2 mb-6 rounded transition-colors',
                    isCompleted ? 'bg-green-500' : 'bg-muted',
                  )}
                />
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
