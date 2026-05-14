'use client'

import { useState } from 'react'
import { Sparkles, Loader2, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ThreeViewCard } from './three-view-card'
import { useSyncCharacterCards, useGenerateAllThreeViews } from '@/hooks/use-character-three-view'
import { useCharacterCards } from '@/hooks/use-character-cards'
import type { CharacterCard } from '@/types/character-card'

interface ThreeViewGalleryProps {
  projectId: string
  className?: string
}

export function ThreeViewGallery({ projectId, className }: ThreeViewGalleryProps) {
  const { data: cards, isLoading, refetch } = useCharacterCards(projectId)
  const syncMutation = useSyncCharacterCards(projectId)
  const batchGenMutation = useGenerateAllThreeViews(projectId)

  const handleSync = async () => {
    await syncMutation.mutateAsync()
    refetch()
  }

  const handleBatchGenerate = async () => {
    await batchGenMutation.mutateAsync({})
    refetch()
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className={className}>
      {/* Action bar */}
      <div className="flex items-center justify-between mb-4">
        <div className="text-xs text-muted-foreground">
          {cards ? `${cards.length} 个角色` : ''}
          {syncMutation.isPending && ' 同步中...'}
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            className="text-xs gap-1"
            onClick={handleSync}
            disabled={syncMutation.isPending}
          >
            {syncMutation.isPending ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : (
              <RefreshCw className="w-3 h-3" />
            )}
            从故事同步
          </Button>
          <Button
            size="sm"
            className="text-xs gap-1"
            onClick={handleBatchGenerate}
            disabled={batchGenMutation.isPending}
          >
            {batchGenMutation.isPending ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : (
              <Sparkles className="w-3 h-3" />
            )}
            {batchGenMutation.isPending ? '生成中...' : '批量生成三视图'}
          </Button>
        </div>
      </div>

      {/* Batch progress */}
      {batchGenMutation.data && (
        <div className="text-xs text-muted-foreground mb-3 p-2 rounded bg-muted/30">
          成功: {batchGenMutation.data.success}/{batchGenMutation.data.total}
          {batchGenMutation.data.failed > 0 && (
            <span className="text-destructive ml-2">失败: {batchGenMutation.data.failed}</span>
          )}
          {batchGenMutation.data.skipped > 0 && (
            <span className="text-muted-foreground ml-2">跳过: {batchGenMutation.data.skipped}</span>
          )}
        </div>
      )}

      {/* Cards grid */}
      {cards && cards.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {cards.map((card: CharacterCard) => (
            <ThreeViewCard
              key={card.id}
              card={card}
              projectId={projectId}
              onRefresh={refetch}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <p className="text-sm text-muted-foreground mb-3">暂无角色卡</p>
          <Button
            variant="outline"
            size="sm"
            onClick={handleSync}
            disabled={syncMutation.isPending}
          >
            {syncMutation.isPending && <Loader2 className="w-3 h-3 animate-spin mr-1" />}
            从故事同步角色
          </Button>
        </div>
      )}

      {/* Error */}
      {syncMutation.isError && (
        <div className="text-xs text-destructive mt-2">
          同步失败: {syncMutation.error?.message}
        </div>
      )}
      {batchGenMutation.isError && (
        <div className="text-xs text-destructive mt-2">
          批量生成失败: {batchGenMutation.error?.message}
        </div>
      )}
    </div>
  )
}
