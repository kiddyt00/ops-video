'use client'

import { useRouter, usePathname } from 'next/navigation'
import { Film, BarChart3, ListTodo, Users, Settings, ExternalLink, ArrowLeft, Menu, X, LogIn, LogOut, HardDrive } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useEffect } from 'react'
import { Loader2 } from 'lucide-react'
import { useAuth } from '@/hooks/use-auth'
import { ThemeToggle } from '@/components/theme-toggle'
import { TimezoneBadge } from '@/components/timezone-badge'

const NAV_ITEMS = [
  { key: 'projects', label: '项目总览', icon: Film, href: '/' },
  { key: 'tasks', label: '任务管理', icon: ListTodo, href: '/tasks' },
  { key: 'users', label: '用户管理', icon: Users, href: '/users' },
  { key: 'models', label: '模型管理', icon: Settings, href: '/models' },
  { key: 'storage', label: '存储管理', icon: HardDrive, href: '/storage' },
]

interface AppShellProps {
  /** Show project name in header with back arrow */
  projectHeader?: {
    name: string
    workflowStatus?: {
      current_stage: string | null
      stages: { stage: string; status: string }[]
    }
  }
  /** Optional right panel content */
  rightPanel?: React.ReactNode
  /** Whether to show the global sidebar (default: true) */
  showSidebar?: boolean
  children: React.ReactNode
}

export function AppShell({ projectHeader, rightPanel, showSidebar = true, children }: AppShellProps) {
  const router = useRouter()
  const pathname = usePathname()
  const { user, isAuthenticated, isLoading, logout } = useAuth()

  // Determine active nav item
  const activeKey = NAV_ITEMS.find(item => pathname === item.href)?.key
    ?? (pathname.startsWith('/projects/') ? 'projects' : 'projects')

  // Redirect to login if not authenticated
  useEffect(() => {
    if (pathname === '/login') return
    if (!isLoading && !isAuthenticated) {
      router.replace('/login')
    }
  }, [isLoading, isAuthenticated, pathname, router])

  if (isLoading) {
    return (
      <div className="h-screen flex items-center justify-center bg-background">
        <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (!isAuthenticated && pathname !== '/login') {
    return null
  }

  const handleLogout = async () => {
    await logout()
    router.push('/login')
  }

  return (
    <div className="h-screen flex flex-col bg-background text-foreground">
      {/* Top header bar */}
      <header className="h-12 border-b border-border flex items-center justify-between px-4 shrink-0 bg-background/95 backdrop-blur">
        <div className="flex items-center gap-3">
          <button
            className="flex items-center gap-2 hover:opacity-80 transition-opacity cursor-pointer"
            onClick={() => router.push('/')}
          >
            <Film className="w-5 h-5 text-primary" />
            <span className="font-bold text-lg tracking-tight">Ops-Video</span>
          </button>
          {projectHeader && (
            <>
              <span className="text-muted-foreground/50">/</span>
              <Button
                variant="ghost"
                size="sm"
                className="gap-1.5 text-sm font-medium truncate max-w-[200px]"
                onClick={() => router.push('/')}
              >
                <ArrowLeft className="w-3.5 h-3.5 shrink-0" />
                <span className="truncate">{projectHeader.name}</span>
              </Button>
              {/* Inline workflow status pills */}
              {projectHeader.workflowStatus?.stages && projectHeader.workflowStatus.stages.length > 0 && (
                <div className="hidden md:flex items-center gap-1 ml-2">
                  {projectHeader.workflowStatus.stages.map((stage) => {
                    const statusColors: Record<string, string> = {
                      completed: 'bg-green-500',
                      running: 'bg-blue-500 animate-pulse',
                      failed: 'bg-red-500',
                      pending: 'bg-muted-foreground/30',
                    }
                    return (
                      <div
                        key={stage.stage}
                        className={cn(
                          'w-2.5 h-2.5 rounded-full transition-colors',
                          statusColors[stage.status] ?? 'bg-muted-foreground/30'
                        )}
                        title={`${stage.stage}: ${stage.status}`}
                      />
                    )
                  })}
                </div>
              )}
            </>
          )}
        </div>

        <div className="flex items-center gap-1">
          <TimezoneBadge />
          <ThemeToggle />
          {isAuthenticated && user ? (
            <DropdownMenu>
              <DropdownMenuTrigger className="inline-flex items-center gap-2 px-2 py-1 rounded-md hover:bg-muted transition-colors cursor-pointer">
                <Avatar className="h-7 w-7">
                  <AvatarFallback className="text-xs bg-primary/10 text-primary">
                    {(user.username || user.email).charAt(0).toUpperCase()}
                  </AvatarFallback>
                </Avatar>
                <span className="text-sm hidden sm:inline">{user.username || user.email}</span>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <div className="px-3 py-2 text-sm text-muted-foreground truncate">
                  {user.email}
                </div>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout} className="text-destructive cursor-pointer">
                  <LogOut className="w-4 h-4 mr-2" />
                  退出登录
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <Button
              variant="ghost"
              size="sm"
              className="gap-2"
              onClick={() => router.push('/login')}
            >
              <LogIn className="w-4 h-4" />
              <span className="hidden sm:inline">登录</span>
            </Button>
          )}
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

      <div className="flex flex-1 overflow-hidden">
        {/* Left sidebar — global navigation */}
        {showSidebar && (
          <aside className="w-[200px] border-r border-border bg-background shrink-0 flex flex-col">
            <ScrollArea className="flex-1">
              <nav className="p-2 space-y-1">
                {NAV_ITEMS.map(item => {
                  const isActive = item.key === activeKey
                  const Icon = item.icon
                  return (
                    <button
                      key={item.key}
                      className={cn(
                        'w-full flex items-center gap-2.5 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                        isActive
                          ? 'bg-primary/10 text-primary'
                          : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                      )}
                      onClick={() => router.push(item.href)}
                    >
                      <Icon className="w-4 h-4 shrink-0" />
                      <span>{item.label}</span>
                    </button>
                  )
                })}
              </nav>
            </ScrollArea>
          </aside>
        )}

        {/* Main content */}
        <main className="flex-1 overflow-hidden flex flex-col">
          {children}
        </main>

        {/* Right panel — optional */}
        {rightPanel && (
          <aside className="w-72 border-l border-border bg-background shrink-0 overflow-y-auto">
            {rightPanel}
          </aside>
        )}
      </div>
    </div>
  )
}
