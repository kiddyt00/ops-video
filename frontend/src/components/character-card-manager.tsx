'use client'

import { useState } from 'react'
import {
  Plus, Pencil, Trash2, Loader2, AlertCircle, X, User
} from 'lucide-react'
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
  front_image_url: string
  side_image_url: string
  back_image_url: string
}

const emptyForm: CardFormState = {
  name: '',
  description: '',
  front_image_url: '',
  side_image_url: '',
  back_image_url: '',
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
          front_image_url: card.front_image_url,
          side_image_url: card.side_image_url,
          back_image_url: card.back_image_url,
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
            front_image_url: card.front_image_url,
            side_image_url: card.side_image_url,
            back_image_url: card.back_image_url,
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
    if (!form.front_image_url.trim()) errs.front_image_url = '正面图 URL 不能为空'
    if (!form.side_image_url.trim()) errs.side_image_url = '侧面图 URL 不能为空'
    if (!form.back_image_url.trim()) errs.back_image_url = '背面图 URL 不能为空'
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
        if (form.front_image_url !== card!.front_image_url) update.front_image_url = form.front_image_url
        if (form.side_image_url !== card!.side_image_url) update.side_image_url = form.side_image_url
        if (form.back_image_url !== card!.back_image_url) update.back_image_url = form.back_image_url
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

              {(['front_image_url', 'side_image_url', 'back_image_url'] as const).map(
                (key) => {
                  const labelMap = {
                    front_image_url: '正面图',
                    side_image_url: '侧面图',
                    back_image_url: '背面图',
                  }
                  return (
                    <div key={key}>
                      <label className="text-xs text-muted-foreground mb-1 block">
                        {labelMap[key]} <span className="text-destructive">*</span>
                      </label>
                      <Input
                        value={form[key]}
                        onChange={e => setField(key, e.target.value)}
                        placeholder={`https://example.com/${key.replace('_image_url', '')}.png`}
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
/* Main manager component                                             */
/* ------------------------------------------------------------------ */

export function CharacterCardManager({ projectId, className }: CharacterCardManagerProps) {
  const { data: cards, isLoading, error } = useCharacterCards(projectId)
  const [createOpen, setCreateOpen] = useState(false)
  const [editCard, setEditCard] = useState<CharacterCard | null>(null)
  const [deleteCard, setDeleteCard] = useState<CharacterCard | null>(null)

  return (
    <div className={cn('flex flex-col h-full', className)}>
      {/* Header */}
      <div className="p-3 border-b border-border flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <User className="w-4 h-4 text-muted-foreground" />
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
            角色卡
          </h3>
          {cards && (
            <Badge variant="outline" className="text-xs">{cards.length}</Badge>
          )}
        </div>
        <Button size="sm" variant="outline" onClick={() => setCreateOpen(true)}>
          <Plus className="w-3.5 h-3.5 mr-1" />
          新建
        </Button>
      </div>

      {/* Content */}
      <ScrollArea className="flex-1">
        <div className="p-3">
          {isLoading && (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
            </div>
          )}

          {error && (
            <div className="flex items-start gap-2 text-xs text-destructive bg-destructive/10 rounded-md p-3">
              <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
              <span>{error instanceof Error ? error.message : '加载失败'}</span>
            </div>
          )}

          {!isLoading && !error && cards?.length === 0 && (
            <div className="text-center py-8">
              <User className="w-8 h-8 text-muted-foreground/40 mx-auto mb-2" />
              <p className="text-sm text-muted-foreground">暂无角色卡</p>
              <p className="text-xs text-muted-foreground mt-1">点击「新建」添加第一个角色卡</p>
            </div>
          )}

          {cards && cards.length > 0 && (
            <div className="space-y-3">
              {cards.map(card => (
                <Card key={card.id} className="overflow-hidden group">
                  <CardHeader className="pb-2">
                    <div className="flex items-start justify-between">
                      <div className="min-w-0 flex-1">
                        <CardTitle className="text-sm truncate">{card.name}</CardTitle>
                        {card.description && (
                          <CardDescription className="mt-0.5 line-clamp-2">
                            {card.description}
                          </CardDescription>
                        )}
                      </div>
                      <div className="flex items-center gap-1 shrink-0 ml-2 opacity-0 group-hover:opacity-100 transition-opacity">
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
                        { label: '正面', url: card.front_image_url },
                        { label: '侧面', url: card.side_image_url },
                        { label: '背面', url: card.back_image_url },
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
