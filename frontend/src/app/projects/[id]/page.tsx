'use client'

import { useParams } from 'next/navigation'
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
import { Play, Loader2 } from 'lucide-react'
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
  const projectId = params.id as string
  const [activeStage, setActiveStage] = useState<TaskStage | null>(null)

  const { data: project, isLoading: loadingProject } = useProject(projectId)
  const { data: tasks, isLoading: loadingTasks } = useTasks(projectId)
  const { data: workflowStatus } = useWorkflowStatus(projectId)
  const advanceWorkflow = useAdvanceWorkflow()

  const currentStage = workflowStatus?.current_stage as TaskStage | null
  const displayStage = activeStage || currentStage

  const completedStages = (workflowStatus?.stages || [])
    .filter((s: { stage: string; status: string }) => s.status === 'completed')
    .map((s: { stage: string }) => s.stage as TaskStage)

  const handleAdvance = async () => {
    await advanceWorkflow.mutateAsync({ projectId })
  }

  return (
    <ThreePanelLayout
      header={{
        projectName: loadingProject ? undefined : project?.name,
        workflowStatus,
      }}
      sidebar={{
        currentStage: displayStage,
        completedStages,
        onSelectStage: setActiveStage,
      }}
      panel={{
        stage: displayStage,
        onAdvance: handleAdvance,
        canAdvance: !!currentStage,
      }}
    >
      <ScrollArea className="h-full">
        <div className="p-6">
          {loadingProject || loadingTasks ? (
            <div className="space-y-4">
              <Skeleton className="h-8 w-48" />
              <Skeleton className="h-4 w-32" />
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
