'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  Plus, Trash2, Loader2, AlertCircle, Film, Clock,
  PlayCircle, ChevronRight,
} from 'lucide-react'
import {
  Card, CardContent, CardHeader,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import {
  Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { cn } from '@/lib/utils'
import {
  useChapters,
  useCreateChapter,
  useDeleteChapter,
} from '@/hooks/use-chapters'
import type { Chapter } from '@/types/chapter'

/* ------------------------------------------------------------------ */
/* Status helpers                                                       */
/* ------------------------------------------------------------------ */

const statusCfg: Record<string, { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline'; dot: string }> = {
  completed: { label: '已完成', variant: 'default', dot: 'bg-emerald-400' },
  running: { label: '生成中', variant: 'secondary', dot: 'bg-sky-400 animate-pulse' },
  failed: { label: '失败', variant: 'destructive', dot: 'bg-rose-400' },
  pending: { label: '待开始', variant: 'outline', dot: 'bg-zinc-500' },
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  if (diff < 60_000) return '刚刚'
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)} 分钟前`
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)} 小时前`
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

/* ------------------------------------------------------------------ */
/* Add Chapter Dialog                                                   */
/* ------------------------------------------------------------------ */

function AddChapterDialog({
  open,
  onOpenChange,
  projectId,
}: {
  open: boolean
  onOpenChange: (v: boolean) => void
  projectId: string
}) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [error, setError] = useState<string | null>(null)
  const createMutation = useCreateChapter(projectId)

  const handleSubmit = async () => {
    if (!name.trim()) {
      setError('名称不能为空')
      return
    }
    setError(null)
    try {
      await createMutation.mutateAsync({ name: name.trim(), description: description.trim() || null })
      setName('')
      setDescription('')
      onOpenChange(false)
    } catch (e) {
      setError(e instanceof Error ? e.message : '创建失败')
    }
  }

  const handleOpenChange = (v: boolean) => {
    if (!v) {
      setName('')
      setDescription('')
      setError(null)
    }
    onOpenChange(v)
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>新增章节</DialogTitle>
          <DialogDescription>创建一个新的章节，将自动进入生成流水线</DialogDescription>
        </DialogHeader>

        {error && (
          <div className="flex items-start gap-2 text-xs text-destructive bg-destructive/10 rounded p-2">
            <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <div className="space-y-3">
          <div>
            <label className="text-sm font-medium mb-1 block">
              名称 <span className="text-destructive">*</span>
            </label>
            <Input
              value={name}
              onChange={(e) => { setName(e.target.value); setError(null) }}
              placeholder="例如：第一章 - 初遇"
              onKeyDown={(e) => { if (e.key === 'Enter') handleSubmit() }}
            />
          </div>
          <div>
            <label className="text-sm font-medium mb-1 block">描述</label>
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="章节简介（可选）"
              rows={3}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => handleOpenChange(false)}>
            取消
          </Button>
          <Button onClick={handleSubmit} disabled={createMutation.isPending}>
            {createMutation.isPending && <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />}
            创建
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

/* ------------------------------------------------------------------ */
/* Delete confirmation dialog                                           */
/* ------------------------------------------------------------------ */

function DeleteConfirmDialog({
  open,
  onOpenChange,
  chapter,
  projectId,
}: {
  open: boolean
  onOpenChange: (v: boolean) => void
  chapter: Chapter | null
  projectId: string
}) {
  const deleteMutation = useDeleteChapter(projectId)
  const [error, setError] = useState<string | null>(null)

  const handleDelete = async () => {
    if (!chapter) return
    setError(null)
    try {
      await deleteMutation.mutateAsync({ chapterId: chapter.id })
      onOpenChange(false)
    } catch (e) {
      setError(e instanceof Error ? e.message : '删除失败')
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>确认删除</DialogTitle>
          <DialogDescription>
            确定要删除章节「{chapter?.name}」吗？此操作不可撤销。
          </DialogDescription>
        </DialogHeader>

        {error && (
          <div className="flex items-start gap-2 text-xs text-destructive bg-destructive/10 rounded p-2">
            <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button variant="destructive" onClick={handleDelete} disabled={deleteMutation.isPending}>
            {deleteMutation.isPending && <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />}
            删除
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

/* ------------------------------------------------------------------ */
/* Chapter Card                                                         */
/* ------------------------------------------------------------------ */

function ChapterCard({
  chapter,
  onDelete,
}: {
  chapter: Chapter
  onDelete: (c: Chapter) => void
}) {
  const router = useRouter()
  const cfg = statusCfg[chapter.status] ?? statusCfg.pending

  const handleClick = () => {
    router.push(`/projects/${chapter.project_id}/chapters/${chapter.id}`)
  }

  return (
    <Card
      className={cn(
        'group overflow-hidden cursor-pointer transition-all duration-200',
        'hover:ring-1 hover:ring-violet-500/30 hover:shadow-lg hover:shadow-violet-500/5',
        chapter.status === 'completed' && 'shadow-lg shadow-emerald-500/5',
        chapter.status === 'failed' && 'ring-1 ring-rose-500/20',
        chapter.status === 'running' && 'ring-1 ring-sky-500/40 shadow-lg shadow-sky-500/10',
      )}
      onClick={handleClick}
    >
      {/* Thumbnail */}
      <div className="relative aspect-video bg-muted overflow-hidden">
        {chapter.thumbnail_url ? (
          <img
            src={chapter.thumbnail_url}
            alt={chapter.name}
            className="w-full h-full object-cover transition-transform group-hover:scale-105"
            loading="lazy"
            onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-zinc-800 to-zinc-900">
            <Film className="w-10 h-10 text-zinc-600" />
          </div>
        )}

        {/* Overlay on hover */}
        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-center justify-center">
          <ChevronRight className="w-8 h-8 text-white opacity-0 group-hover:opacity-100 transition-all translate-x-1 group-hover:translate-x-0" />
        </div>

        {/* Status badge */}
        <div className="absolute top-2 left-2 flex items-center gap-1.5">
          <div className={cn('w-2 h-2 rounded-full', cfg.dot)} />
          <Badge variant={cfg.variant} className="text-[10px] px-1.5 py-0 bg-black/40 border-0 text-white">
            {cfg.label}
          </Badge>
        </div>

        {/* Chapter number */}
        <div className="absolute bottom-2 left-2 bg-black/60 text-white text-xs font-medium px-2 py-0.5 rounded">
          第 {chapter.chapter_number} 章
        </div>

        {/* Play icon for completed */}
        {chapter.status === 'completed' && (
          <div className="absolute bottom-2 right-2 bg-black/60 rounded-full p-1">
            <PlayCircle className="w-5 h-5 text-white" />
          </div>
        )}
      </div>

      {/* Info */}
      <CardHeader className="pb-1 pt-3 px-3">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <h3 className="text-sm font-semibold truncate">{chapter.name}</h3>
            {chapter.description && (
              <p className="text-xs text-muted-foreground mt-0.5 line-clamp-1">{chapter.description}</p>
            )}
          </div>
          <div
            className="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
            onClick={(e) => { e.stopPropagation(); onDelete(chapter) }}
          >
            <Button variant="ghost" size="icon" className="h-6 w-6" title="删除">
              <Trash2 className="w-3.5 h-3.5 text-destructive" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="px-3 pb-3 pt-0">
        <div className="flex items-center gap-1 text-xs text-muted-foreground">
          <Clock className="w-3 h-3" />
          <span>{formatDate(chapter.updated_at)}</span>
        </div>
      </CardContent>
    </Card>
  )
}

/* ------------------------------------------------------------------ */
/* Main Chapters List                                                   */
/* ------------------------------------------------------------------ */

interface ChaptersListProps {
  projectId: string
  className?: string
}

export function ChaptersList({ projectId, className }: ChaptersListProps) {
  const { data: chapters, isLoading, error } = useChapters(projectId)
  const [addOpen, setAddOpen] = useState(false)
  const [deleteChapter, setDeleteChapter] = useState<Chapter | null>(null)

  return (
    <div className={cn('flex flex-col h-full', className)}>
      {/* Header */}
      <div className="p-3 border-b border-border flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <Film className="w-4 h-4 text-muted-foreground" />
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
            章节
          </h3>
          {chapters && (
            <Badge variant="outline" className="text-xs">{chapters?.length ?? 0}</Badge>
          )}
        </div>
        <Button size="sm" variant="outline" onClick={() => setAddOpen(true)}>
          <Plus className="w-3.5 h-3.5 mr-1" />
          新增
        </Button>
      </div>

      {/* Content */}
      <ScrollArea className="flex-1">
        <div className="p-4">
          {isLoading && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
            </div>
          )}

          {error && (
            <div className="flex items-start gap-2 text-xs text-destructive bg-destructive/10 rounded-md p-3">
              <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
              <span>{error instanceof Error ? error.message : '加载失败'}</span>
            </div>
          )}

          {!isLoading && !error && chapters?.length === 0 && (
            <div className="text-center py-12">
              <Film className="w-12 h-12 text-muted-foreground/30 mx-auto mb-3" />
              <p className="text-sm text-muted-foreground">暂无章节</p>
              <p className="text-xs text-muted-foreground mt-1">点击「新增」创建第一个章节</p>
              <Button
                variant="outline"
                size="sm"
                className="mt-3"
                onClick={() => setAddOpen(true)}
              >
                <Plus className="w-3.5 h-3.5 mr-1" />
                新增章节
              </Button>
            </div>
          )}

          {chapters && chapters.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {chapters.map((chapter) => (
                <ChapterCard
                  key={chapter.id}
                  chapter={chapter}
                  onDelete={setDeleteChapter}
                />
              ))}
            </div>
          )}
        </div>
      </ScrollArea>

      <Separator />

      {/* Dialogs */}
      <AddChapterDialog
        open={addOpen}
        onOpenChange={setAddOpen}
        projectId={projectId}
      />
      <DeleteConfirmDialog
        open={!!deleteChapter}
        onOpenChange={(v) => { if (!v) setDeleteChapter(null) }}
        chapter={deleteChapter}
        projectId={projectId}
      />
    </div>
  )
}
