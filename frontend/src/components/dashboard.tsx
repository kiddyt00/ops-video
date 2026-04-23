'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Download, Film, FileText, Music, Image, CheckCircle, XCircle, Clock, PlayCircle } from 'lucide-react'
import type { DashboardResponse, VideoStatistics } from '@/lib/api/analytics'

interface DashboardProps {
  data: DashboardResponse
  onExportReport: () => void
}

export function Dashboard({ data, onExportReport }: DashboardProps) {
  const { metrics, statistics, recent_tasks, files_by_type, project_name } = data

  return (
    <div className="space-y-6">
      {/* Header with export button */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">项目仪表盘</h2>
          <p className="text-sm text-muted-foreground">{project_name}</p>
        </div>
        <Button variant="outline" onClick={onExportReport}>
          <Download className="w-4 h-4 mr-2" />
          导出报告
        </Button>
      </div>

      {/* Metrics grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {metrics.map((metric, index) => (
          <MetricCard key={index} metric={metric} />
        ))}
      </div>

      {/* Video statistics */}
      {statistics.video_stats && (
        <VideoStatsCard videoStats={statistics.video_stats} />
      )}

      {/* Stage progress */}
      <div className="grid gap-6 md:grid-cols-2">
        <StageProgressCard stageStats={statistics.stage_stats} />
        <FileTypeCard filesByType={files_by_type} totalFiles={statistics.file_stats.total_files} />
      </div>

      {/* Recent tasks */}
      <RecentTasksCard tasks={recent_tasks} />
    </div>
  )
}

function MetricCard({ metric }: { metric: { title: string; value: string; trend?: 'up' | 'down' | 'neutral' } }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardDescription>{metric.title}</CardDescription>
        <CardTitle className="text-3xl font-bold">{metric.value}</CardTitle>
      </CardHeader>
      <CardContent>
        {metric.trend === 'up' && <span className="text-xs text-green-600">↑ 良好</span>}
        {metric.trend === 'down' && <span className="text-xs text-red-600">↓ 需关注</span>}
        {metric.trend === 'neutral' && <span className="text-xs text-muted-foreground">-</span>}
      </CardContent>
    </Card>
  )
}

function VideoStatsCard({ videoStats }: { videoStats: VideoStatistics }) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Film className="w-5 h-5" />
          <CardTitle>视频统计</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4 md:grid-cols-3">
          <div>
            <p className="text-sm text-muted-foreground">总时长</p>
            <p className="text-lg font-semibold">{videoStats.duration_formatted}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">总帧数</p>
            <p className="text-lg font-semibold">{videoStats.frame_count.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">帧率</p>
            <p className="text-lg font-semibold">{videoStats.frame_rate} fps</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">分辨率</p>
            <p className="text-lg font-semibold">{videoStats.resolution}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">文件大小</p>
            <p className="text-lg font-semibold">{videoStats.file_size_formatted}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">编码</p>
            <p className="text-lg font-semibold capitalize">{videoStats.codec}</p>
          </div>
        </div>
        {videoStats.has_audio && (
          <div className="mt-4">
            <Badge variant="secondary" className="gap-1">
              <Music className="w-3 h-3" />
              包含音频
            </Badge>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function StageProgressCard({ stageStats }: { stageStats: Array<{ stage: string; total_tasks: number; completed_tasks: number; failed_tasks: number; success_rate: number }> }) {
  const stageLabels: Record<string, string> = {
    script: '脚本',
    storyboard: '分镜',
    image: '图片',
    audio: '音频',
    video: '视频',
  }

  const stageIcons: Record<string, React.ReactNode> = {
    script: <FileText className="w-4 h-4" />,
    storyboard: <Image className="w-4 h-4" />,
    image: <Image className="w-4 h-4" />,
    audio: <Music className="w-4 h-4" />,
    video: <Film className="w-4 h-4" />,
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>阶段进度</CardTitle>
        <CardDescription>各阶段任务完成情况</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {stageStats.map((stage) => (
          <div key={stage.stage} className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                {stageIcons[stage.stage] || <Clock className="w-4 h-4" />}
                <span className="font-medium">{stageLabels[stage.stage] || stage.stage}</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-muted-foreground">
                  {stage.completed_tasks}/{stage.total_tasks}
                </span>
                <Badge variant={stage.success_rate === 100 ? 'default' : stage.success_rate < 50 ? 'destructive' : 'secondary'}>
                  {stage.success_rate}%
                </Badge>
              </div>
            </div>
            <Progress value={stage.success_rate} className="h-2" />
            {stage.failed_tasks > 0 && (
              <p className="text-xs text-red-500 flex items-center gap-1">
                <XCircle className="w-3 h-3" />
                {stage.failed_tasks} 个失败任务
              </p>
            )}
          </div>
        ))}
        {stageStats.length === 0 && (
          <p className="text-sm text-muted-foreground text-center py-4">暂无任务数据</p>
        )}
      </CardContent>
    </Card>
  )
}

function FileTypeCard({ filesByType, totalFiles }: { filesByType: Record<string, number>; totalFiles: number }) {
  const typeLabels: Record<string, { label: string; icon: React.ReactNode }> = {
    image: { label: '图片', icon: <Image className="w-4 h-4" /> },
    video: { label: '视频', icon: <Film className="w-4 h-4" /> },
    audio: { label: '音频', icon: <Music className="w-4 h-4" /> },
    script: { label: '脚本', icon: <FileText className="w-4 h-4" /> },
    storyboard: { label: '分镜', icon: <Image className="w-4 h-4" /> },
  }

  const sortedTypes = Object.entries(filesByType).sort((a, b) => b[1] - a[1])

  return (
    <Card>
      <CardHeader>
        <CardTitle>文件类型分布</CardTitle>
        <CardDescription>共 {totalFiles} 个文件</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {sortedTypes.map(([type, count]) => {
          const percentage = totalFiles > 0 ? (count / totalFiles * 100) : 0
          const typeInfo = typeLabels[type] || { label: type, icon: <FileText className="w-4 h-4" /> }

          return (
            <div key={type} className="space-y-1">
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  {typeInfo.icon}
                  <span>{typeInfo.label}</span>
                </div>
                <span className="text-muted-foreground">{count} ({percentage.toFixed(1)}%)</span>
              </div>
              <Progress value={percentage} className="h-1.5" />
            </div>
          )
        })}
        {sortedTypes.length === 0 && (
          <p className="text-sm text-muted-foreground text-center py-4">暂无文件</p>
        )}
      </CardContent>
    </Card>
  )
}

function RecentTasksCard({ tasks }: { tasks: Array<{ id: string; stage: string; status: string; generator_type: string; created_at: string; completed_at: string | null; error_message: string | null }> }) {
  const stageLabels: Record<string, string> = {
    script: '脚本',
    storyboard: '分镜',
    image: '图片',
    audio: '音频',
    video: '视频',
  }

  const statusConfig: Record<string, { color: string; label: string; icon: React.ReactNode }> = {
    completed: { color: 'text-green-600', label: '已完成', icon: <CheckCircle className="w-4 h-4" /> },
    failed: { color: 'text-red-600', label: '失败', icon: <XCircle className="w-4 h-4" /> },
    running: { color: 'text-blue-600', label: '运行中', icon: <PlayCircle className="w-4 h-4" /> },
    pending: { color: 'text-gray-400', label: '待执行', icon: <Clock className="w-4 h-4" /> },
    cancelled: { color: 'text-gray-400', label: '已取消', icon: <Clock className="w-4 h-4" /> },
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>最近任务</CardTitle>
        <CardDescription>最近创建的 {tasks.length} 个任务</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {tasks.map((task) => {
            const status = statusConfig[task.status] || statusConfig.pending
            return (
              <div key={task.id} className="flex items-center justify-between py-2 border-b last:border-0">
                <div className="flex items-center gap-3">
                  {status.icon}
                  <div>
                    <p className="text-sm font-medium">{stageLabels[task.stage] || task.stage}</p>
                    <p className="text-xs text-muted-foreground">{task.generator_type}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className={`text-sm font-medium ${status.color}`}>{status.label}</p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(task.created_at).toLocaleString('zh-CN')}
                  </p>
                </div>
              </div>
            )
          })}
          {tasks.length === 0 && (
            <p className="text-sm text-muted-foreground text-center py-4">暂无任务记录</p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
