'use client'

import { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useProject } from '@/hooks/use-projects'
import { useTasks } from '@/hooks/use-tasks'
import { useWorkflowStatus } from '@/hooks/use-workflow'
import { useFiles } from '@/hooks/use-files'
import { AppShell } from '@/components/app-shell'
import { WorkflowWaterfall } from '@/components/workflow-waterfall'
import { AlertCircle, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { ScrollArea } from '@/components/ui/scroll-area'
import { type TaskStage } from '@/types/task'

export default function ProjectPage() {
  const params = useParams()
  const router = useRouter()
  const projectId = params.id as string
  const [apiError, setApiError] = useState<string | null>(null)

  const { data: project, isLoading: loadingProject, error: projectError } = useProject(projectId)
  const { data: tasks, isLoading: loadingTasks, error: tasksError } = useTasks(projectId)
  const { data: workflowStatus, isLoading: loadingWorkflow, error: workflowError } = useWorkflowStatus(projectId)
  const { data: files } = useFiles(projectId)

  const currentStage = workflowStatus?.current_stage as TaskStage | null

  const handleAdvance = async () => {
    setApiError(null)
    // We'll import and call the advance mutation here
    try {
      const resp = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/workflow/${projectId}/advance`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })
      if (!resp.ok) {
        const data = await resp.json()
        throw new Error(data.detail || '推进工作流失败')
      }
      // Force re-fetch by reloading
      window.location.reload()
    } catch (e: unknown) {
      setApiError(e instanceof Error ? e.message : '推进工作流失败')
    }
  }

  const handleGenerate = async (stage: TaskStage, stageParams: Record<string, unknown>) => {
    setApiError(null)
    try {
      const resp = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/workflow/${projectId}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          generator_type: stage,
          parameters: stageParams,
        }),
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

  const queryError = projectError || tasksError || workflowError
  if (queryError) {
    return (
      <div className="h-screen flex flex-col items-center justify-center bg-background text-foreground">
        <AlertCircle className="w-12 h-12 text-destructive mb-4" />
        <h2 className="text-xl font-semibold mb-2">加载失败</h2>
        <p className="text-sm text-muted-foreground mb-4 max-w-md text-center">
          {queryError instanceof Error ? queryError.message : '无法加载项目数据'}
        </p>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => router.push('/')}>
            返回项目列表
          </Button>
          <Button onClick={handleRetry}>
            <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
            重试
          </Button>
        </div>
      </div>
    )
  }

  const isLoading = loadingProject || loadingWorkflow
  if (isLoading) {
    return (
      <AppShell
        projectHeader={{ name: '...', workflowStatus: undefined }}
      >
        <div className="p-6 max-w-2xl mx-auto space-y-4">
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
      <WorkflowWaterfall
        projectId={projectId}
        tasks={tasks}
        files={files}
        workflowStatus={workflowStatus ?? undefined}
        onGenerate={handleGenerate}
        onAdvance={handleAdvance}
        isLoading={loadingTasks}
        onFilesChange={() => window.location.reload()}
      />
    </AppShell>
  )
}
