'use client'

import { useState } from 'react'
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

const VIEW_LABELS = [
  { key: 'front_view_url' as const, label: '正面', desc: 'Front' },
  { key: 'side_view_url' as const, label: '侧面', desc: 'Side' },
  { key: 'back_view_url' as const, label: '背面', desc: 'Back' },
]

export function ThreeViewCard({ card, projectId, onRefresh, className }: ThreeViewCardProps) {
  const [expanded, setExpanded] = useState(true)
  const generateMutation = useGenerateThreeView(projectId)

  const hasAllViews = card.front_view_url && card.side_view_url && card.back_view_url

  const handleGenerate = async () => {
    try {
      await generateMutation.mutateAsync({ cardId: card.id })
      onRefresh?.()
    } catch {
      // handled by mutation state
    }
  }

  return (
    <Card className={cn('overflow-hidden', className)}>
      <div className="p-3 space-y-3">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 min-w-0">
            <span className="text-sm font-medium truncate">{card.name}</span>
            {card.traits?.role && (
              <Badge variant="outline" className="text-[10px] shrink-0">
                {card.traits.role}
              </Badge>
            )}
          </div>
          <Button
            variant={hasAllViews ? 'outline' : 'default'}
            size="sm"
            className="text-xs gap-1 shrink-0 h-7"
            onClick={handleGenerate}
            disabled={generateMutation.isPending}
          >
            {generateMutation.isPending ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : hasAllViews ? (
              <RotateCcw className="w-3 h-3" />
            ) : (
              <Sparkles className="w-3 h-3" />
            )}
            {generateMutation.isPending ? '生成中...' : hasAllViews ? '重新生成' : '生成三视图'}
          </Button>
        </div>

        {/* Three-View Grid */}
        <div className="grid grid-cols-3 gap-2">
          {VIEW_LABELS.map(({ key, label, desc }) => {
            const url = card[key]
            return (
              <div key={key} className="space-y-1">
                <span className="text-[10px] text-muted-foreground block text-center">
                  {label}
                </span>
                <div className="aspect-[3/4] bg-muted rounded-md overflow-hidden relative group">
                  {url ? (
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
