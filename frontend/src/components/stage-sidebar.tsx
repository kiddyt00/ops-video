'use client'

import { cn } from '@/lib/utils'
import { ScrollArea } from '@/components/ui/scroll-area'
import { FileText, Image, ImageIcon, Music, Video } from 'lucide-react'
import { type TaskStage } from '@/types/task'

const STAGE_CONFIG: { stage: TaskStage; label: string; icon: typeof FileText }[] = [
  { stage: 'script', label: '脚本', icon: FileText },
  { stage: 'storyboard', label: '分镜', icon: ImageIcon },
  { stage: 'image', label: '图片', icon: Image },
  { stage: 'audio', label: '音频', icon: Music },
  { stage: 'video', label: '视频', icon: Video },
]

interface StageSidebarProps {
  currentStage?: TaskStage | null
  completedStages?: TaskStage[]
  onSelectStage?: (stage: TaskStage) => void
}

export function StageSidebar({ currentStage, completedStages = [], onSelectStage }: StageSidebarProps) {
  return (
    <div className="w-48 border-r border-border bg-muted/30 flex flex-col shrink-0">
      <div className="p-3 border-b border-border">
        <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">阶段</h3>
      </div>
      <ScrollArea className="flex-1">
        <nav className="p-2 space-y-1">
          {STAGE_CONFIG.map(({ stage, label, icon: Icon }) => {
            const isCompleted = completedStages.includes(stage)
            const isActive = currentStage === stage
            return (
              <button
                key={stage}
                onClick={() => onSelectStage?.(stage)}
                className={cn(
                  'w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-colors',
                  isActive && 'bg-primary text-primary-foreground',
                  !isActive && 'hover:bg-muted',
                )}
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span className="truncate">{label}</span>
                {isCompleted && !isActive && (
                  <span className="ml-auto w-1.5 h-1.5 rounded-full bg-green-500 shrink-0" />
                )}
              </button>
            )
          })}
        </nav>
      </ScrollArea>
    </div>
  )
}
