'use client'

import { useState, useEffect } from 'react'
import {
  Plus, Pencil, Trash2, Loader2, AlertCircle, X, User, Eye
} from 'lucide-react'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
import {
  Card, CardContent, CardDescription, CardHeader, CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import {
  Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle,
} from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { cn } from '@/lib/utils'
import {
  useCharacterCards,
  useCreateCharacterCard,
  useUpdateCharacterCard,
  useDeleteCharacterCard,
} from '@/hooks/use-character-cards'
import { ThreeViewGallery } from './three-view-gallery'
import type { CharacterCard, CharacterCardCreate, CharacterCardUpdate } from '@/types/character-card'

interface CharacterCardManagerProps {
  projectId: string
  className?: string
}

/* ------------------------------------------------------------------ */
/* Form used for both create and edit                                 */
/* ------------------------------------------------------------------ */

interface CardFormState {
  name: string
  description: string
  front_view_url: string
  side_view_url: string
  back_view_url: string
}

const emptyForm: CardFormState = {
  name: '',
  description: '',
  front_view_url: '',
  side_view_url: '',
  back_view_url: '',
}

function CardFormDialog({
  open,
  onOpenChange,
  projectId,
  card,
}: {
  open: boolean
  onOpenChange: (v: boolean) => void
  projectId: string
  card?: CharacterCard
}) {
  const isEdit = !!card
  const [form, setForm] = useState<CardFormState>(
    card
      ? {
          name: card.name,
          description: card.description,
          front_view_url: card.front_view_url,
          side_view_url: card.side_view_url,
          back_view_url: card.back_view_url,
        }
      : { ...emptyForm }
  )
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [apiError, setApiError] = useState<string | null>(null)

  const createMutation = useCreateCharacterCard(projectId)
  const updateMutation = useUpdateCharacterCard(projectId, card?.id ?? '')

  const resetForm = () => {
    setForm(
      card
        ? {
            name: card.name,
            description: card.description,
            front_view_url: card.front_view_url,
            side_view_url: card.side_view_url,
            back_view_url: card.back_view_url,
          }
        : { ...emptyForm }
    )
    setErrors({})
    setApiError(null)
  }

  const handleOpenChange = (v: boolean) => {
    if (!v) resetForm()
    onOpenChange(v)
  }

  const setField = (key: keyof CardFormState, value: string) => {
    setForm(prev => ({ ...prev, [key]: value }))
    if (errors[key]) setErrors(prev => { const n = { ...prev }; delete n[key]; return n })
    if (apiError) setApiError(null)
  }

  const validate = (): boolean => {
    const errs: Record<string, string> = {}
    if (!form.name.trim()) errs.name = '名称不能为空'
    // 三视图 URL 可选（可通过 AI 自动生成）
    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  const handleSubmit = async () => {
    if (!validate()) return
    setApiError(null)
    try {
      if (isEdit) {
        const update: CharacterCardUpdate = {}
        if (form.name !== card!.name) update.name = form.name
        if (form.description !== card!.description) update.description = form.description
        if (form.front_view_url !== card!.front_view_url) update.front_view_url = form.front_view_url
        if (form.side_view_url !== card!.side_view_url) update.side_view_url = form.side_view_url
        if (form.back_view_url !== card!.back_view_url) update.back_view_url = form.back_view_url
        await updateMutation.mutateAsync(update)
      } else {
        await createMutation.mutateAsync(form as CharacterCardCreate)
      }
      onOpenChange(false)
    } catch (e) {
      setApiError(e instanceof Error ? e.message : '操作失败')
    }
  }

  const isPending = isEdit ? updateMutation.isPending : createMutation.isPending

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>{isEdit ? '编辑角色卡' : '新建角色卡'}</DialogTitle>
          <DialogDescription>
            {isEdit ? '修改角色卡信息' : '添加一个新的角色卡，包含三视图信息'}
          </DialogDescription>
        </DialogHeader>

        {apiError && (
          <div className="flex items-start gap-2 text-xs text-destructive bg-destructive/10 rounded p-2">
            <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
            <span>{apiError}</span>
          </div>
        )}

        <ScrollArea className="max-h-[60vh] pr-2">
          <div className="space-y-3">
            {/* Name */}
            <div>
              <label className="text-sm font-medium mb-1 block">
                名称 <span className="text-destructive">*</span>
              </label>
              <Input
                value={form.name}
                onChange={e => setField('name', e.target.value)}
                placeholder="角色名称"
                className={cn(errors.name && 'border-destructive')}
              />
              {errors.name && <p className="text-xs text-destructive mt-1">{errors.name}</p>}
            </div>

            {/* Description */}
            <div>
              <label className="text-sm font-medium mb-1 block">描述</label>
              <Textarea
                value={form.description}
                onChange={e => setField('description', e.target.value)}
                placeholder="角色描述、性格特征等"
                rows={3}
              />
            </div>

            <Separator />

            {/* Image URLs */}
            <div className="space-y-3">
              <label className="text-sm font-medium">三视图 URL</label>

              {(['front_view_url', 'side_view_url', 'back_view_url'] as const).map(
                (key) => {
                  const labelMap = {
                    front_view_url: '正面图',
                    side_view_url: '侧面图',
                    back_view_url: '背面图',
                  }
                  return (
                    <div key={key}>
                      <label className="text-xs text-muted-foreground mb-1 block">
                        {labelMap[key]}
                      </label>
                      <Input
                        value={form[key]}
                        onChange={e => setField(key, e.target.value)}
                        placeholder={`https://example.com/${key.replace('_view_url', '')}.png`}
                        className={cn(errors[key] && 'border-destructive')}
                      />
                      {errors[key] && (
                        <p className="text-xs text-destructive mt-1">{errors[key]}</p>
                      )}
                      {form[key] && (
                        <div className="mt-1.5 aspect-video bg-muted rounded overflow-hidden">
                          <img
                            src={form[key]}
                            alt={labelMap[key]}
                            className="w-full h-full object-contain"
                            onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
                          />
                        </div>
                      )}
                    </div>
                  )
                }
              )}
            </div>
          </div>
        </ScrollArea>

        <div className="flex justify-end gap-2 pt-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={handleSubmit} disabled={isPending}>
            {isPending && <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />}
            {isEdit ? '保存' : '创建'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

/* ------------------------------------------------------------------ */
/* Delete confirmation dialog                                         */
/* ------------------------------------------------------------------ */

function DeleteConfirmDialog({
  open,
  onOpenChange,
  card,
  projectId,
}: {
  open: boolean
  onOpenChange: (v: boolean) => void
  card: CharacterCard | null
  projectId: string
}) {
  const deleteMutation = useDeleteCharacterCard(projectId)
  const [error, setError] = useState<string | null>(null)

  const handleDelete = async () => {
    if (!card) return
    setError(null)
    try {
      await deleteMutation.mutateAsync({ cardId: card.id })
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
            确定要删除角色卡「{card?.name}」吗？此操作不可撤销。
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
          <Button
            variant="destructive"
            onClick={handleDelete}
            disabled={deleteMutation.isPending}
          >
            {deleteMutation.isPending && <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />}
            删除
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

/* ------------------------------------------------------------------ */
/* Character Context Preview                                          */
/* ------------------------------------------------------------------ */

function CharacterContextPreview({
  projectId,
  cards,
}: {
  projectId: string
  cards: CharacterCard[]
}) {
  const [show, setShow] = useState(false)
  const [context, setContext] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!show || context !== null) return
    setLoading(true)
    fetch(`${API_BASE}/projects/${projectId}/character-cards/context`)
      .then(r => r.json())
      .then(data => {
        setContext(data.context_template || '无角色设定')
      })
      .catch(() => setContext('获取角色上下文失败'))
      .finally(() => setLoading(false))
  }, [show, projectId, context])

  const activeCount = cards.filter(c => c.is_active !== false).length

  return (
    <div className="border-t px-3 py-2">
      <button
        onClick={() => { if (!show) setShow(true); else setShow(!show) }}
        className="flex items-center gap-2 w-full text-xs text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
      >
        <Eye className="w-3.5 h-3.5" />
        <span>角色一致性 — {activeCount} 个活跃角色</span>
        <span className="ml-auto text-[10px]">{show ? '收起' : '预览'}</span>
      </button>

      {show && (
        <div className="mt-2">
          {loading ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin text-muted-foreground" />
          ) : (
            <pre className="text-[11px] text-muted-foreground whitespace-pre-wrap font-mono bg-muted/50 rounded p-2 max-h-40 overflow-y-auto">
              {context}
            </pre>
          )}
        </div>
      )}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Main component                                                     */
/* ------------------------------------------------------------------ */

export function CharacterCardManager({ projectId, className }: CharacterCardManagerProps) {
  const { data: cards, isLoading, error } = useCharacterCards(projectId)
  const [createOpen, setCreateOpen] = useState(false)
  const [editCard, setEditCard] = useState<CharacterCard | null>(null)
  const [deleteCard, setDeleteCard] = useState<CharacterCard | null>(null)

  return (
    <div className={cn('flex flex-col h-full', className)}>
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b shrink-0">
        <div className="flex items-center gap-2">
          <User className="w-4 h-4 text-primary" />
          <span className="font-medium text-sm">角色卡</span>
          {cards && (
            <Badge variant="secondary" className="text-[10px] h-4 px-1.5">
              {cards.length}
            </Badge>
          )}
        </div>
        <Button variant="outline" size="sm" className="h-7 text-xs" onClick={() => setCreateOpen(true)}>
          <Plus className="w-3 h-3 mr-1" />
          新建
        </Button>
      </div>

      {/* Card list */}
      <ScrollArea className="flex-1">
        <div className="p-2 space-y-2">
          {isLoading && (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
            </div>
          )}

          {error && (
            <div className="flex items-start gap-2 text-xs text-destructive bg-destructive/10 rounded p-2 mx-1">
              <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
              <span>加载失败: {error.message}</span>
            </div>
          )}

          {!isLoading && !error && cards && cards.length === 0 && (
            <div className="text-center py-8 text-xs text-muted-foreground">
              暂无角色卡
            </div>
          )}

          {!isLoading && cards && cards.length > 0 && (
            <div className="space-y-2">
              {cards.map(card => (
                <Card key={card.id} className="overflow-hidden">
                  <CardHeader className="p-3 pb-0">
                    <div className="flex items-start justify-between">
                      <div className="min-w-0">
                        <CardTitle className="text-sm font-medium truncate">
                          {card.name}
                        </CardTitle>
                        {card.description && (
                          <CardDescription className="text-xs mt-0.5 line-clamp-2">
                            {card.description}
                          </CardDescription>
                        )}
                      </div>
                      <div className="flex items-center gap-0.5 shrink-0 ml-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7"
                          onClick={() => setEditCard(card)}
                          title="编辑"
                        >
                          <Pencil className="w-3.5 h-3.5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7"
                          onClick={() => setDeleteCard(card)}
                          title="删除"
                        >
                          <Trash2 className="w-3.5 h-3.5 text-destructive" />
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <div className="grid grid-cols-3 gap-1.5">
                      {[
                        { label: '正面', url: card.front_view_url },
                        { label: '侧面', url: card.side_view_url },
                        { label: '背面', url: card.back_view_url },
                      ].map(({ label, url }) => (
                        <div key={label} className="space-y-1">
                          <span className="text-[10px] text-muted-foreground">{label}</span>
                          <div className="aspect-square bg-muted rounded overflow-hidden">
                            {url ? (
                              <img
                                src={url}
                                alt={`${card.name} - ${label}`}
                                className="w-full h-full object-cover"
                                loading="lazy"
                                onError={(e) => {
                                  (e.target as HTMLImageElement).style.display = 'none'
                                }}
                              />
                            ) : (
                              <div className="w-full h-full flex items-center justify-center text-muted-foreground/30">
                                <X className="w-4 h-4" />
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Three-View Gallery */}
      <div className="border-t pt-4 mt-4">
        <h3 className="text-sm font-medium mb-3">角色三视图</h3>
        <ThreeViewGallery projectId={projectId} />
      </div>

      {/* Character Context Preview */}
      {cards && cards.length > 0 && (
        <CharacterContextPreview projectId={projectId} cards={cards} />
      )}

      {/* Dialogs */}
      <CardFormDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        projectId={projectId}
      />
      {editCard && (
        <CardFormDialog
          open={!!editCard}
          onOpenChange={(v) => { if (!v) setEditCard(null) }}
          projectId={projectId}
          card={editCard}
        />
      )}
      <DeleteConfirmDialog
        open={!!deleteCard}
        onOpenChange={(v) => { if (!v) setDeleteCard(null) }}
        card={deleteCard}
        projectId={projectId}
      />
    </div>
  )
}
