'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Plus, Loader2, Trash2, AlertCircle, Clock, CheckCircle2, RotateCcw, ShieldBan, Sparkles, ArrowRight, Wand2 } from 'lucide-react'
import { cn, formatRelativeTime } from '@/lib/utils'
import { AppShell } from '@/components/app-shell'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import {
  useProjects,
  useMyProjects,
  useSharedProjects,
  useRecycleBin,
  useCreateProject,
  useDeleteProject,
  useRestoreProject,
  usePermanentDeleteProject,
} from '@/hooks/use-projects'
import { useTasks } from '@/hooks/use-tasks'
import { useWorkflowStatus } from '@/hooks/use-workflow'
import { useAuth } from '@/hooks/use-auth'
import { ErrorBoundary } from '@/components/error-boundary'
import type { Task } from '@/types/task'
import type { Project } from '@/types/project'

const STAGE_ORDER = ['inspiration', 'story', 'chapter_outline', 'script', 'storyboard', 'image', 'audio', 'video']

type TabKey = 'mine' | 'shared' | 'recycle'

// ─── Project Card ─────────────────────────────────────────────────────

function ProjectCard({
  project,
  showDelete = true,
  showRestore = false,
  showPermanentDelete = false,
  onRestore,
  onPermanentDelete,
}: {
  project: Project
  showDelete?: boolean
  showRestore?: boolean
  showPermanentDelete?: boolean
  onRestore?: (id: string) => void
  onPermanentDelete?: (id: string) => void
}) {
  const router = useRouter()
  const deleteProject = useDeleteProject()
  const { data: workflowStatus } = useWorkflowStatus(project.id)
  const { data: tasks } = useTasks(project.id, { enabled: !showRestore && !showPermanentDelete })

  const stages = workflowStatus?.stages ?? []
  const completedStages = stages.filter((s: { status: string }) => s.status === 'completed').length
  const progress = stages.length > 0 ? Math.round((completedStages / stages.length) * 100) : 0

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation()
    if (confirm('确定删除此项目？删除后的项目可在回收站中恢复。')) {
      try {
        await deleteProject.mutateAsync(project.id)
      } catch (e: unknown) {
        alert(e instanceof Error ? e.message : '删除项目失败')
      }
    }
  }

  const handleRestore = (e: React.MouseEvent) => {
    e.stopPropagation()
    onRestore?.(project.id)
  }

  const handlePermanentDelete = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (confirm('确定永久删除此项目？此操作不可撤销！')) {
      onPermanentDelete?.(project.id)
    }
  }

  return (
    <Card
      className={cn(
        'cursor-pointer hover:border-primary transition-colors group relative',
        (showRestore || showPermanentDelete) && 'opacity-70 hover:opacity-100'
      )}
      onClick={() => !showRestore && !showPermanentDelete && router.push(`/projects/${project.id}`)}
    >
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span className="truncate">{project.name}</span>
          <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
            {showDelete && (
              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={handleDelete}>
                <Trash2 className="w-3.5 h-3.5 text-destructive" />
              </Button>
            )}
            {showRestore && (
              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={handleRestore} title="恢复">
                <RotateCcw className="w-3.5 h-3.5 text-green-500" />
              </Button>
            )}
            {showPermanentDelete && (
              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={handlePermanentDelete} title="永久删除">
                <ShieldBan className="w-3.5 h-3.5 text-destructive" />
              </Button>
            )}
          </div>
        </CardTitle>
        <CardDescription>{project.description || '暂无描述'}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {!showRestore && !showPermanentDelete && stages.length > 0 && (
            <div>
              <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
                <span>进度</span>
                <span>{completedStages}/{stages.length} 阶段</span>
              </div>
              <div className="w-full h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-violet-500 to-sky-400 transition-all duration-500"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <Clock className="w-3 h-3" />
            <span>{formatRelativeTime(project.updated_at || project.created_at)}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// ─── Create Project Dialog ────────────────────────────────────────────

function CreateProjectDialog({
  open,
  onOpenChange,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const createProject = useCreateProject()
  const [newName, setNewName] = useState('')
  const [newDesc, setNewDesc] = useState('')
  const [nameError, setNameError] = useState<string | null>(null)
  const [mutateError, setMutateError] = useState<string | null>(null)

  const validateName = (name: string): boolean => {
    if (!name.trim()) {
      setNameError('项目名称不能为空')
      return false
    }
    if (name.trim().length < 2) {
      setNameError('项目名称至少 2 个字符')
      return false
    }
    setNameError(null)
    return true
  }

  const handleCreate = async () => {
    setMutateError(null)
    if (!validateName(newName)) return
    try {
      await createProject.mutateAsync({
        name: newName.trim(),
        description: newDesc.trim() || undefined,
      })
      setNewName('')
      setNewDesc('')
      setNameError(null)
      onOpenChange(false)
    } catch (e: unknown) {
      setMutateError(e instanceof Error ? e.message : '创建项目失败')
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>新建项目</DialogTitle>
          <DialogDescription>为你的漫剧短片创建一个新项目</DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          {mutateError && (
            <div className="flex items-start gap-2 text-sm text-destructive bg-destructive/10 rounded-md p-2">
              <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
              <span>{mutateError}</span>
            </div>
          )}
          <div>
            <label className="text-sm font-medium mb-1.5 block">项目名称 <span className="text-destructive">*</span></label>
            <Input
              value={newName}
              onChange={e => { setNewName(e.target.value); if (nameError) validateName(e.target.value) }}
              onBlur={() => validateName(newName)}
              placeholder="输入项目名称"
              autoFocus
              className={cn(nameError && 'border-destructive')}
            />
            {nameError && <p className="text-xs text-destructive mt-1">{nameError}</p>}
          </div>
          <div>
            <label className="text-sm font-medium mb-1.5 block">描述（可选）</label>
            <Input value={newDesc} onChange={e => setNewDesc(e.target.value)} placeholder="项目描述" />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>取消</Button>
          <Button onClick={handleCreate} disabled={!newName.trim() || createProject.isPending}>
            {createProject.isPending && <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />}
            创建
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─── Project Grid ─────────────────────────────────────────────────────

function ProjectGrid({
  projects,
  isLoading,
  error,
  emptyMessage,
  showDelete,
  showRestore,
  showPermanentDelete,
  onRestore,
  onPermanentDelete,
}: {
  projects: Project[] | undefined
  isLoading: boolean
  error: Error | null
  emptyMessage: string
  showDelete?: boolean
  showRestore?: boolean
  showPermanentDelete?: boolean
  onRestore?: (id: string) => Promise<void>
  onPermanentDelete?: (id: string) => Promise<void>
}) {
  if (isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <Card key={i}>
            <CardHeader>
              <Skeleton className="h-5 w-3/4" />
              <Skeleton className="h-4 w-full mt-2" />
            </CardHeader>
          </Card>
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-start gap-2 text-sm text-destructive bg-destructive/10 rounded-md p-3">
        <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
        <span>{error instanceof Error ? error.message : '加载失败'}</span>
      </div>
    )
  }

  if (!projects || projects.length === 0) {
    return <p className="text-center py-12 text-muted-foreground">{emptyMessage}</p>
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {projects.map(project => (
        <ProjectCard
          key={project.id}
          project={project}
          showDelete={showDelete}
          showRestore={showRestore}
          showPermanentDelete={showPermanentDelete}
          onRestore={onRestore}
          onPermanentDelete={onPermanentDelete}
        />
      ))}
    </div>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────

function ProjectsOverview() {
  const router = useRouter()
  const { isAuthenticated } = useAuth()
  const [activeTab, setActiveTab] = useState<TabKey>('mine')
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [inspiration, setInspiration] = useState('')
  const [isQuickCreating, setIsQuickCreating] = useState(false)

  const createProjectMutation = useCreateProject()

  const handleQuickCreate = async () => {
    const topic = inspiration.trim()
    if (!topic || isQuickCreating) return
    setIsQuickCreating(true)
    try {
      const project = await createProjectMutation.mutateAsync({
        name: topic.slice(0, 30),
        description: `灵感创作: ${topic}`,
      })
      setInspiration('')
      router.push(`/projects/${project.id}`)
    } catch (e) {
      alert(e instanceof Error ? e.message : '创建失败')
    } finally {
      setIsQuickCreating(false)
    }
  }

  const { data: myProjects, isLoading: mineLoading, error: mineError } = useMyProjects()
  const { data: sharedProjects, isLoading: sharedLoading, error: sharedError } = useSharedProjects()
  const { data: recycleProjects, isLoading: recycleLoading, error: recycleError } = useRecycleBin()

  const restoreMutation = useRestoreProject()
  const permanentDeleteMutation = usePermanentDeleteProject()

  const handleRestore = async (id: string) => {
    try {
      await restoreMutation.mutateAsync(id)
    } catch (e) {
      alert(e instanceof Error ? e.message : '恢复失败')
    }
  }

  const handlePermanentDelete = async (id: string) => {
    try {
      await permanentDeleteMutation.mutateAsync(id)
    } catch (e) {
      alert(e instanceof Error ? e.message : '删除失败')
    }
  }

  return (
    <AppShell>
      <ScrollArea className="h-full">
        <div className="p-6 max-w-5xl mx-auto">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-semibold">项目总览</h2>
            {isAuthenticated && (
              <Button onClick={() => setShowCreateDialog(true)}>
                <Plus className="w-4 h-4 mr-1.5" />
                新建项目
              </Button>
            )}
          </div>

          {!isAuthenticated ? (
            <div className="text-center py-20">
              <p className="text-muted-foreground mb-4">登录后即可管理你的项目</p>
              <Button onClick={() => router.push('/login')}>前往登录</Button>
            </div>
          ) : (
            <>
              {/* ── Inspiration quick-create ── */}
              <div className="mb-6 p-6 rounded-2xl border border-violet-500/20 bg-gradient-to-br from-violet-500/5 via-transparent to-sky-500/5">
                <div className="flex items-center gap-2 mb-3">
                  <Wand2 className="w-5 h-5 text-violet-400" />
                  <h3 className="text-sm font-semibold text-white/80">灵感一键创作</h3>
                </div>
                <p className="text-xs text-zinc-500 mb-4">输入一个创意主题，AI 将自动为你生成完整故事</p>
                <div className="flex gap-2">
                  <Input
                    value={inspiration}
                    onChange={(e) => setInspiration(e.target.value)}
                    placeholder="例如：赛博朋克世界的花店少女、修仙界的程序员..."
                    className="flex-1 bg-white/5 border-white/10 text-white placeholder:text-zinc-600"
                    onKeyDown={(e) => { if (e.key === 'Enter') handleQuickCreate() }}
                  />
                  <Button
                    onClick={handleQuickCreate}
                    disabled={!inspiration.trim() || isQuickCreating}
                    className="gap-1.5 bg-violet-600 hover:bg-violet-500"
                  >
                    {isQuickCreating ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Sparkles className="w-4 h-4" />
                    )}
                    开始创作
                    {!isQuickCreating && <ArrowRight className="w-4 h-4" />}
                  </Button>
                </div>
              </div>

              <Tabs value={activeTab} onValueChange={v => setActiveTab(v as TabKey)} className="w-full">
                <TabsList className="mb-6">
                  <TabsTrigger value="mine">我的项目</TabsTrigger>
                  <TabsTrigger value="shared">分享给我</TabsTrigger>
                  <TabsTrigger value="recycle">回收站</TabsTrigger>
                </TabsList>
              </Tabs>

              {activeTab === 'mine' && (
                <ProjectGrid
                  projects={myProjects}
                  isLoading={mineLoading}
                  error={mineError}
                  emptyMessage="还没有项目，点击右上角新建项目开始"
                  showDelete
                />
              )}

              {activeTab === 'shared' && (
                <ProjectGrid
                  projects={sharedProjects}
                  isLoading={sharedLoading}
                  error={sharedError}
                  emptyMessage="没有被分享的项目"
                />
              )}

              {activeTab === 'recycle' && (
                <ProjectGrid
                  projects={recycleProjects}
                  isLoading={recycleLoading}
                  error={recycleError}
                  emptyMessage="回收站为空"
                  showRestore
                  showPermanentDelete
                  onRestore={handleRestore}
                  onPermanentDelete={handlePermanentDelete}
                />
              )}
            </>
          )}
        </div>
      </ScrollArea>

      <CreateProjectDialog open={showCreateDialog} onOpenChange={setShowCreateDialog} />
    </AppShell>
  )
}

export default function HomePage() {
  return (
    <ErrorBoundary>
      <ProjectsOverview />
    </ErrorBoundary>
  )
}
