'use client'

import { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useQueryClient } from '@tanstack/react-query'
import { useProject } from '@/hooks/use-projects'
import { useTasks } from '@/hooks/use-tasks'
import { useWorkflowStatus } from '@/hooks/use-workflow'
import { useFiles } from '@/hooks/use-files'
import { useChapter } from '@/hooks/use-chapters'
import { AppShell } from '@/components/app-shell'
import { WorkflowWaterfall } from '@/components/workflow-waterfall'
import { ShareDialog } from '@/components/share-dialog'
import { AlertCircle, RefreshCw, Share2, ArrowLeft, Film } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { cn } from '@/lib/utils'
import { type TaskStage } from '@/types/task'

const statusCfg: Record<string, { label: string; color: string; dot: string }> = {
  completed: { label: '已完成', color: 'text-emerald-400', dot: 'bg-emerald-400' },
  running: { label: '生成中', color: 'text-sky-400', dot: 'bg-sky-400 animate-pulse' },
  failed: { label: '失败', color: 'text-rose-400', dot: 'bg-rose-400' },
  pending: { label: '待开始', color: 'text-zinc-500', dot: 'bg-zinc-600' },
}

export default function ChapterPage() {
  const params = useParams()
  const router = useRouter()
  const projectId = params.id as string
  const chapterId = params.chapterId as string
  const [apiError, setApiError] = useState<string | null>(null)

  const queryClient = useQueryClient()
  const { data: project, isLoading: loadingProject, error: projectError } = useProject(projectId)
  const { data: chapter, isLoading: loadingChapter, error: chapterError } = useChapter(projectId, chapterId)
  const { data: tasks, isLoading: loadingTasks, error: tasksError } = useTasks(projectId)
  const { data: workflowStatus, isLoading: loadingWorkflow, error: workflowError } = useWorkflowStatus(projectId)
  const { data: files } = useFiles(projectId)

  const handleAdvance = async () => {
    setApiError(null)
    try {
      const token = localStorage.getItem('ops-video-tokens')
      const accessToken = token ? JSON.parse(token).access_token : null
      const resp = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/api/v1'}/workflow/${projectId}/advance`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(accessToken ? { 'Authorization': `Bearer ${accessToken}` } : {}),
        },
        body: JSON.stringify({ execute: true }),
      })
      if (!resp.ok) {
        const data = await resp.json()
        throw new Error(data.detail || '推进工作流失败')
      }
      window.location.reload()
    } catch (e: unknown) {
      setApiError(e instanceof Error ? e.message : '推进工作流失败')
    }
  }

  const handleGenerate = async (stage: TaskStage, stageParams: Record<string, unknown>) => {
    setApiError(null)
    try {
      const token = localStorage.getItem('ops-video-tokens')
      const accessToken = token ? JSON.parse(token).access_token : null
      const stageMap: Record<string, string> = {
        script: 'script', storyboard: 'storyboard', image: 'image', audio: 'audio', video: 'video'
      }
      const resp = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/api/v1'}/workflow/${projectId}/advance/${stageMap[stage] || stage}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(accessToken ? { 'Authorization': `Bearer ${accessToken}` } : {}),
        },
        body: JSON.stringify({ parameters: stageParams, execute: true }),
      })
      if (!resp.ok) {
        const data = await resp.json()
        throw new Error(data.detail || '生成任务失败')
      }
      window.location.reload()
    } catch (e: unknown) {
      setApiError(e instanceof Error ? e.message : '生成任务失败')
    }
  }

  const handleRetry = () => {
    setApiError(null)
    window.location.reload()
  }

  const queryError = projectError || chapterError || tasksError || workflowError
  if (queryError) {
    return (
      <div className="h-screen flex flex-col items-center justify-center bg-background text-foreground">
        <AlertCircle className="w-12 h-12 text-destructive mb-4" />
        <h2 className="text-xl font-semibold mb-2">加载失败</h2>
        <p className="text-sm text-muted-foreground mb-4 max-w-md text-center">
          {queryError instanceof Error ? queryError.message : '无法加载章节数据'}
        </p>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => router.push(`/projects/${projectId}`)}>
            <ArrowLeft className="w-3.5 h-3.5 mr-1" />
            返回项目
          </Button>
          <Button onClick={handleRetry}>
            <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
            重试
          </Button>
        </div>
      </div>
    )
  }

  const isLoading = loadingProject || loadingChapter || loadingWorkflow
  if (isLoading) {
    return (
      <AppShell
        projectHeader={{ name: '...', workflowStatus: undefined }}
      >
        <div className="p-6 max-w-2xl mx-auto space-y-4">
          <Skeleton className="h-8 w-48" />
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      </AppShell>
    )
  }

  if (!project) {
    return (
      <div className="h-screen flex flex-col items-center justify-center bg-background text-foreground">
        <h2 className="text-xl font-semibold mb-2">项目不存在</h2>
        <p className="text-sm text-muted-foreground mb-4">找不到该项目，请确认链接是否正确</p>
        <Button onClick={() => router.push('/')}>
          返回项目列表
        </Button>
      </div>
    )
  }

  const status = chapter?.status ?? 'pending'
  const cfg = statusCfg[status] ?? statusCfg.pending

  return (
    <AppShell
      projectHeader={{
        name: project.name,
        workflowStatus: workflowStatus ?? undefined,
      }}
    >
      {apiError && (
        <div className="absolute top-14 left-0 right-0 z-50 p-4">
          <div className="max-w-2xl mx-auto flex items-start gap-2 text-sm text-destructive bg-destructive/10 rounded-md p-3">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{apiError}</span>
          </div>
        </div>
      )}

      {/* Chapter header */}
      <div className="px-4 pt-3 max-w-4xl mx-auto w-full">
        <div className="flex items-center gap-3 mb-3">
          <Button
            variant="ghost"
            size="sm"
            className="gap-1"
            onClick={() => router.push(`/projects/${projectId}`)}
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            返回
          </Button>
          <Separator orientation="vertical" className="h-5" />
          <div className="flex items-center gap-2 min-w-0">
            <Film className="w-4 h-4 text-muted-foreground shrink-0" />
            <h2 className="text-sm font-semibold truncate">
              {chapter?.name || '章节详情'}
            </h2>
            {chapter && (
              <Badge variant="outline" className="text-xs shrink-0">
                第 {chapter.chapter_number} 章
              </Badge>
            )}
            <div className="flex items-center gap-1.5 shrink-0">
              <div className={cn('w-2 h-2 rounded-full', cfg.dot)} />
              <span className={cn('text-xs', cfg.color)}>{cfg.label}</span>
            </div>
          </div>
        </div>
        {chapter?.description && (
          <p className="text-xs text-muted-foreground mb-3 ml-12">{chapter.description}</p>
        )}
      </div>

      <div className="flex items-center justify-end px-4 pt-1 max-w-4xl mx-auto">
        <ShareDialog
          projectId={projectId}
          trigger={
            <Button variant="outline" size="sm" className="gap-1.5">
              <Share2 className="w-3.5 h-3.5" />
              分享
            </Button>
          }
        />
      </div>

      {/* Workflow */}
      <ScrollArea className="h-full mt-2">
        <WorkflowWaterfall
          projectId={projectId}
          tasks={tasks}
          files={files}
          workflowStatus={workflowStatus ?? undefined}
          onGenerate={handleGenerate}
          onAdvance={handleAdvance}
          isLoading={loadingTasks}
          onFilesChange={() => {
            queryClient.invalidateQueries({ queryKey: ['files'] })
            queryClient.invalidateQueries({ queryKey: ['workflow'] })
          }}
        />
      </ScrollArea>
    </AppShell>
  )
}
