'use client'

import { useState } from 'react'
import { ChevronDown, Play, Loader2, AlertCircle, Circle, Sparkles, FileText, Image as ImageIcon, Music, Film, Download, Lightbulb, BookOpen, ListTree } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { ParameterPanel } from '@/components/parameter-panel'
import { StageArtifacts } from '@/components/stage-artifacts'
import { GenerationPanel } from '@/components/generation-panel'
import { useEventStream } from '@/hooks/use-event-stream'
import { type TaskStage, type Task } from '@/types/task'
import type { FileRecord } from '@/lib/api/files'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api/v1'

const CREATION_STAGES = new Set(['inspiration', 'story', 'chapter_outline'])

const STAGES: { key: TaskStage; label: string; desc: string; icon: typeof Sparkles; fileType: string }[] = [
  { key: 'inspiration', label: '灵感', desc: 'AI 创意发散', icon: Lightbulb, fileType: 'inspiration' },
  { key: 'story', label: '故事', desc: '故事大纲创作', icon: BookOpen, fileType: 'story' },
  { key: 'chapter_outline', label: '章节', desc: '章节大纲拆解', icon: ListTree, fileType: 'chapter_outline' },
  { key: 'script', label: '剧本', desc: 'AI 编剧创作剧本', icon: FileText, fileType: 'script' },
  { key: 'storyboard', label: '分镜', desc: '拆解为视觉分镜', icon: Sparkles, fileType: 'storyboard' },
  { key: 'image', label: '生图', desc: 'Wan2.6 文生图', icon: ImageIcon, fileType: 'image' },
  { key: 'audio', label: '配音', desc: 'Qwen3-TTS 旁白音效', icon: Music, fileType: 'audio' },
  { key: 'video', label: '成片', desc: '合成最终视频', icon: Film, fileType: 'video' },
]

const statusCfg: Record<string, { label: string; color: string; glow: string; dot: string }> = {
  completed: { label: '完成', color: 'text-emerald-400', glow: 'shadow-emerald-500/20', dot: 'bg-emerald-400' },
  running: { label: '生成中', color: 'text-sky-400', glow: 'shadow-sky-500/30', dot: 'bg-sky-400 animate-pulse' },
  failed: { label: '失败', color: 'text-rose-400', glow: 'shadow-rose-500/20', dot: 'bg-rose-400' },
  pending: { label: '待开始', color: 'text-muted-foreground', glow: '', dot: 'bg-zinc-600' },
  cancelled: { label: '已取消', color: 'text-muted-foreground', glow: '', dot: 'bg-zinc-600' },
}

interface Props {
  projectId: string
  tasks?: Task[]
  files?: FileRecord[]
  workflowStatus?: { current_stage: string | null; stages: { stage: string; status: string }[] }
  onGenerate: (stage: TaskStage, params: Record<string, unknown>) => void
  onAdvance: () => void
  onRunAll?: () => void
  autoRunning?: boolean
  isLoading?: boolean
  onFilesChange?: () => void
  chapterId?: string
  chapterName?: string
}

export function WorkflowWaterfall({ projectId, tasks, files, workflowStatus, onGenerate, onAdvance, onRunAll, autoRunning, isLoading, onFilesChange, chapterId, chapterName }: Props) {
  const [expanded, setExpanded] = useState<TaskStage | null>(null)
  const [panelOpen, setPanelOpen] = useState(false)
  const [streamingStage, setStreamingStage] = useState<TaskStage | null>(null)
  const { events, isStreaming, error, startStream, stopStream, clear } = useEventStream()

  const startStreaming = (stage: TaskStage, params?: Record<string, unknown>) => {
    setStreamingStage(stage)
    setPanelOpen(true)
    clear()
    startStream(`/api/v1/workflow/stream/${projectId}/advance/${stage}`, { parameters: params || {}, execute: true })
  }

  const handlePanelClose = () => {
    setPanelOpen(false)
    setStreamingStage(null)
    stopStream()
  }

  const stageMap = new Map(workflowStatus?.stages.map(s => [s.stage, s.status]) ?? [])
  const currentStage = workflowStatus?.current_stage as TaskStage | null

  const getStatus = (key: string): string => {
    const stageTasks = (tasks ?? []).filter(t => t.stage === key)
    if (stageTasks.some(t => t.status === 'completed')) return 'completed'
    if (stageTasks.some(t => t.status === 'running')) return 'running'
    if (stageTasks.length > 0) return stageTasks[0].status
    return stageMap.get(key) ?? 'pending'
  }

  const getFiles = (fileType: string) => (files ?? []).filter(f => f.file_type === fileType)

  const toggle = (s: TaskStage) => setExpanded(p => p === s ? null : s)

  if (isLoading) {
    return (
      <ScrollArea className="h-full">
        <div className="p-6 max-w-3xl mx-auto space-y-5">
          {STAGES.map((_, i) => (
            <div key={i} className="h-24 rounded-2xl bg-muted/30 animate-pulse" />
          ))}
        </div>
      </ScrollArea>
    )
  }

  return (
    <div className="h-full">
      <ScrollArea className="h-full">
        <div className="p-6 max-w-3xl mx-auto space-y-0">
          <div className="text-center mb-8">
            <h2 className="text-lg font-semibold text-foreground/90 tracking-wide">生成流水线</h2>
            <p className="text-xs text-muted-foreground mt-1">点击阶段展开查看制品与参数</p>
            {onRunAll && (
              <div className="mt-3">
                <Button size="sm" onClick={onRunAll} disabled={autoRunning} className="gap-1.5 bg-violet-600 hover:bg-violet-500">
                  {autoRunning ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
                  {autoRunning ? '生成中...' : '全部生成'}
                </Button>
              </div>
            )}
            {chapterId && chapterName && (
              <div className="mt-3 inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-violet-500/10 border border-violet-500/20">
                <Film className="w-3.5 h-3.5 text-violet-400" />
                <span className="text-sm text-violet-300 font-medium">{chapterName}</span>
                <Badge variant="outline" className="text-[10px] px-1.5 py-0 bg-violet-500/10 text-violet-300 border-violet-500/20">当前章节</Badge>
              </div>
            )}
          </div>

          <div className="relative">
            {/* Vertical timeline line */}
            <div className="absolute left-8 top-0 bottom-0 w-px bg-border/50" />

            {STAGES.map(({ key, label, desc, icon: Icon, fileType }) => {
              const status = getStatus(key)
              const cfg = statusCfg[status] || statusCfg.pending
              const stageTasks = (tasks ?? []).filter(t => t.stage === key)
              const stageFiles = getFiles(fileType)
              const task = stageTasks.find(t => t.status === 'completed') || stageTasks[0]
              const isCurrent = currentStage === key
              const isOpen = expanded === key
              const isCreation = CREATION_STAGES.has(key)

              // ── Creation stages: compact summary ──
              if (isCreation) {
                if (status === 'completed') {
                  return (
                    <div key={key} className="relative pb-2">
                      <div className="absolute left-8 top-8 -translate-x-1/2 z-10">
                        <div className="w-3.5 h-3.5 rounded-full border-2 border-background bg-violet-400" />
                      </div>
                      <div className="ml-14">
                        <div className="rounded-2xl border border-violet-500/20 bg-violet-500/5 p-4">
                          <div className="flex items-center gap-3">
                            <div className="w-9 h-9 rounded-xl bg-violet-500/15 text-violet-400 flex items-center justify-center shrink-0">
                              <Icon className="w-4 h-4" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <span className="text-sm font-semibold text-foreground/90">{label}</span>
                                <Badge className="text-[10px] px-1.5 py-0 bg-violet-500/15 text-violet-400 border-0">已完成</Badge>
                              </div>
                              <p className="text-xs text-muted-foreground mt-0.5">内容已保存在「创作」Tab</p>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                }
                return (
                  <div key={key} className="relative pb-2">
                    <div className="absolute left-8 top-8 -translate-x-1/2 z-10">
                      <div className="w-3.5 h-3.5 rounded-full border-2 border-background bg-muted-foreground/30" />
                    </div>
                    <div className="ml-14">
                      <div className="rounded-2xl border border-dashed border-border/50 bg-muted/20 p-4">
                        <div className="flex items-center gap-3">
                          <div className="w-9 h-9 rounded-xl bg-muted/30 text-muted-foreground flex items-center justify-center shrink-0">
                            <Icon className="w-4 h-4" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-medium text-muted-foreground">{label}</span>
                              <Badge variant="outline" className="text-[10px] px-1.5 py-0 text-muted-foreground/50 border-muted-foreground/20">待开始</Badge>
                            </div>
                            <p className="text-xs text-muted-foreground/50 mt-0.5">请先在「创作」Tab 中完成{label}设定</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )
              }

              // ══════ Production stages (script → video) ══════
              const hasPreview = stageFiles.length > 0 && (fileType === 'image' || fileType === 'video' || fileType === 'audio')

              return (
                <div key={key} className="relative pb-2">
                  <div className="absolute left-8 top-8 -translate-x-1/2 z-10">
                    <div className={cn('w-3.5 h-3.5 rounded-full border-2 border-background transition-colors', cfg.dot)} />
                  </div>
                  <div className="ml-14">
                    <Card
                      className={cn(
                        'border-0 rounded-2xl transition-all duration-300 cursor-pointer overflow-hidden',
                        'bg-muted/30 backdrop-blur-sm hover:bg-muted/50',
                        isOpen && 'bg-muted/50 ring-1 ring-violet-500/30',
                        isCurrent && status === 'running' && 'ring-1 ring-sky-500/40 shadow-lg shadow-sky-500/10',
                        status === 'completed' && 'shadow-lg shadow-emerald-500/5',
                        status === 'failed' && 'ring-1 ring-rose-500/20',
                      )}
                      onClick={() => toggle(key)}
                    >
                      <div className="flex items-center gap-4 p-4">
                        <div className={cn(
                          'w-11 h-11 rounded-xl flex items-center justify-center shrink-0 transition-colors',
                          status === 'completed' ? 'bg-emerald-500/10 text-emerald-400' :
                          status === 'running' ? 'bg-sky-500/15 text-sky-400' :
                          status === 'failed' ? 'bg-rose-500/10 text-rose-400' :
                          'bg-muted text-muted-foreground',
                        )}>
                          {status === 'running' ? <Loader2 className="w-5 h-5 animate-spin" /> : <Icon className="w-5 h-5" />}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-semibold text-foreground/90">{label}</span>
                            <Badge variant="outline" className={cn('text-[10px] px-1.5 py-0 border-0', cfg.color, 'bg-muted/30')}>{cfg.label}</Badge>
                          </div>
                          <p className="text-xs text-muted-foreground mt-0.5">{desc}</p>
                        </div>
                        {status === 'completed' && hasPreview && <MiniPreview fileType={fileType} file={stageFiles[0]} />}
                        <div className={cn('transition-transform duration-200', isOpen && 'rotate-180')}>
                          <ChevronDown className="w-4 h-4 text-muted-foreground" />
                        </div>
                      </div>
                      {task?.error_message && (
                        <div className="px-4 pb-3">
                          <div className="text-[11px] text-rose-400/80 bg-rose-500/5 rounded-lg px-3 py-2">{task.error_message.slice(0, 200)}</div>
                        </div>
                      )}
                    </Card>
                    {isOpen && (
                      <div className="mt-2 ml-2 space-y-2 animate-in fade-in slide-in-from-top-2 duration-200">
                        {stageFiles.length > 0 && <StageArtifacts fileType={fileType} files={stageFiles} onFilesChange={onFilesChange} />}
                        <Card className="border-0 rounded-xl bg-muted/20">
                          <CardContent className="p-4">
                            <ParameterPanel stage={key} onGenerate={(params) => onGenerate(key, params)} canGenerate={true} canAdvance={false} />
                            <div className="flex gap-2 mt-3">
                              <Button size="sm" variant="outline" className="text-xs border-border text-foreground/70 hover:bg-muted/50"
                                onClick={(e) => { e.stopPropagation(); startStreaming(key, {}) }}
                                disabled={status === 'running' || isStreaming}>
                                {status === 'running'
                                  ? <><Loader2 className="w-3 h-3 mr-1 animate-spin" />生成中</>
                                  : <><Play className="w-3 h-3 mr-1" />{task ? '重新生成' : '开始生成'}</>}
                              </Button>
                              {status === 'completed' && isCurrent && (
                                <Button size="sm" className="text-xs" onClick={(e) => { e.stopPropagation(); onAdvance() }}>推进下一阶段</Button>
                              )}
                            </div>
                          </CardContent>
                        </Card>
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
          <div className="h-16" />
        </div>
      </ScrollArea>

      <GenerationPanel
        visible={panelOpen}
        events={events}
        isStreaming={isStreaming}
        error={error}
        onClose={handlePanelClose}
        onStop={stopStream}
        onRestart={() => streamingStage && startStreaming(streamingStage)}
      />
    </div>
  )
}

function MiniPreview({ fileType, file }: { fileType: string; file: FileRecord }) {
  const src = `${API_BASE}/files/${file.id}/download`
  if (fileType === 'image') {
    return <div className="w-12 h-12 rounded-lg overflow-hidden bg-zinc-800 shrink-0 ring-1 ring-white/10">
      <img src={src} alt="" className="w-full h-full object-cover" loading="lazy" />
    </div>
  }
  if (fileType === 'video') {
    return <div className="w-12 h-12 rounded-lg overflow-hidden bg-zinc-800 shrink-0 ring-1 ring-white/10 flex items-center justify-center">
      <Film className="w-5 h-5 text-muted-foreground" />
    </div>
  }
  if (fileType === 'audio') {
    return <div className="shrink-0">
      <audio controls src={src} className="h-7 w-32" preload="metadata" />
    </div>
  }
  return null
}
