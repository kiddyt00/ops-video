'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { ListTodo, Filter, Loader2, CheckCircle2, AlertCircle, Circle, Play } from 'lucide-react'
import { cn, formatRelativeTime } from '@/lib/utils'
import { AppShell } from '@/components/app-shell'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useTasks } from '@/hooks/use-tasks'
import { useProjects } from '@/hooks/use-projects'
import type { Task, TaskStatus, TaskStage } from '@/types/task'

const STATUS_CONFIG: Record<string, { label: string; icon: typeof Circle; color: string }> = {
  completed: { label: '已完成', icon: CheckCircle2, color: 'text-green-500' },
  running: { label: '运行中', icon: Loader2, color: 'text-blue-500' },
  failed: { label: '失败', icon: AlertCircle, color: 'text-red-500' },
  pending: { label: '待执行', icon: Circle, color: 'text-muted-foreground' },
  cancelled: { label: '已取消', icon: AlertCircle, color: 'text-gray-500' },
}

const STAGE_LABELS: Record<string, string> = {
  inspiration: '灵感',
  story: '故事',
  chapter_outline: '章节大纲',
  script: '剧本',
  storyboard: '分镜',
  image: '生图',
  audio: '配音',
  video: '成片',
}

export default function TasksPage() {
  const router = useRouter()
  const { data: tasks, isLoading } = useTasks()
  const { data: projects } = useProjects()
  const [statusFilter, setStatusFilter] = useState<string | null>('all')
  const [stageFilter, setStageFilter] = useState<string | null>('all')

  const projectMap = new Map(projects?.map(p => [p.id, p.name]) ?? [])

  const filteredTasks = (tasks ?? []).filter((task: Task) => {
    if (statusFilter && statusFilter !== 'all' && task.status !== statusFilter) return false
    if (stageFilter && stageFilter !== 'all' && task.stage !== stageFilter) return false
    return true
  })

  // Sort by created_at descending
  filteredTasks.sort((a: Task, b: Task) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())

  return (
    <AppShell>
      <ScrollArea className="h-full">
        <div className="p-6 max-w-5xl mx-auto">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-semibold flex items-center gap-2">
              <ListTodo className="w-6 h-6" />
              任务管理
            </h2>
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1 text-sm text-muted-foreground">
                <Filter className="w-3.5 h-3.5" />
                <span>筛选</span>
              </div>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[120px]">
                  <SelectValue placeholder="状态" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部状态</SelectItem>
                  <SelectItem value="pending">待执行</SelectItem>
                  <SelectItem value="running">运行中</SelectItem>
                  <SelectItem value="completed">已完成</SelectItem>
                  <SelectItem value="failed">失败</SelectItem>
                  <SelectItem value="cancelled">已取消</SelectItem>
                </SelectContent>
              </Select>
              <Select value={stageFilter} onValueChange={setStageFilter}>
                <SelectTrigger className="w-[120px]">
                  <SelectValue placeholder="阶段" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部阶段</SelectItem>
                  {Object.entries(STAGE_LABELS).map(([key, label]) => (
                    <SelectItem key={key} value={key}>{label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 8 }).map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : filteredTasks.length > 0 ? (
            <div className="space-y-2">
              {filteredTasks.map((task: Task) => {
                const statusConf = STATUS_CONFIG[task.status]
                const StatusIcon = statusConf?.icon ?? Circle
                const projectName = projectMap.get(task.project_id) ?? '未知项目'

                return (
                  <Card
                    key={task.id}
                    className="cursor-pointer hover:bg-muted/50 transition-colors"
                    onClick={() => router.push(`/projects/${task.project_id}`)}
                  >
                    <CardContent className="pt-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3 min-w-0">
                          <StatusIcon className={cn('w-5 h-5 shrink-0', statusConf?.color, task.status === 'running' && 'animate-spin')} />
                          <div className="min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="font-medium">{STAGE_LABELS[task.stage] ?? task.stage}</span>
                              <Badge variant="secondary" className="text-xs">{task.generator_type}</Badge>
                            </div>
                            <div className="flex items-center gap-2 text-xs text-muted-foreground mt-0.5">
                              <span className="truncate">{projectName}</span>
                              <span>·</span>
                              <span>{formatRelativeTime(task.created_at)}</span>
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-3 shrink-0">
                          <Badge variant="outline" className="text-xs">
                            {statusConf?.label ?? task.status}
                          </Badge>
                          {task.status === 'pending' && (
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-7 w-7"
                              title="查看项目"
                              onClick={(e) => { e.stopPropagation(); router.push(`/projects/${task.project_id}`) }}
                            >
                              <Play className="w-3.5 h-3.5" />
                            </Button>
                          )}
                        </div>
                      </div>
                      {task.error_message && (
                        <p className="text-xs text-destructive mt-1 ml-8">{task.error_message}</p>
                      )}
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          ) : (
            <div className="text-center py-20">
              <ListTodo className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">暂无任务</p>
            </div>
          )}
        </div>
      </ScrollArea>
    </AppShell>
  )
}
