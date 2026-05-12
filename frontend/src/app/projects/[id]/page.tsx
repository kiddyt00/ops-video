'use client'

import { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useQueryClient } from '@tanstack/react-query'
import { useProject } from '@/hooks/use-projects'
import { useTasks } from '@/hooks/use-tasks'
import { useWorkflowStatus } from '@/hooks/use-workflow'
import { useFiles } from '@/hooks/use-files'
import { AppShell } from '@/components/app-shell'
import { WorkflowWaterfall } from '@/components/workflow-waterfall'
import { CharacterCardManager } from '@/components/character-card-manager'
import { ChaptersList } from '@/components/chapters-list'
import { StoryEditor } from '@/components/story-editor'
import { ShareDialog } from '@/components/share-dialog'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { AlertCircle, RefreshCw, Share2, Workflow, Users, Film, BookOpen } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { ScrollArea } from '@/components/ui/scroll-area'
import { type TaskStage } from '@/types/task'

export default function ProjectPage() {
  const params = useParams()
  const router = useRouter()
  const projectId = params.id as string
  const [apiError, setApiError] = useState<string | null>(null)

  const queryClient = useQueryClient()
  const { data: project, isLoading: loadingProject, error: projectError } = useProject(projectId)
  const { data: tasks, isLoading: loadingTasks, error: tasksError } = useTasks(projectId)
  const { data: workflowStatus, isLoading: loadingWorkflow, error: workflowError } = useWorkflowStatus(projectId)
  const { data: files } = useFiles(projectId)

  const currentStage = workflowStatus?.current_stage as TaskStage | null

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
      <div className="flex items-center justify-end px-4 pt-3 max-w-4xl mx-auto">
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

      {/* Tabs: 故事 → 章节 → 角色卡 → 工作流 */}
      <Tabs defaultValue="story" className="flex-1 flex flex-col min-h-0">
        <div className="px-4 pt-2 max-w-4xl mx-auto w-full">
          <TabsList className="w-full">
            <TabsTrigger value="story" className="gap-1.5">
              <BookOpen className="w-3.5 h-3.5" />
              故事
            </TabsTrigger>
            <TabsTrigger value="character-cards" className="gap-1.5">
              <Users className="w-3.5 h-3.5" />
              角色卡
            </TabsTrigger>
            <TabsTrigger value="chapters" className="gap-1.5">
              <Film className="w-3.5 h-3.5" />
              章节
            </TabsTrigger>
            <TabsTrigger value="workflow" className="gap-1.5">
              <Workflow className="w-3.5 h-3.5" />
              工作流
            </TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="story" className="flex-1 min-h-0 mt-3">
          <div className="max-w-4xl mx-auto w-full h-full">
            <StoryEditor projectId={projectId} className="h-full" />
          </div>
        </TabsContent>

        <TabsContent value="character-cards" className="flex-1 min-h-0 mt-3">
          <div className="max-w-4xl mx-auto w-full h-full">
            <CharacterCardManager projectId={projectId} className="h-full" />
          </div>
        </TabsContent>

        <TabsContent value="chapters" className="flex-1 min-h-0 mt-3">
          <div className="max-w-6xl mx-auto w-full h-full">
            <ChaptersList projectId={projectId} className="h-full" />
          </div>
        </TabsContent>

        <TabsContent value="workflow" className="flex-1 min-h-0 mt-3">
          <ScrollArea className="h-full">
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
        </TabsContent>
      </Tabs>
    </AppShell>
  )
}
