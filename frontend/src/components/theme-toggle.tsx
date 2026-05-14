'use client'

import { Sun, Moon, Monitor } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useThemeContext } from '@/components/theme-provider'
import { cn } from '@/lib/utils'

export function ThemeToggle() {
  const { theme, setTheme } = useThemeContext()

  const iconClass = 'w-4 h-4'

  return (
    <DropdownMenu>
      <DropdownMenuTrigger className="inline-flex items-center justify-center rounded-md w-8 h-8 hover:bg-muted transition-colors shrink-0 cursor-pointer">
        <Sun className={cn(iconClass, theme !== 'light' && 'hidden')} />
        <Moon className={cn(iconClass, theme !== 'dark' && 'hidden')} />
        <Monitor className={cn(iconClass, theme !== 'system' && 'hidden')} />
        <span className="sr-only">切换主题</span>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-40">
        <DropdownMenuItem
          onClick={() => setTheme('light')}
          className={cn('cursor-pointer gap-3', theme === 'light' && 'text-primary font-medium')}
        >
          <Sun className="w-4 h-4" />
          <span>浅色</span>
          {theme === 'light' && <span className="ml-auto text-xs text-muted-foreground">✓</span>}
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={() => setTheme('dark')}
          className={cn('cursor-pointer gap-3', theme === 'dark' && 'text-primary font-medium')}
        >
          <Moon className="w-4 h-4" />
          <span>深色</span>
          {theme === 'dark' && <span className="ml-auto text-xs text-muted-foreground">✓</span>}
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={() => setTheme('system')}
          className={cn('cursor-pointer gap-3', theme === 'system' && 'text-primary font-medium')}
        >
          <Monitor className="w-4 h-4" />
          <span>跟随系统</span>
          {theme === 'system' && <span className="ml-auto text-xs text-muted-foreground">✓</span>}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
