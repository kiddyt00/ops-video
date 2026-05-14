'use client'

import { useRouter } from 'next/navigation'
import { Film, ExternalLink, ArrowLeft, CheckCircle2, Circle, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { ThemeToggle } from '@/components/theme-toggle'
import { TimezoneBadge } from '@/components/timezone-badge'

interface AppHeaderProps {
  projectName?: string
  showBack?: boolean
  workflowStatus?: {
    current_stage: string | null
    stages: { stage: string; status: string; completed_tasks?: number; total_tasks?: number }[]
  }
}

const STATUS_CONFIG: Record<string, { color: string; icon: typeof Circle }> = {
  pending: { color: 'text-muted-foreground', icon: Circle },
  running: { color: 'text-blue-500', icon: Loader2 },
  completed: { color: 'text-green-500', icon: CheckCircle2 },
  failed: { color: 'text-red-500', icon: Circle },
}

export function AppHeader({ projectName, showBack, workflowStatus }: AppHeaderProps) {
  const router = useRouter()

  return (
    <header className="h-14 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-blur]:bg-background/90 flex items-center justify-between px-4 shrink-0">
      <div className="flex items-center gap-3">
        {showBack && (
          <Button variant="ghost" size="icon" className="shrink-0 hover:bg-muted" onClick={() => router.push('/projects')}>
            <ArrowLeft className="w-4 h-4" />
          </Button>
        )}
        <button
          className="flex items-center gap-2 hover:opacity-80 transition-opacity"
          onClick={() => router.push('/projects')}
        >
          <Film className="w-5 h-5 text-primary" />
          <span className="font-bold text-lg tracking-tight">Ops-Video</span>
        </button>
        {projectName && (
          <>
            <span className="text-muted-foreground/50">/</span>
            <span className="font-medium truncate max-w-[200px]">{projectName}</span>
          </>
        )}
      </div>

      <div className="flex items-center gap-3">
        {/* Workflow stage indicators */}
        {workflowStatus?.stages && workflowStatus.stages.length > 0 && (
          <div className="hidden md:flex items-center gap-1.5 px-3 py-1.5 bg-muted/50 rounded-full border border-border">
            {workflowStatus.stages.map((stage, index) => {
              const statusConfig = STATUS_CONFIG[stage.status] || STATUS_CONFIG.pending
              const StatusIcon = statusConfig.icon
              const isLast = index === workflowStatus.stages.length - 1

              return (
                <div key={stage.stage} className="flex items-center">
                  <div
                    className={cn(
                      'w-6 h-6 rounded-full flex items-center justify-center transition-colors',
                      stage.status === 'completed' && 'bg-green-500/20',
                      stage.status === 'running' && 'bg-blue-500/20',
                      stage.status === 'pending' && 'bg-muted',
                      stage.status === 'failed' && 'bg-red-500/20'
                    )}
                    title={`${stage.stage}: ${stage.status}`}
                  >
                    <StatusIcon className={cn('w-3 h-3', statusConfig.color, stage.status === 'running' && 'animate-spin')} />
                  </div>
                  {!isLast && (
                    <div
                      className={cn(
                        'w-4 h-0.5 mx-0.5',
                        stage.status === 'completed' ? 'bg-green-500/50' : 'bg-muted'
                      )}
                    />
                  )}
                </div>
              )
            })}
          </div>
        )}

        {workflowStatus?.current_stage && (
          <Badge variant="outline" className="hidden sm:inline-flex text-xs font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-green-500 mr-1.5 animate-pulse" />
            {workflowStatus.current_stage === 'script' && '脚本'}
            {workflowStatus.current_stage === 'storyboard' && '分镜'}
            {workflowStatus.current_stage === 'image' && '图片'}
            {workflowStatus.current_stage === 'audio' && '音频'}
            {workflowStatus.current_stage === 'video' && '视频'}
          </Badge>
        )}

        <TimezoneBadge />
        <ThemeToggle />
        <Button
          variant="ghost"
          size="icon"
          className="shrink-0 hover:bg-muted"
          onClick={() => window.open('https://github.com/kiddyt00/ops-video', '_blank', 'noopener,noreferrer')}
        >
          <ExternalLink className="w-4 h-4" />
        </Button>
      </div>
    </header>
  )
}
