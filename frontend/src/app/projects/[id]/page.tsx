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
export const dynamic = 'force-dynamic'

import { ChaptersList } from '@/components/chapters-list'
import { StoryEditor } from '@/components/story-editor'
import { ShareDialog } from '@/components/share-dialog'
import { ProviderSelector } from '@/components/provider-selector'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Separator } from '@/components/ui/separator'
import { cn } from '@/lib/utils'
import { useChapters } from '@/hooks/use-chapters'
import {
  AlertCircle, RefreshCw, Share2, Workflow, Users, Film, BookOpen,
  Settings,
} from 'lucide-react'
import { type TaskStage } from '@/types/task'

export default function ProjectPage() {
  const params = useParams()
  const router = useRouter()
  const projectId = params.id as string
  const [apiError, setApiError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState('creation')
  const [selectedChapter, setSelectedChapter] = useState<{ id: string; name: string } | null>(null)
  const queryClient = useQueryClient()
  const { data: project, isLoading: loadingProject, error: projectError } = useProject(projectId)
  const { data: tasks, isLoading: loadingTasks, error: tasksError } = useTasks(projectId)
  const { data: workflowStatus, isLoading: loadingWorkflow, error: workflowError } = useWorkflowStatus(projectId)
  const { data: files } = useFiles(projectId)
  const { data: chapters } = useChapters(projectId)

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
          ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        },
        body: JSON.stringify({ execute: true }),
      })
      if (!resp.ok) {
        const data = await resp.json()
        throw new Error(data.detail || '推进工作流失败')
      }
      queryClient.invalidateQueries({ queryKey: ['tasks', projectId] })
      queryClient.invalidateQueries({ queryKey: ['workflow', projectId] })
      queryClient.invalidateQueries({ queryKey: ['files', projectId] })
      queryClient.invalidateQueries({ queryKey: ['story', projectId] })
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
        inspiration: 'inspiration', story: 'story', chapter_outline: 'chapter_outline',
        script: 'script', storyboard: 'storyboard', image: 'image', audio: 'audio', video: 'video',
      }
      const resp = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || '/api/v1'}/workflow/${projectId}/advance/${stageMap[stage] || stage}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
          },
          body: JSON.stringify({ parameters: stageParams, execute: true }),
        },
      )
      if (!resp.ok) {
        const data = await resp.json()
        throw new Error(data.detail || '生成任务失败')
      }
      queryClient.invalidateQueries({ queryKey: ['tasks', projectId] })
      queryClient.invalidateQueries({ queryKey: ['workflow', projectId] })
      queryClient.invalidateQueries({ queryKey: ['files', projectId] })
      queryClient.invalidateQueries({ queryKey: ['story', projectId] })
    } catch (e: unknown) {
      setApiError(e instanceof Error ? e.message : '生成任务失败')
    }
  }

  const handleSelectChapter = (chapter: { id: string; name: string }) => {
    setSelectedChapter(chapter)
    setActiveTab('pipeline')
  }

  const handleRetry = () => {
    setApiError(null)
    queryClient.invalidateQueries({ queryKey: ['tasks', projectId] })
    queryClient.invalidateQueries({ queryKey: ['workflow', projectId] })
    queryClient.invalidateQueries({ queryKey: ['files', projectId] })
    queryClient.invalidateQueries({ queryKey: ['story', projectId] })
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
          <Button variant="outline" onClick={() => router.push('/')}>返回项目列表</Button>
          <Button onClick={handleRetry}><RefreshCw className="w-3.5 h-3.5 mr-1.5" />重试</Button>
        </div>
      </div>
    )
  }

  const isLoading = loadingProject || loadingWorkflow
  if (isLoading) {
    return (
      <AppShell projectHeader={{ name: '...', workflowStatus: undefined }}>
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
        <Button onClick={() => router.push('/')}>返回项目列表</Button>
      </div>
    )
  }

  const stages = workflowStatus?.stages ?? []
  const completedStages = stages.filter((s: { status: string }) => s.status === 'completed').length
  const pipelineProgress = stages.length > 0 ? Math.round((completedStages / stages.length) * 100) : 0

  return (
    <AppShell
      projectHeader={{
        name: project.name,
        workflowStatus: workflowStatus ?? undefined,
      }}
    >
      <div className="flex flex-col h-full min-h-0">
        {apiError && (
          <div className="absolute top-14 left-0 right-0 z-50 p-4">
            <div className="max-w-2xl mx-auto flex items-start gap-2 text-sm text-destructive bg-destructive/10 rounded-md p-3">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{apiError}</span>
            </div>
          </div>
        )}

        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col min-h-0">
          <div className="flex items-center justify-between px-4 pt-2 max-w-4xl mx-auto w-full">
            <TabsList>
              <TabsTrigger value="creation" className="gap-1.5">
                <BookOpen className="w-3.5 h-3.5" /> 创作
              </TabsTrigger>
              <TabsTrigger value="pipeline" className="gap-1.5">
                <Workflow className="w-3.5 h-3.5" /> 管线
                {selectedChapter && (
                  <span className="text-[10px] text-muted-foreground ml-1">· {selectedChapter.name}</span>
                )}
              </TabsTrigger>
              <TabsTrigger value="settings" className="gap-1.5">
                <Settings className="w-3.5 h-3.5" /> 设置
              </TabsTrigger>
            </TabsList>
            <ShareDialog
              projectId={projectId}
              trigger={
                <Button variant="outline" size="sm" className="gap-1.5">
                  <Share2 className="w-3.5 h-3.5" /> 分享
                </Button>
              }
            />
          </div>

          {/* ══════ 📖 创作 Tab ══════ */}
          <TabsContent value="creation" className="flex-1 min-h-0 mt-3">
            <ScrollArea className="h-full">
              <div className="max-w-4xl mx-auto px-4 pb-8 space-y-6">
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <BookOpen className="w-4 h-4 text-primary" />
                    <h3 className="text-sm font-semibold">故事设定</h3>
                  </div>
                  <StoryEditor projectId={projectId} />
                </div>

                <Separator />

                <div>
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <Film className="w-4 h-4 text-primary" />
                      <h3 className="text-sm font-semibold">章节大纲</h3>
                      {chapters && (
                        <Badge variant="secondary" className="text-[10px]">{chapters.length} 章</Badge>
                      )}
                    </div>
                    {chapters && chapters.length > 0 && (
                      <Button
                        variant="ghost" size="sm" className="text-xs gap-1"
                        onClick={() => setActiveTab('pipeline')}
                      >
                        进入管线 <Workflow className="w-3 h-3" />
                      </Button>
                    )}
                  </div>
                  <ChaptersList
                    projectId={projectId}
                    onSelectChapter={handleSelectChapter}
                  />
                </div>

                <Separator />

                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <Users className="w-4 h-4 text-primary" />
                    <h3 className="text-sm font-semibold">角色三视图</h3>
                  <p className="text-[11px] text-muted-foreground">在角色设定中点击「生成三视图」生成正/侧/背视图</p>
                  </div>
                </div>
              </div>
            </ScrollArea>
          </TabsContent>

          {/* ══════ 🏗️ 管线 Tab ══════ */}
          <TabsContent value="pipeline" className="flex-1 min-h-0 mt-3">
            <ScrollArea className="h-full">
              <div className="max-w-4xl mx-auto px-4 pb-8">
                {chapters && chapters.length > 0 && (
                  <div className="flex items-center gap-2 mb-4 p-3 rounded-lg border bg-card/50">
                    <span className="text-xs text-muted-foreground shrink-0">当前章节:</span>
                    <div className="flex gap-1.5 flex-wrap">
                      {chapters.map((ch: { id: string; name: string; chapter_number?: number; status?: string }) => (
                        <button
                          key={ch.id}
                          onClick={() => setSelectedChapter({ id: ch.id, name: ch.name })}
                          className={cn(
                            'px-2.5 py-1 rounded-md text-xs font-medium transition-colors',
                            selectedChapter?.id === ch.id
                              ? 'bg-primary/20 text-primary border border-primary/30'
                              : 'bg-muted/50 text-muted-foreground hover:text-foreground border border-border/50',
                          )}
                        >
                          第{ch.chapter_number || '?'}章
                          {ch.status === 'completed' ? ' ✅' : ch.status === 'running' ? ' 🔄' : ''}
                        </button>
                      ))}
                    </div>
                    {!selectedChapter && chapters.length > 0 && (
                      <span className="text-[10px] text-muted-foreground ml-auto">请选择一章开始生成</span>
                    )}
                  </div>
                )}

                {stages.length > 0 && (
                  <div className="flex items-center gap-2 mb-4 text-xs text-muted-foreground">
                    <span>管线进度: {completedStages}/{stages.length} 阶段</span>
                    <div className="flex-1 h-1.5 rounded-full bg-muted/30 overflow-hidden max-w-[200px]">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-violet-500 to-sky-400 transition-all duration-500"
                        style={{ width: `${pipelineProgress}%` }}
                      />
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
                  chapterId={selectedChapter?.id}
                  chapterName={selectedChapter?.name}
                  onFilesChange={() => {
                    queryClient.invalidateQueries({ queryKey: ['files'] })
                    queryClient.invalidateQueries({ queryKey: ['workflow'] })
                  }}
                />
              </div>
            </ScrollArea>
          </TabsContent>

          {/* ══════ ⚙️ 设置 Tab ══════ */}
          <TabsContent value="settings" className="flex-1 min-h-0 mt-3">
            <ScrollArea className="h-full">
              <div className="max-w-2xl mx-auto p-6 space-y-6">
                <div className="border rounded-lg p-4">
                  <ProviderSelector projectId={projectId} />
                </div>
              </div>
            </ScrollArea>
          </TabsContent>
        </Tabs>
      </div>
    </AppShell>
  )
}
