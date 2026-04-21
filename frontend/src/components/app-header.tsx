'use client'

import { useRouter } from 'next/navigation'
import { Film, ExternalLink, ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

interface AppHeaderProps {
  projectName?: string
  showBack?: boolean
  workflowStatus?: {
    current_stage: string | null
    stages: { stage: string; status: string }[]
  }
}

export function AppHeader({ projectName, showBack, workflowStatus }: AppHeaderProps) {
  const router = useRouter()
  return (
    <header className="h-14 border-b border-border bg-background flex items-center justify-between px-4 shrink-0">
      <div className="flex items-center gap-3">
        {showBack && (
          <Button variant="ghost" size="icon" className="shrink-0" onClick={() => router.push('/projects')}>
            <ArrowLeft className="w-4 h-4" />
          </Button>
        )}
        <button
          className="flex items-center gap-2 hover:opacity-80 transition-opacity"
          onClick={() => router.push('/projects')}
        >
          <Film className="w-5 h-5 text-primary" />
          <span className="font-bold text-lg">Ops-Video</span>
        </button>
        {projectName && (
          <>
            <span className="text-muted-foreground">/</span>
            <span className="font-medium">{projectName}</span>
          </>
        )}
      </div>

      <div className="flex items-center gap-2">
        {workflowStatus?.current_stage && (
          <Badge variant="outline" className="text-xs">
            当前: {workflowStatus.current_stage}
          </Badge>
        )}
        <Button variant="ghost" size="icon" onClick={() => window.open('https://github.com/kiddyt00/ops-video', '_blank', 'noopener,noreferrer')}>
          <ExternalLink className="w-4 h-4" />
        </Button>
      </div>
    </header>
  )
}
