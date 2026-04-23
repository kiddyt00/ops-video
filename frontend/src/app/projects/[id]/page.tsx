'use client'

import { useParams, useRouter } from 'next/navigation'
import { useState } from 'react'
import { ThreePanelLayout } from '@/components/three-panel-layout'
import { useProject } from '@/hooks/use-projects'
import { useTasks } from '@/hooks/use-tasks'
import { useWorkflowStatus, useWorkflowHistory, useAdvanceWorkflow } from '@/hooks/use-workflow'
import { useFiles, useFileUrl } from '@/hooks/use-files'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Play, Loader2, ArrowLeft, AlertCircle, RefreshCw, Image as ImageIcon, Music, Film, BarChart3 } from 'lucide-react'
import { WorkflowProgress } from '@/components/workflow-progress'
import { Dashboard } from '@/components/dashboard'
import { useDashboardData, useExportReport } from '@/hooks/use-analytics'
import { type TaskStage, type TaskStatus } from '@/types/task'
import type { FileType } from '@/types/file'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

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

function fileDownloadUrl(fileId: string): string {
  return `${API_BASE_URL}/files/${fileId}/url`
}

/** Media preview section shown below task list */
function MediaPreviews({ projectId }: { projectId: string }) {
  const { data: files, isLoading } = useFiles(projectId)

  if (isLoading) {
    return (
      <div className="mt-6">
        <h2 className="text-xl font-semibold mb-4">生成的文件</h2>
        <div className="grid gap-4 md:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-40 w-full rounded-md" />
          ))}
        </div>
      </div>
    )
  }

  if (!files || files.length === 0) {
    return null
  }

  const imageFiles = files.filter(f => f.file_type === 'image')
  const videoFiles = files.filter(f => f.file_type === 'video')
  const audioFiles = files.filter(f => f.file_type === 'audio')
  const scriptFiles = files.filter(f => f.file_type === 'script')
  const storyboardFiles = files.filter(f => f.file_type === 'storyboard')

  return (
    <div className="mt-6 space-y-6">
      {/* Script files */}
      {scriptFiles.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-2">脚本文件</h3>
          <div className="grid gap-2 md:grid-cols-2">
            {scriptFiles.map(f => (
              <Card key={f.id}>
                <CardContent className="pt-4">
                  <p className="text-sm font-medium truncate">{f.file_path.split('/').pop()}</p>
                  <p className="text-xs text-muted-foreground">{new Date(f.created_at).toLocaleString('zh-CN')}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Storyboard files */}
      {storyboardFiles.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-2">分镜文件</h3>
          <div className="grid gap-2 md:grid-cols-2">
            {storyboardFiles.map(f => (
              <Card key={f.id}>
                <CardContent className="pt-4">
                  <p className="text-sm font-medium truncate">{f.file_path.split('/').pop()}</p>
                  <p className="text-xs text-muted-foreground">{new Date(f.created_at).toLocaleString('zh-CN')}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Image files — thumbnail grid */}
      {imageFiles.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-2">
            <ImageIcon className="w-4 h-4 inline mr-1" />
            图片 ({imageFiles.length})
          </h3>
          <div className="grid gap-3 grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
            {imageFiles.map(f => (
              <ImageCard key={f.id} file={f} />
            ))}
          </div>
        </div>
      )}

      {/* Audio files — audio player */}
      {audioFiles.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-2">
            <Music className="w-4 h-4 inline mr-1" />
            音频 ({audioFiles.length})
          </h3>
          <div className="grid gap-2 md:grid-cols-2">
            {audioFiles.map(f => (
              <AudioCard key={f.id} file={f} />
            ))}
          </div>
        </div>
      )}

      {/* Video files — video player */}
      {videoFiles.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-2">
            <Film className="w-4 h-4 inline mr-1" />
            视频 ({videoFiles.length})
          </h3>
          <div className="grid gap-4 md:grid-cols-2">
            {videoFiles.map(f => (
              <VideoCard key={f.id} file={f} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function ImageCard({ file }: { file: { id: string; file_path: string; created_at: string; generation_params?: Record<string, unknown> } }) {
  const [url, setUrl] = useState<string | null>(null)

  const handleLoad = async () => {
    try {
      const resp = await fetch(fileDownloadUrl(file.id))
      const data = await resp.json()
      setUrl(`${API_BASE_URL}/files/${file.id}/download`)
    } catch {
      setUrl(`${API_BASE_URL}/files/${file.id}/download`)
    }
  }

  return (
    <Card className="overflow-hidden">
      <div className="aspect-square bg-muted relative">
        {url ? (
          <img
            src={url}
            alt={file.file_path.split('/').pop()}
            className="w-full h-full object-cover"
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = 'none'
              const parent = (e.target as HTMLImageElement).parentElement
              if (parent) {
                parent.innerHTML = `<div class="flex items-center justify-center h-full text-muted-foreground"><svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg></div>`
              }
            }}
          />
        ) : (
          <button onClick={handleLoad} className="w-full h-full flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors">
            <ImageIcon className="w-8 h-8" />
          </button>
        )}
      </div>
      <CardContent className="p-2">
        <p className="text-xs text-muted-foreground truncate">{file.file_path.split('/').pop()}</p>
      </CardContent>
    </Card>
  )
}

function AudioCard({ file }: { file: { id: string; file_path: string; created_at: string; generation_params?: Record<string, unknown> } }) {
  const [audioUrl, setAudioUrl] = useState<string | null>(null)

  const handleLoad = () => {
    setAudioUrl(`${API_BASE_URL}/files/${file.id}/download`)
  }

  const params = file.generation_params as Record<string, unknown> | undefined
  const typeLabel = params?.type ? String(params.type).toUpperCase() : 'AUDIO'

  return (
    <Card>
      <CardContent className="pt-4 space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Music className="w-4 h-4 text-muted-foreground" />
            <Badge variant="secondary" className="text-xs">{typeLabel}</Badge>
          </div>
          <p className="text-xs text-muted-foreground truncate max-w-[120px]">{file.file_path.split('/').pop()}</p>
        </div>
        {audioUrl ? (
          <audio controls src={audioUrl} className="w-full h-8" />
        ) : (
          <Button variant="outline" size="sm" className="w-full text-xs" onClick={handleLoad}>
            加载播放器
          </Button>
        )}
      </CardContent>
    </Card>
  )
}

function VideoCard({ file }: { file: { id: string; file_path: string; created_at: string } }) {
  const [videoUrl, setVideoUrl] = useState<string | null>(null)

  const handleLoad = () => {
    setVideoUrl(`${API_BASE_URL}/files/${file.id}/download`)
  }

  return (
    <Card className="overflow-hidden">
      <div className="aspect-[9/16] bg-muted max-h-[400px]">
        {videoUrl ? (
          <video controls src={videoUrl} className="w-full h-full object-contain" />
        ) : (
          <div className="flex flex-col items-center justify-center h-full gap-2">
            <Film className="w-12 h-12 text-muted-foreground" />
            <Button variant="outline" size="sm" onClick={handleLoad}>
              加载视频
            </Button>
          </div>
        )}
      </div>
      <CardContent className="p-2">
        <p className="text-xs text-muted-foreground truncate">{file.file_path.split('/').pop()}</p>
      </CardContent>
    </Card>
  )
}

export default function ProjectPage() {
  const params = useParams()
  const router = useRouter()
  const projectId = params.id as string
  const [activeStage, setActiveStage] = useState<TaskStage | null>(null)
  const [activeTab, setActiveTab] = useState<'tasks' | 'dashboard'>('tasks')
  const [apiError, setApiError] = useState<string | null>(null)

  const { data: project, isLoading: loadingProject, error: projectError } = useProject(projectId)
  const { data: tasks, isLoading: loadingTasks, error: tasksError } = useTasks(projectId)
  const { data: workflowStatus, isLoading: loadingWorkflow, error: workflowError } = useWorkflowStatus(projectId)
  const { data: dashboardData, isLoading: loadingDashboard } = useDashboardData(projectId)
  const exportReport = useExportReport()
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

          {/* Tabs for Tasks and Dashboard */}
          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'tasks' | 'dashboard')} className="w-full">
            <TabsList className="mb-4">
              <TabsTrigger value="tasks" className="gap-1">
                <Film className="w-4 h-4" />
                任务
              </TabsTrigger>
              <TabsTrigger value="dashboard" className="gap-1">
                <BarChart3 className="w-4 h-4" />
                仪表盘
              </TabsTrigger>
            </TabsList>

            {/* Tasks Tab */}
            <TabsContent value="tasks" className="mt-0">
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
                              类型：{task.generator_type}
                            </CardDescription>
                          </CardHeader>
                          <CardContent>
                            {task.error_message && (
                              <p className="text-xs text-destructive mb-2">{task.error_message}</p>
                            )}
                            <div className="flex gap-2 text-xs text-muted-foreground">
                              {task.started_at && <span>开始：{new Date(task.started_at).toLocaleString('zh-CN')}</span>}
                            </div>
                          </CardContent>
                        </Card>
                      )
                    })}
                  </div>
                  <MediaPreviews projectId={projectId} />
                </div>
              ) : (
                <div className="text-center py-20">
                  <Play className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                  <p className="text-muted-foreground mb-2">该项目还没有任务</p>
                  <p className="text-sm text-muted-foreground mb-4">点击右侧面板的「推进到下一阶段」开始工作流</p>
                </div>
              )}
            </TabsContent>

            {/* Dashboard Tab */}
            <TabsContent value="dashboard" className="mt-0">
              {loadingDashboard ? (
                <div className="space-y-4">
                  <Skeleton className="h-8 w-48" />
                  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                    {Array.from({ length: 4 }).map((_, i) => (
                      <Skeleton key={i} className="h-24 w-full" />
                    ))}
                  </div>
                </div>
              ) : dashboardData ? (
                <Dashboard
                  data={dashboardData}
                  onExportReport={() => exportReport.mutate(projectId)}
                />
              ) : null}
            </TabsContent>
          </Tabs>
        </div>
      </ScrollArea>
    </ThreePanelLayout>
  )
}
