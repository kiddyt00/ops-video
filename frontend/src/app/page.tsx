'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Plus, Loader2, Trash2, AlertCircle, Clock, CheckCircle2 } from 'lucide-react'
import { cn, formatRelativeTime } from '@/lib/utils'
import { AppShell } from '@/components/app-shell'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
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
import { useProjects, useCreateProject, useDeleteProject } from '@/hooks/use-projects'
import { useTasks } from '@/hooks/use-tasks'
import { ErrorBoundary } from '@/components/error-boundary'
import type { Task } from '@/types/task'

const STAGE_ORDER = ['script', 'storyboard', 'image', 'audio', 'video']

function ProjectCard({ project }: { project: { id: string; name: string; description: string | null; created_at: string } }) {
  const router = useRouter()
  const deleteProject = useDeleteProject()
  const { data: tasks } = useTasks(project.id)

  const completedCount = (tasks ?? []).filter((t: Task) => t.status === 'completed').length

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

  return (
    <Card
      className="cursor-pointer hover:border-primary transition-colors group relative"
      onClick={() => router.push(`/projects/${project.id}`)}
    >
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span className="truncate">{project.name}</span>
          <Button
            variant="ghost"
            size="icon"
            className="opacity-0 group-hover:opacity-100 transition-opacity h-7 w-7"
            onClick={handleDelete}
          >
            <Trash2 className="w-3.5 h-3.5 text-destructive" />
          </Button>
        </CardTitle>
        <CardDescription>
          {project.description || '暂无描述'}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <div className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            <span>{formatRelativeTime(project.created_at)}</span>
          </div>
          <div className="flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3" />
            <span>已完成 {completedCount}/{STAGE_ORDER.length}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function ProjectsOverview() {
  const router = useRouter()
  const { data: projects, isLoading, error } = useProjects()
  const createProject = useCreateProject()
  const [showDialog, setShowDialog] = useState(false)
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
      setShowDialog(false)
    } catch (e: unknown) {
      setMutateError(e instanceof Error ? e.message : '创建项目失败')
    }
  }

  return (
    <AppShell>
      <ScrollArea className="h-full">
        <div className="p-6 max-w-5xl mx-auto">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-semibold">项目总览</h2>
            <Button onClick={() => {
              setMutateError(null)
              setNameError(null)
              setShowDialog(true)
            }}>
              <Plus className="w-4 h-4 mr-1.5" />
              新建项目
            </Button>
          </div>

          {error && (
            <div className="flex items-start gap-2 text-sm text-destructive bg-destructive/10 rounded-md p-3 mb-4">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{error instanceof Error ? error.message : '加载项目失败'}</span>
            </div>
          )}

          {isLoading ? (
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
          ) : projects && projects.length > 0 ? (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {projects.map(project => (
                <ProjectCard key={project.id} project={project} />
              ))}
            </div>
          ) : (
            <div className="text-center py-20">
              <p className="text-muted-foreground mb-4">还没有项目，创建一个开始吧</p>
              <Button onClick={() => setShowDialog(true)}>
                <Plus className="w-4 h-4 mr-1.5" />
                新建项目
              </Button>
            </div>
          )}
        </div>
      </ScrollArea>

      <Dialog open={showDialog} onOpenChange={(open) => {
        setShowDialog(open)
        if (!open) {
          setNameError(null)
          setMutateError(null)
        }
      }}>
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
                onChange={e => {
                  setNewName(e.target.value)
                  if (nameError) validateName(e.target.value)
                }}
                onBlur={() => validateName(newName)}
                placeholder="输入项目名称"
                autoFocus
                className={cn(nameError && 'border-destructive')}
              />
              {nameError && <p className="text-xs text-destructive mt-1">{nameError}</p>}
            </div>
            <div>
              <label className="text-sm font-medium mb-1.5 block">描述（可选）</label>
              <Input
                value={newDesc}
                onChange={e => setNewDesc(e.target.value)}
                placeholder="项目描述"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setShowDialog(false)
              setNameError(null)
              setMutateError(null)
            }}>
              取消
            </Button>
            <Button onClick={handleCreate} disabled={!newName.trim() || createProject.isPending}>
              {createProject.isPending && <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />}
              创建
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
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
