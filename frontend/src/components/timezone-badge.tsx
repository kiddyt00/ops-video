'use client'

import { Globe } from 'lucide-react'
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { useTimezone } from '@/hooks/use-timezone'

export function TimezoneBadge() {
  const { timezone, offset } = useTimezone()

  return (
    <Tooltip>
      <TooltipTrigger className="inline-flex items-center gap-1 px-2 py-1 text-xs text-muted-foreground hover:text-foreground hover:bg-muted rounded-md transition-colors shrink-0 cursor-pointer">
        <Globe className="w-3 h-3" />
        <span className="hidden sm:inline">{timezone}</span>
        <span className="text-[10px] text-muted-foreground/60">({offset})</span>
      </TooltipTrigger>
      <TooltipContent side="bottom" className="text-xs">
        <p>当前时区: {timezone}</p>
        <p>UTC 偏移: {offset}</p>
      </TooltipContent>
    </Tooltip>
  )
}
