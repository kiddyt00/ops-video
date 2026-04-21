'use client'

import { useParams, useRouter } from 'next/navigation'
import { useState } from 'react'
import { ThreePanelLayout } from '@/components/three-panel-layout'
import { useProject } from '@/hooks/use-projects'
import { useTasks } from '@/hooks/use-tasks'
import { useWorkflowStatus, useAdvanceWorkflow } from '@/hooks/use-workflow'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Play, Loader2, ArrowLeft, AlertCircle, RefreshCw } from 'lucide-react'
import { type TaskStage, type TaskStatus } from '@/types/task'

const STAGE_LABELS: Record<string, string> = {
  script: '脚本',
  storyboard: '分镜',
  image: '图片',
  audio: '音频',
  video: '视频',
}

const STATUS_CONFIG: Record<string, { color: string; label: string }> = {
  pending: { color: 'bg-yellow-500', label: '待执行' },
  running: { color: 'bg-blue-500', label: '运行中' },
  completed: { color: 'bg-green-500', label: '已完成' },
  failed: { color: 'bg-red-500', label: '失败' },
  cancelled: { color: 'bg-gray-500', label: '已取消' },
}

export default function ProjectPage() {
  const params = useParams()
  const router = useRouter()
  const projectId = params.id as string
  const [activeStage, setActiveStage] = useState<TaskStage | null>(null)
  const [apiError, setApiError] = useState<string | null>(null)

  const { data: project, isLoading: loadingProject, error: projectError } = useProject(projectId)
  const { data: tasks, isLoading: loadingTasks, error: tasksError } = useTasks(projectId)
  const { data: workflowStatus, isLoading: loadingWorkflow, error: workflowError } = useWorkflowStatus(projectId)
  const advanceWorkflow = useAdvanceWorkflow()

  const currentStage = workflowStatus?.current_stage as TaskStage | null
  const displayStage = activeStage || currentStage

  const completedStages = (workflowStatus?.stages || [])
    .filter((s: { stage: string; status: string }) => s.status === 'completed')
    .map((s: { stage: string }) => s.stage as TaskStage)

  const handleAdvance = async () => {
    setApiError(null)
    try {
      await advanceWorkflow.mutateAsync({ projectId })
    } catch (e: unknown) {
      setApiError(e instanceof Error ? e.message : '推进工作流失败')
    }
  }

  const handleGenerate = async (stageParams: Record<string, unknown>) => {
    setApiError(null)
    try {
      await advanceWorkflow.mutateAsync({
        projectId,
        params: {
          generator_type: displayStage ?? 'script',
          parameters: stageParams,
        },
      })
    } catch (e: unknown) {
      setApiError(e instanceof Error ? e.message : '生成任务失败')
    }
  }

  const handleRetry = () => {
    setApiError(null)
    // Refetch all data
    window.location.reload()
  }

  // Show error if any core query failed
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
          <Button variant="outline" onClick={() => router.push('/projects')}>
            <ArrowLeft className="w-3.5 h-3.5 mr-1.5" />
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
      <div className="h-screen flex flex-col">
        <div className="h-14 border-b border-border px-4 flex items-center gap-2">
          <Skeleton className="h-6 w-32" />
          <Skeleton className="h-4 w-20" />
        </div>
        <div className="flex flex-1">
          <div className="w-48 border-r border-border p-2 space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-9 w-full rounded-md" />
            ))}
          </div>
          <div className="flex-1 p-6 space-y-4">
            <Skeleton className="h-8 w-48" />
            <Skeleton className="h-4 w-32" />
            <div className="grid gap-4 md:grid-cols-2">
              <Skeleton className="h-32 w-full" />
              <Skeleton className="h-32 w-full" />
            </div>
          </div>
          <div className="w-72 border-l border-border p-3 space-y-3">
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-32 w-full" />
          </div>
        </div>
      </div>
    )
  }

  if (!project) {
    return (
      <div className="h-screen flex flex-col items-center justify-center bg-background text-foreground">
        <h2 className="text-xl font-semibold mb-2">项目不存在</h2>
        <p className="text-sm text-muted-foreground mb-4">找不到该项目，请确认链接是否正确</p>
        <Button onClick={() => router.push('/projects')}>
          <ArrowLeft className="w-3.5 h-3.5 mr-1.5" />
          返回项目列表
        </Button>
      </div>
    )
  }

  return (
    <ThreePanelLayout
      header={{
        projectName: project.name,
        showBack: true,
        workflowStatus,
      }}
      sidebar={{
        currentStage: displayStage,
        completedStages,
        onSelectStage: setActiveStage,
      }}
      panel={{
        stage: displayStage,
        onGenerate: handleGenerate,
        onAdvance: handleAdvance,
        canGenerate: !!displayStage,
        canAdvance: !!currentStage,
      }}
    >
      <ScrollArea className="h-full">
        <div className="p-6">
          {apiError && (
            <div className="flex items-start gap-2 text-sm text-destructive bg-destructive/10 rounded-md p-3 mb-4">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{apiError}</span>
            </div>
          )}
          {loadingTasks ? (
            <div className="space-y-4">
              <Skeleton className="h-8 w-48" />
              <div className="grid gap-4 md:grid-cols-2">
                <Skeleton className="h-32 w-full" />
                <Skeleton className="h-32 w-full" />
              </div>
            </div>
          ) : tasks && tasks.length > 0 ? (
            <div>
              <h2 className="text-xl font-semibold mb-4">任务列表</h2>
              <div className="grid gap-3 md:grid-cols-2">
                {tasks.map(task => {
                  const status = STATUS_CONFIG[task.status]
                  return (
                    <Card key={task.id}>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm flex items-center justify-between">
                          {STAGE_LABELS[task.stage] || task.stage}
                          <span className="flex items-center gap-1.5">
                            <span className={`w-2 h-2 rounded-full ${status?.color}`} />
                            <span className="text-xs text-muted-foreground">{status?.label}</span>
                          </span>
                        </CardTitle>
                        <CardDescription className="text-xs">
                          类型: {task.generator_type}
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        {task.error_message && (
                          <p className="text-xs text-destructive mb-2">{task.error_message}</p>
                        )}
                        <div className="flex gap-2 text-xs text-muted-foreground">
                          {task.started_at && <span>开始: {new Date(task.started_at).toLocaleString('zh-CN')}</span>}
                        </div>
                      </CardContent>
                    </Card>
                  )
                })}
              </div>
            </div>
          ) : (
            <div className="text-center py-20">
              <Play className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground mb-2">该项目还没有任务</p>
              <p className="text-sm text-muted-foreground mb-4">点击右侧面板的「推进到下一阶段」开始工作流</p>
            </div>
          )}
        </div>
      </ScrollArea>
    </ThreePanelLayout>
  )
}
