'use client'

import { useState } from 'react'
import { Bookmark, ChevronDown, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { usePresets } from '@/hooks/use-presets'
import type { Preset } from '@/types/preset'
import type { TaskStage } from '@/types/task'

const STAGE_TO_GENERATOR: Record<TaskStage, string> = {
  script: 'script',
  storyboard: 'storyboard',
  image: 'image',
  audio: 'tts',
  video: 'video_composer',
}

interface PresetSelectorProps {
  stage: TaskStage | null
  onSelect: (params: Record<string, unknown>) => void
  onOpenManager?: () => void
}

export function PresetSelector({ stage, onSelect, onOpenManager }: PresetSelectorProps) {
  const generatorType = stage ? STAGE_TO_GENERATOR[stage] : undefined
  const { data: presets, isLoading } = usePresets(generatorType)

  if (!stage) return null

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" className="gap-1.5 text-xs">
          <Bookmark className="w-3.5 h-3.5" />
          <span>预设</span>
          <ChevronDown className="w-3 h-3 opacity-50" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-56">
        {isLoading ? (
          <div className="flex items-center justify-center py-4">
            <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
          </div>
        ) : presets && presets.length > 0 ? (
          <>
            {presets.map((preset: Preset) => (
              <DropdownMenuItem
                key={preset.id}
                onClick={() => onSelect(preset.parameters)}
                className="flex flex-col items-start gap-0.5"
              >
                <span className="font-medium text-sm">{preset.name}</span>
                {preset.description && (
                  <span className="text-xs text-muted-foreground truncate w-full">
                    {preset.description}
                  </span>
                )}
              </DropdownMenuItem>
            ))}
            <DropdownMenuSeparator />
          </>
        ) : (
          <div className="px-2 py-3 text-xs text-muted-foreground text-center">
            暂无预设模板
          </div>
        )}
        <DropdownMenuItem
          onClick={(e) => {
            e.preventDefault()
            onOpenManager?.()
          }}
          className="text-xs text-muted-foreground cursor-pointer"
        >
          管理预设...
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
