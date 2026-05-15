'use client'

import { useState } from 'react'
import { ChevronDown, Play, Loader2, CheckCircle2, Circle, Sparkles, FileText, Image as ImageIcon, Music, Film, Lightbulb, BookOpen, ListTree, AlertCircle, RefreshCw, ArrowRight } from 'lucide-react'
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

const PRODUCTION_STAGES: { key: TaskStage; label: string; desc: string; icon: typeof Sparkles; fileType: string }[] = [
  { key: 'script', label: '剧本', desc: 'AI 编剧创作剧本', icon: FileText, fileType: 'script' },
  { key: 'storyboard', label: '分镜', desc: '拆解为视觉分镜', icon: Sparkles, fileType: 'storyboard' },
  { key: 'image', label: '生图', desc: 'Wan2.6 文生图', icon: ImageIcon, fileType: 'image' },
  { key: 'audio', label: '配音', desc: 'TTS 旁白 + BGM + 音效', icon: Music, fileType: 'audio' },
  { key: 'video', label: '成片', desc: '合成 → 时间轴 → 字幕 → MP4', icon: Film, fileType: 'video' },
]

const CREATION_STAGES: { key: string; label: string }[] = [
  { key: 'inspiration', label: '灵感' },
  { key: 'story', label: '故事' },
  { key: 'chapter_outline', label: '章节' },
  { key: 'chapter_body', label: '正文' },
]

const statusCfg: Record<string, { label: string; color: string; dot: string }> = {
  completed: { label: '完成', color: 'text-emerald-400', dot: 'bg-emerald-400' },
  running: { label: '生成中', color: 'text-sky-400', dot: 'bg-sky-400 animate-pulse' },
  failed: { label: '失败', color: 'text-rose-400', dot: 'bg-rose-400' },
  pending: { label: '待开始', color: 'text-muted-foreground', dot: 'bg-zinc-600' },
  cancelled: { label: '已取消', color: 'text-muted-foreground', dot: 'bg-zinc-600' },
}

interface Props {
  projectId: string
  tasks?: Task[]
  files?: FileRecord[]
  workflowStatus?: { current_stage: string | null; stages: { stage: string; status: string }[] }
  onGenerate: (stage: TaskStage, params: Record<string, unknown>) => Promise<void>
  onAdvance: () => Promise<void>
  isLoading?: boolean
  onFilesChange?: () => void
  chapterId?: string
  chapterName?: string
}

export function WorkflowWaterfall({ projectId, tasks, files, workflowStatus, onGenerate, onAdvance, isLoading, onFilesChange, chapterId, chapterName }: Props) {
  const [expanded, setExpanded] = useState<TaskStage | null>(null)
  const [panelOpen, setPanelOpen] = useState(false)
  const [streamingStage, setStreamingStage] = useState<TaskStage | null>(null)
  const { events, isStreaming, error, startStream, stopStream, clear } = useEventStream()

  const stageMap = new Map(workflowStatus?.stages.map(s => [s.stage, s.status]) ?? [])
  const currentStage = workflowStatus?.current_stage as TaskStage | null

  const getStatus = (key: string): string => {
    const stageTasks = (tasks ?? []).filter(t => t.stage === key)
    if (stageTasks.some(t => t.status === 'completed')) return 'completed'
    if (stageTasks.some(t => t.status === 'running')) return 'running'
    if (stageTasks.length > 0) return stageTasks[0].status
    return stageMap.get(key) ?? 'pending'
  }

  const allCreationDone = CREATION_STAGES.every(s => getStatus(s.key) === 'completed')

  const startStreaming = (stage: TaskStage, params?: Record<string, unknown>) => {
    setStreamingStage(stage); setPanelOpen(true); clear()
    startStream(`/api/v1/workflow/stream/${projectId}/advance/${stage}`, { parameters: params || {}, execute: true })
  }
  const handlePanelClose = () => { setPanelOpen(false); setStreamingStage(null); stopStream() }
  const getFiles = (fileType: string) => (files ?? []).filter(f => f.file_type === fileType)
  const toggle = (s: TaskStage) => setExpanded(p => p === s ? null : s)

  const nextPending = PRODUCTION_STAGES.find(s => getStatus(s.key) !== 'completed')
  const allDone = !nextPending && PRODUCTION_STAGES.every(s => getStatus(s.key) === 'completed')

  if (!!isLoading && !tasks) {
    return <ScrollArea className="h-full"><div className="p-6 max-w-3xl mx-auto space-y-5">
      {[...Array(5)].map((_, i) => <div key={i} className="h-24 rounded-2xl bg-muted/30 animate-pulse" />)}
    </div></ScrollArea>
  }

  return (
    <div className="h-full">
      <ScrollArea className="h-full">
        <div className="p-6 max-w-3xl mx-auto">
          <div className="text-center mb-6">
            <h2 className="text-lg font-semibold text-foreground/90 tracking-wide">生产管线</h2>
            {!allDone && <p className="text-xs text-muted-foreground mt-1">逐阶段生成，每阶段完成后确认再继续</p>}
            {chapterId && chapterName && (
              <div className="mt-3 inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 border border-primary/20">
                <Film className="w-3.5 h-3.5 text-primary" />
                <span className="text-sm text-foreground font-medium">{chapterName}</span>
                <Badge variant="outline" className="text-[10px] px-1.5 py-0 bg-primary/10 text-primary border-primary/20">当前章节</Badge>
              </div>
            )}
            {allDone && (
              <div className="mt-4 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                <CheckCircle2 className="w-6 h-6 text-emerald-500 mx-auto mb-1" />
                <p className="text-sm font-medium text-emerald-600 dark:text-emerald-400">全部阶段已完成</p>
                <p className="text-xs text-muted-foreground mt-1">最终成片已生成，可在下方查看</p>
              </div>
            )}
          </div>

          {/* ── 前期创作状态栏 ── */}
          <div className="mb-6 p-4 rounded-xl border bg-card/50">
            <div className="flex items-center gap-2 mb-3">
              <BookOpen className="w-4 h-4 text-primary" />
              <span className="text-xs font-semibold text-foreground/80">前期创作</span>
              {allCreationDone && <Badge className="text-[10px] px-1.5 py-0 bg-emerald-500/15 text-emerald-500 border-0 ml-auto">全部就绪</Badge>}
            </div>
            <div className="flex items-center gap-3">
              {CREATION_STAGES.map((s, i) => {
                const st = getStatus(s.key)
                return <div key={s.key} className="flex items-center gap-1.5">
                  {st === 'completed' ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" /> :
                   st === 'running' ? <Loader2 className="w-3.5 h-3.5 animate-spin text-sky-500 shrink-0" /> :
                   <Circle className="w-3.5 h-3.5 text-muted-foreground/40 shrink-0" />}
                  <span className={cn('text-xs', st === 'completed' ? 'text-emerald-600 dark:text-emerald-400' : st === 'running' ? 'text-sky-600 dark:text-sky-400' : 'text-muted-foreground/50')}>{s.label}</span>
                  {i < CREATION_STAGES.length - 1 && <ChevronDown className="w-3 h-3 text-muted-foreground/30 -rotate-90" />}
                </div>
              })}
            </div>
            {!allCreationDone && <p className="text-[11px] text-muted-foreground/60 mt-2">请先在「创作」Tab 完成前期创作</p>}
          </div>

          {/* ── 生产阶段 ── */}
          <div className="relative">
            <div className="absolute left-8 top-0 bottom-0 w-px bg-border/50" />
            {PRODUCTION_STAGES.map(({ key, label, desc, icon: Icon, fileType }) => {
              const status = getStatus(key)
              const cfg = statusCfg[status] || statusCfg.pending
              const stageFiles = getFiles(fileType)
              const task = (tasks ?? []).filter(t => t.stage === key).find(t => t.status === 'completed') || (tasks ?? []).filter(t => t.stage === key)[0]
              const isCurrent = currentStage === key
              const isOpen = expanded === key
              const justCompleted = status === 'completed' && isCurrent
              const hasPreview = stageFiles.length > 0 && (fileType === 'image' || fileType === 'video' || fileType === 'audio')

              return <div key={key} className="relative pb-2">
                <div className="absolute left-8 top-8 -translate-x-1/2 z-10">
                  <div className={cn('w-3.5 h-3.5 rounded-full border-2 border-background transition-colors', cfg.dot)} />
                </div>
                <div className="ml-14">
                  <Card className={cn(
                    'border-0 rounded-2xl transition-all duration-300 overflow-hidden',
                    'bg-muted/30 backdrop-blur-sm',
                    justCompleted ? 'ring-1 ring-emerald-500/30 cursor-default' : 'cursor-pointer hover:bg-muted/50',
                    isOpen && 'bg-muted/50 ring-1 ring-violet-500/30',
                    isCurrent && status === 'running' && 'ring-1 ring-sky-500/40 shadow-lg shadow-sky-500/10',
                    status === 'completed' && 'shadow-lg shadow-emerald-500/5',
                    status === 'failed' && 'ring-1 ring-rose-500/20',
                  )} onClick={() => !justCompleted && toggle(key)}>
                    <div className="flex items-center gap-4 p-4">
                      <div className={cn('w-11 h-11 rounded-xl flex items-center justify-center shrink-0 transition-colors',
                        status === 'completed' ? 'bg-emerald-500/10 text-emerald-400' :
                        status === 'running' ? 'bg-sky-500/15 text-sky-400' :
                        status === 'failed' ? 'bg-rose-500/10 text-rose-400' : 'bg-muted text-muted-foreground')}>
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
                      {!justCompleted && <div className={cn('transition-transform duration-200', isOpen && 'rotate-180')}>
                        <ChevronDown className="w-4 h-4 text-muted-foreground" /></div>}
                    </div>
                    {task?.error_message && <div className="px-4 pb-3">
                      <div className="text-[11px] text-rose-400/80 bg-rose-500/5 rounded-lg px-3 py-2">{task.error_message.slice(0, 200)}</div>
                    </div>}
                  </Card>

                  {justCompleted && (
                    <div className="mt-2 p-4 rounded-xl border bg-emerald-500/5 border-emerald-500/20">
                      <div className="flex items-center gap-2 mb-3">
                        <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                        <span className="text-sm font-medium text-emerald-600 dark:text-emerald-400">{label}已生成，请确认结果</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button size="sm" className="gap-1 bg-emerald-600 hover:bg-emerald-500"
                          onClick={() => { onAdvance(); toggle(key) }}>
                          确认，继续 <ArrowRight className="w-3 h-3" />
                        </Button>
                        <Button size="sm" variant="outline" className="gap-1"
                          onClick={() => startStreaming(key, {})}>
                          <RefreshCw className="w-3 h-3" />重新生成
                        </Button>
                        <Button size="sm" variant="ghost" className="text-xs" onClick={() => toggle(key)}>查看详情</Button>
                      </div>
                    </div>
                  )}

                  {isOpen && !justCompleted && <div className="mt-2 ml-2 space-y-2 animate-in fade-in slide-in-from-top-2 duration-200">
                    {stageFiles.length > 0 && <StageArtifacts fileType={fileType} files={stageFiles} onFilesChange={onFilesChange} />}
                    <Card className="border-0 rounded-xl bg-muted/20">
                      <CardContent className="p-4">
                        <ParameterPanel stage={key} onGenerate={(params) => onGenerate(key, params)} canGenerate={true} canAdvance={false} />
                        <div className="flex gap-2 mt-3">
                          <Button size="sm" variant="outline" className="text-xs border-border text-foreground/70 hover:bg-muted/50"
                            onClick={(e) => { e.stopPropagation(); startStreaming(key, {}) }}
                            disabled={status === 'running' || isStreaming}>
                            {status === 'running' ? <><Loader2 className="w-3 h-3 mr-1 animate-spin" />生成中</> :
                             <><Play className="w-3 h-3 mr-1" />{task ? '重新生成' : '开始生成'}</>}
                          </Button>
                          {status === 'completed' && isCurrent && (
                            <Button size="sm" className="text-xs gap-1" onClick={(e) => { e.stopPropagation(); onAdvance() }}>
                              确认继续 <ArrowRight className="w-3 h-3" /></Button>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  </div>}
                </div>
              </div>
            })}
          </div>
          <div className="h-16" />
        </div>
      </ScrollArea>
      <GenerationPanel visible={panelOpen} events={events} isStreaming={isStreaming} error={error}
        onClose={handlePanelClose} onStop={stopStream}
        onRestart={() => streamingStage && startStreaming(streamingStage)} />
    </div>
  )
}

function MiniPreview({ fileType, file }: { fileType: string; file: FileRecord }) {
  const src = file.oss_url || `${API_BASE}/files/${file.id}/download`
  if (fileType === 'image') return <div className="w-12 h-12 rounded-lg overflow-hidden bg-muted shrink-0 ring-1 ring-border">
    <img src={src} alt="" className="w-full h-full object-cover" loading="lazy" /></div>
  if (fileType === 'video') return <div className="w-12 h-12 rounded-lg overflow-hidden bg-muted shrink-0 ring-1 ring-border flex items-center justify-center">
    <Film className="w-5 h-5 text-muted-foreground" /></div>
  if (fileType === 'audio') return <div className="shrink-0">
    <audio controls src={src} className="h-7 w-32" preload="metadata" /></div>
  return null
}
