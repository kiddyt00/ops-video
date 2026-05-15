'use client'

import React, { useState } from 'react'
import { Loader2, AlertCircle, Sparkles, RotateCcw, Eye } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { useGenerateThreeView } from '@/hooks/use-character-three-view'
import type { CharacterCard } from '@/types/character-card'

interface ThreeViewCardProps {
  card: CharacterCard
  projectId: string
  onRefresh?: () => void
  className?: string
}

type ViewKey = 'front_view_url' | 'side_view_url' | 'back_view_url'

const VIEW_LABELS: { key: ViewKey; label: string; desc: string }[] = [
  { key: 'front_view_url', label: '正面', desc: 'Front' },
  { key: 'side_view_url', label: '侧面', desc: 'Side' },
  { key: 'back_view_url', label: '背面', desc: 'Back' },
]

const PROGRESS_STAGES = [
  { label: '正在生成角色描述...', pct: 15, timeout: 2000 },
  { label: '正在生成正面视图...', pct: 35, timeout: 15000 },
  { label: '正在生成侧面视图...', pct: 55, timeout: 15000 },
  { label: '正在生成背面视图...', pct: 80, timeout: 15000 },
  { label: '正在上传OSS...',      pct: 95, timeout: 5000 },
]

export function ThreeViewCard({ card, projectId, onRefresh, className }: ThreeViewCardProps) {
  const [previewUrls, setPreviewUrls] = useState<Record<string, string>>({})
  const [versionHistory, setVersionHistory] = useState<Record<string, string[]>>({})
  const [progress, setProgress] = useState(0)
  const [stageLabel, setStageLabel] = useState('')
  const generateMutation = useGenerateThreeView(projectId)

  // Simulated progress during generation
  const [progressTimer, setProgressTimer] = useState<ReturnType<typeof setInterval> | null>(null)

  const displayUrl = (key: ViewKey): string => {
    if (previewUrls[key]) return previewUrls[key]
    return (card[key] as string) || ''
  }

  const hasAllViews = card.front_view_url && card.side_view_url && card.back_view_url

  // Start/stop progress simulation when mutation state changes
  React.useEffect(() => {
    if (generateMutation.isPending) {
      setProgress(0)
      setStageLabel('准备中...')
      let idx = 0
      const timer = setInterval(() => {
        idx = Math.min(idx + 1, PROGRESS_STAGES.length - 1)
        setProgress(PROGRESS_STAGES[idx].pct)
        setStageLabel(PROGRESS_STAGES[idx].label)
      }, PROGRESS_STAGES[0].timeout)
      setProgressTimer(timer)
      return () => clearInterval(timer)
    } else {
      if (progressTimer) clearInterval(progressTimer)
      if (hasAllViews) { setProgress(100); setStageLabel('生成完成') }
      else if (generateMutation.isError) setStageLabel('生成失败')
    }
  }, [generateMutation.isPending])

  const handleGenerate = async () => {
    try {
      setProgress(0)
      setStageLabel('准备中...')
      const result = await generateMutation.mutateAsync({ cardId: card.id })
      const urls: Record<string, string> = {}
      if (result.front_view_url) {
        urls.front_view_url = result.front_view_url
        setVersionHistory(prev => ({
          ...prev,
          front_view_url: [result.front_view_url!, ...(prev.front_view_url || [])],
        }))
      }
      if (result.side_view_url) {
        urls.side_view_url = result.side_view_url
        setVersionHistory(prev => ({
          ...prev,
          side_view_url: [result.side_view_url!, ...(prev.side_view_url || [])],
        }))
      }
      if (result.back_view_url) {
        urls.back_view_url = result.back_view_url
        setVersionHistory(prev => ({
          ...prev,
          back_view_url: [result.back_view_url!, ...(prev.back_view_url || [])],
        }))
      }
      setPreviewUrls(urls)
      setProgress(100)
      setStageLabel('生成完成')
      onRefresh?.()
    } catch {
      setStageLabel('生成失败')
    }
  }

  const status = generateMutation.isPending ? 'generating'
    : (hasAllViews || previewUrls.front_view_url) ? 'completed'
    : generateMutation.isError ? 'failed'
    : 'pending'

  return (
    <Card className={cn('overflow-hidden', className)}>
      <div className="p-3 space-y-3">
        {/* Header */}
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <span className="text-sm font-medium truncate">{card.name}</span>
            {card.traits?.role && (
              <Badge variant="outline" className="text-[10px] shrink-0">
                {card.traits.role}
              </Badge>
            )}
            {status === 'generating' && (
              <Badge variant="secondary" className="text-[10px] shrink-0 animate-pulse">生成中</Badge>
            )}
            {status === 'completed' && (
              <Badge variant="default" className="text-[10px] shrink-0 bg-emerald-500/20 text-emerald-400 border-emerald-500/30">已生成</Badge>
            )}
            {status === 'pending' && (
              <Badge variant="outline" className="text-[10px] shrink-0 text-muted-foreground">待生成</Badge>
            )}
          </div>
          <Button
            variant={status === 'completed' ? 'outline' : 'default'}
            size="default"
            className="text-xs gap-1.5 shrink-0"
            onClick={handleGenerate}
            disabled={generateMutation.isPending}
          >
            {generateMutation.isPending ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : status === 'completed' ? (
              <RotateCcw className="w-3.5 h-3.5" />
            ) : (
              <Sparkles className="w-3.5 h-3.5" />
            )}
            {generateMutation.isPending ? '生成中' : status === 'completed' ? '重新生成' : '生成三视图'}
          </Button>
        </div>

        {/* Progress bar during generation */}
        {generateMutation.isPending && (
          <div className="space-y-1">
            <div className="w-full bg-muted rounded-full h-1.5 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-violet-500 to-cyan-500 rounded-full transition-all duration-700 ease-out"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="text-[10px] text-muted-foreground text-right">{stageLabel} {progress}%</p>
          </div>
        )}

        {/* Three-View Grid */}
        <div className="grid grid-cols-3 gap-2">
          {VIEW_LABELS.map(({ key, label, desc }) => {
            const url = displayUrl(key)
            const history = versionHistory[key] || []
            return (
              <div key={key} className="space-y-1">
                <span className="text-[10px] text-muted-foreground block text-center">
                  {label}
                </span>
                <div className="aspect-[3/4] bg-muted rounded-md overflow-hidden relative group">
                  {generateMutation.isPending ? (
                    <div className="w-full h-full flex flex-col items-center justify-center bg-muted/50">
                      <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
                      <span className="text-[9px] text-muted-foreground mt-2">生成中</span>
                    </div>
                  ) : url ? (
                    <>
                      <img
                        src={url}
                        alt={`${card.name} - ${label}`}
                        className="w-full h-full object-cover"
                        loading="lazy"
                        onError={(e) => {
                          (e.target as HTMLImageElement).style.display = 'none'
                        }}
                      />
                      <button
                        className="absolute inset-0 bg-black/0 hover:bg-black/40 transition-colors flex items-center justify-center opacity-0 hover:opacity-100"
                        onClick={() => window.open(url, '_blank')}
                      >
                        <Eye className="w-5 h-5 text-white drop-shadow" />
                      </button>
                    </>
                  ) : (
                    <div className="w-full h-full flex flex-col items-center justify-center text-muted-foreground/30 gap-1">
                      <span className="text-[10px]">{desc}</span>
                      <span className="text-xs">—</span>
                    </div>
                  )}
                </div>
                {history.length > 0 && (
                  <p className="text-[9px] text-muted-foreground text-center">{history.length} 个版本</p>
                )}
              </div>
            )
          })}
        </div>

        {/* Description */}
        {card.description && (
          <p className="text-[11px] text-muted-foreground leading-relaxed line-clamp-2">
            {card.description}
          </p>
        )}

        {/* Error */}
        {generateMutation.isError && (
          <div className="flex items-start gap-1.5 text-[11px] text-destructive bg-destructive/10 rounded p-2">
            <AlertCircle className="w-3 h-3 shrink-0 mt-0.5" />
            <span>{generateMutation.error?.message || '生成失败'}</span>
          </div>
        )}
      </div>
    </Card>
  )
}
