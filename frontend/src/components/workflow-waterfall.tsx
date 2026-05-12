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
import { type TaskStage, type Task } from '@/types/task'
import type { FileRecord } from '@/lib/api/files'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api/v1'

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
  pending: { label: '待开始', color: 'text-zinc-500', glow: '', dot: 'bg-zinc-600' },
  cancelled: { label: '已取消', color: 'text-zinc-500', glow: '', dot: 'bg-zinc-600' },
}

interface Props {
  projectId: string
  tasks?: Task[]
  files?: FileRecord[]
  workflowStatus?: { current_stage: string | null; stages: { stage: string; status: string }[] }
  onGenerate: (stage: TaskStage, params: Record<string, unknown>) => void
  onAdvance: () => void
  isLoading?: boolean
  onFilesChange?: () => void
  /** If set, show chapter context banner and pass to onGenerate */
  chapterId?: string
  chapterName?: string
}

export function WorkflowWaterfall({ projectId, tasks, files, workflowStatus, onGenerate, onAdvance, isLoading, onFilesChange, chapterId, chapterName }: Props) {
  const [expanded, setExpanded] = useState<TaskStage | null>(null)

  const stageMap = new Map(workflowStatus?.stages.map(s => [s.stage, s.status]) ?? [])
  const currentStage = workflowStatus?.current_stage as TaskStage | null

  const getStatus = (key: string): string => {
    const stageTasks = (tasks ?? []).filter(t => t.stage === key)
    // Prefer completed, then running, then any status, then pending
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
            <div key={i} className="h-24 rounded-2xl bg-white/5 animate-pulse" />
          ))}
        </div>
      </ScrollArea>
    )
  }

  return (
    <div className="h-full bg-gradient-to-b from-[#0a0a14] via-[#0d0d1a] to-[#0a0a14]">
      <ScrollArea className="h-full">
        <div className="p-6 max-w-3xl mx-auto space-y-0">
          <div className="text-center mb-8">
            <h2 className="text-lg font-semibold text-white/90 tracking-wide">生成流水线</h2>
            <p className="text-xs text-zinc-500 mt-1">点击阶段展开查看制品与参数</p>
            {chapterId && chapterName && (
              <div className="mt-3 inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-violet-500/10 border border-violet-500/20">
                <Film className="w-3.5 h-3.5 text-violet-400" />
                <span className="text-sm text-violet-300 font-medium">{chapterName}</span>
                <Badge variant="outline" className="text-[10px] px-1.5 py-0 bg-violet-500/10 text-violet-300 border-violet-500/20">
                  当前章节
                </Badge>
              </div>
            )}
          </div>

          <div className="relative">
            <div className="absolute left-8 top-0 bottom-0 w-px bg-gradient-to-b from-violet-500/30 via-sky-500/20 to-emerald-500/30" />

            {STAGES.map(({ key, label, desc, icon: Icon, fileType }, i) => {
              const status = getStatus(key)
              const cfg = statusCfg[status] ?? statusCfg.pending
              const isOpen = expanded === key
              const isCurrent = currentStage === key
              const stageFiles = getFiles(fileType)
              const stageTasks = (tasks ?? []).filter(t => t.stage === key)
              const task = stageTasks.find(t => t.status === 'completed') || stageTasks[0]
              const hasPreview = stageFiles.length > 0 && (fileType === 'image' || fileType === 'video' || fileType === 'audio')

              return (
                <div key={key} className="relative pb-2">
                  <div className="absolute left-8 top-8 -translate-x-1/2 z-10">
                    <div className={cn('w-3.5 h-3.5 rounded-full border-2 border-[#0a0a14] transition-colors', cfg.dot)} />
                  </div>

                  <div className="ml-14">
                    <Card
                      className={cn(
                        'border-0 rounded-2xl transition-all duration-300 cursor-pointer overflow-hidden',
                        'bg-white/[0.03] backdrop-blur-sm hover:bg-white/[0.06]',
                        isOpen && 'bg-white/[0.06] ring-1 ring-violet-500/30',
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
                          'bg-zinc-800 text-zinc-500',
                        )}>
                          {status === 'running' ? <Loader2 className="w-5 h-5 animate-spin" /> : <Icon className="w-5 h-5" />}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-semibold text-white/90">{label}</span>
                            <Badge variant="outline" className={cn('text-[10px] px-1.5 py-0 border-0', cfg.color, 'bg-white/5')}>
                              {cfg.label}
                            </Badge>
                          </div>
                          <p className="text-xs text-zinc-500 mt-0.5">{desc}</p>
                        </div>
                        {status === 'completed' && hasPreview && (
                          <MiniPreview fileType={fileType} file={stageFiles[0]} />
                        )}
                        <div className={cn('transition-transform duration-200', isOpen && 'rotate-180')}>
                          <ChevronDown className="w-4 h-4 text-zinc-600" />
                        </div>
                      </div>
                      {task?.error_message && (
                        <div className="px-4 pb-3">
                          <div className="text-[11px] text-rose-400/80 bg-rose-500/5 rounded-lg px-3 py-2">
                            {task.error_message.slice(0, 200)}
                          </div>
                        </div>
                      )}
                    </Card>

                    {isOpen && (
                      <div className="mt-2 ml-2 space-y-2 animate-in fade-in slide-in-from-top-2 duration-200">
                        {stageFiles.length > 0 && (
                          <StageArtifacts fileType={fileType} files={stageFiles} onFilesChange={onFilesChange} />
                        )}
                        <Card className="border-0 rounded-xl bg-white/[0.02]">
                          <CardContent className="p-4">
                            <ParameterPanel
                              stage={key}
                              onGenerate={(params) => onGenerate(key, params)}
                              canGenerate={true}
                              canAdvance={false}
                            />
                            <div className="flex gap-2 mt-3">
                              <Button
                                size="sm" variant="outline"
                                className="text-xs border-white/10 text-white/70 hover:bg-white/10"
                                onClick={(e) => { e.stopPropagation(); onGenerate(key, {}) }}
                                disabled={status === 'running'}
                              >
                                <Play className="w-3 h-3 mr-1" />
                                {task ? '重新生成' : '开始生成'}
                              </Button>
                              {status === 'completed' && isCurrent && (
                                <Button size="sm" className="text-xs" onClick={(e) => { e.stopPropagation(); onAdvance() }}>
                                  推进下一阶段
                                </Button>
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
      <Film className="w-5 h-5 text-zinc-500" />
    </div>
  }
  if (fileType === 'audio') {
    return <div className="shrink-0">
      <audio controls src={src} className="h-7 w-32 [&::-webkit-media-controls-panel]:bg-zinc-800" preload="metadata" />
    </div>
  }
  return null
}
