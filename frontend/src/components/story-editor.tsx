'use client'

import { useState, useEffect } from 'react'
import { StoryWizard } from './story-wizard'
import {
  BookOpen, Sparkles, Loader2, AlertCircle, Save, Pencil, RotateCcw,
  ChevronDown, ChevronUp, Clock, FileText, Globe, MapPin, Users, ScrollText,
} from 'lucide-react'

const API_BASE_SE = process.env.NEXT_PUBLIC_API_URL || '/api/v1'
import {
  Card, CardContent, CardHeader, CardTitle, CardDescription,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { cn } from '@/lib/utils'
import {
  useStory,
  useUpdateStory,
  useGenerateInspiration,
  useGenerateStory,
  useGenerateChapterOutline,
  useGenerateChapterBody,
} from '@/hooks/use-stories'
import { useChapters } from '@/hooks/use-chapters'
import type { Story, ChapterOutlineItem } from '@/types/story'

/* ------------------------------------------------------------------ */
/* Props                                                                */
/* ------------------------------------------------------------------ */

interface StoryEditorProps {
  projectId: string
  className?: string
}

/* ------------------------------------------------------------------ */
/* Duration formatter                                                   */
/* ------------------------------------------------------------------ */

function formatDuration(seconds: number): string {
  if (!seconds || isNaN(seconds) || seconds <= 0) return '--'
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  if (m === 0) return `${s}秒`
  if (s === 0) return `${m}分钟`
  return `${m}分${s}秒`
}

/* ------------------------------------------------------------------ */
/* Collapsible Section                                                  */
/* ------------------------------------------------------------------ */

function CollapsibleSection({
  title,
  icon,
  children,
  defaultOpen = true,
  badge,
}: {
  title: string
  icon?: React.ReactNode
  children: React.ReactNode
  defaultOpen?: boolean
  badge?: React.ReactNode
}) {
  const [open, setOpen] = useState(defaultOpen)

  return (
    <div className="border border-border rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between p-3 hover:bg-muted/50 transition-colors text-left"
      >
        <div className="flex items-center gap-2">
          {icon}
          <span className="text-sm font-medium">{title}</span>
          {badge}
        </div>
        {open ? (
          <ChevronUp className="w-4 h-4 text-muted-foreground" />
        ) : (
          <ChevronDown className="w-4 h-4 text-muted-foreground" />
        )}
      </button>
      {open && (
        <div className="px-3 pb-3">
          {children}
        </div>
      )}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Editable Text Field                                                  */
/* ------------------------------------------------------------------ */

function EditableField({
  label,
  value,
  onChange,
  placeholder,
  multiline = true,
  rows = 4,
}: {
  label: string
  value: string
  onChange: (v: string) => void
  placeholder?: string
  multiline?: boolean
  rows?: number
}) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(value)

  useEffect(() => {
    setDraft(value)
  }, [value])

  const handleSave = () => {
    onChange(draft)
    setEditing(false)
  }

  const handleCancel = () => {
    setDraft(value)
    setEditing(false)
  }

  if (!editing && !value) {
    return (
      <div
        className="flex items-center justify-between p-2 rounded border border-dashed border-border cursor-pointer hover:border-violet-500/50 transition-colors"
        onClick={() => setEditing(true)}
      >
        <span className="text-xs text-muted-foreground">{label} — 点击添加</span>
        <Pencil className="w-3 h-3 text-muted-foreground" />
      </div>
    )
  }

  if (!editing) {
    return (
      <div
        className="p-2 rounded cursor-pointer hover:bg-muted/50 transition-colors group"
        onClick={() => setEditing(true)}
      >
        <div className="text-xs text-muted-foreground mb-1">{label}</div>
        <div className="text-sm whitespace-pre-wrap">{value || <span className="text-muted-foreground italic">未设置</span>}</div>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <div className="text-xs text-muted-foreground">{label}</div>
      {multiline ? (
        <Textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder={placeholder}
          rows={rows}
          className="text-sm"
        />
      ) : (
        <Input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder={placeholder}
          className="text-sm"
        />
      )}
      <div className="flex justify-end gap-2">
        <Button variant="ghost" size="sm" onClick={handleCancel}>
          取消
        </Button>
        <Button size="sm" onClick={handleSave}>
          <Save className="w-3 h-3 mr-1" />
          保存
        </Button>
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Chapter Outline Editor                                               */
/* ------------------------------------------------------------------ */

function ChapterOutlineEditor({
  chapters,
  onChange,
}: {
  chapters: ChapterOutlineItem[]
  onChange: (chapters: ChapterOutlineItem[]) => void
}) {
  const [editingIndex, setEditingIndex] = useState<number | null>(null)
  const [draft, setDraft] = useState<ChapterOutlineItem | null>(null)

  const startEdit = (idx: number) => {
    setEditingIndex(idx)
    setDraft({ ...chapters[idx] })
  }

  const cancelEdit = () => {
    setEditingIndex(null)
    setDraft(null)
  }

  const saveEdit = () => {
    if (editingIndex === null || !draft) return
    const updated = [...chapters]
    updated[editingIndex] = draft
    onChange(updated)
    setEditingIndex(null)
    setDraft(null)
  }

  if (chapters.length === 0) {
    return (
      <div className="text-center py-6">
        <FileText className="w-8 h-8 text-muted-foreground/40 mx-auto mb-2" />
        <p className="text-sm text-muted-foreground">暂无章节大纲</p>
        <p className="text-xs text-muted-foreground mt-1">使用 AI 生成或手动添加</p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {chapters.map((ch, idx) => (
        <div key={idx} className="border border-border rounded-lg overflow-hidden">
          {editingIndex === idx && draft ? (
            <div className="p-3 space-y-2">
              <Input
                value={draft.title}
                onChange={(e) => setDraft({ ...draft, title: e.target.value })}
                placeholder="章节标题"
                className="text-sm"
              />
              <Textarea
                value={draft.summary}
                onChange={(e) => setDraft({ ...draft, summary: e.target.value })}
                placeholder="章节摘要"
                rows={2}
                className="text-sm"
              />
              <div className="flex items-center gap-2">
                <Clock className="w-3 h-3 text-muted-foreground" />
                <Input
                  type="number"
                  value={draft.estimated_duration}
                  onChange={(e) => setDraft({ ...draft, estimated_duration: parseInt(e.target.value) || 0 })}
                  className="w-24 text-sm"
                  min={0}
                />
                <span className="text-xs text-muted-foreground">{formatDuration(draft.estimated_duration)}</span>
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="ghost" size="sm" onClick={cancelEdit}>取消</Button>
                <Button size="sm" onClick={saveEdit}>
                  <Save className="w-3 h-3 mr-1" />
                  保存
                </Button>
              </div>
            </div>
          ) : (
            <div
              className="p-3 cursor-pointer hover:bg-muted/50 transition-colors group"
              onClick={() => startEdit(idx)}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <Badge variant="outline" className="text-[10px]">
                      第 {ch.chapter_number} 章
                    </Badge>
                    <span className="text-sm font-medium truncate">{ch.title}</span>
                  </div>
                  {ch.summary && (
                    <p className="text-xs text-muted-foreground line-clamp-2">{ch.summary}</p>
                  )}
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-[10px] text-muted-foreground flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {formatDuration(ch.estimated_duration)}
                  </span>
                  <Pencil className="w-3 h-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Structured worldbuilding display                                    */
/* ------------------------------------------------------------------ */

function WorldbuildingDisplay({ data, onChange }: { data: any; onChange?: (v: string) => void }) {
  const [editing, setEditing] = useState(false)
  const [editText, setEditText] = useState('')

  const startEdit = () => {
    setEditText(typeof data === 'object' ? JSON.stringify(data, null, 2) : String(data ?? ''))
    setEditing(true)
  }

  const handleSave = () => {
    try {
      JSON.parse(editText) // validate JSON
      onChange?.(editText)
      setEditing(false)
    } catch {
      // keep editing, JSON invalid
    }
  }

  if (editing) {
    return (
      <div className="space-y-2">
        <Textarea value={editText} onChange={(e) => setEditText(e.target.value)} rows={8} className="text-sm font-mono" />
        <div className="flex gap-2">
          <Button size="sm" onClick={handleSave}>保存</Button>
          <Button size="sm" variant="outline" onClick={() => setEditing(false)}>取消</Button>
        </div>
      </div>
    )
  }

  if (!data) return (
    <div className="text-center py-4">
      <p className="text-xs text-muted-foreground mb-2">暂无世界观设定</p>
      <Button size="sm" variant="outline" onClick={startEdit}>手动添加</Button>
    </div>
  )
  if (typeof data === 'string') {
    try { data = JSON.parse(data) } catch { return <pre className="text-sm text-muted-foreground whitespace-pre-wrap bg-black/20 rounded-lg p-3">{data}</pre> }
  }
  if (typeof data !== 'object' || data === null) return null
  const wb = data as Record<string, string>
  const items = [
    { key: 'setting', icon: Globe, label: '世界背景', value: wb.setting },
    { key: 'time_period', icon: Clock, label: '时代设定', value: wb.time_period },
    { key: 'rules', icon: ScrollText, label: '世界规则', value: wb.rules },
  ].filter(i => i.value)
  if (!items.length) return <p className="text-xs text-muted-foreground py-4 text-center">暂无世界观设定</p>
  return (
    <div className="grid grid-cols-1 gap-2">
      {items.map(({ key, icon: Icon, label, value }) => (
        <div key={key} className="flex items-start gap-3 p-3 rounded-lg bg-muted/30 ring-1 ring-border/50">
          <Icon className="w-4 h-4 text-violet-400 mt-0.5 shrink-0" />
          <div className="min-w-0">
            <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">{label}</p>
            <p className="text-sm text-muted-foreground leading-relaxed">{value}</p>
          </div>
        </div>
      ))}
      <div className="flex justify-end mt-2">
        <Button variant="ghost" size="sm" className="text-xs gap-1" onClick={startEdit}>
          <Pencil className="w-3 h-3" />编辑
        </Button>
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Structured characters display                                       */
/* ------------------------------------------------------------------ */

function CharactersDisplay({ data, onChange, projectId }: { data: any; onChange?: (v: string) => void; projectId: string }) {
  const [editing, setEditing] = useState(false)
  const [editText, setEditText] = useState('')
  // Fetch CharacterCards for three-view data
  const [charCards, setCharCards] = useState<Record<string, any>>({})
  useEffect(() => {
    if (!projectId) return
    const token = localStorage.getItem('ops-video-tokens')
    const accessToken = token ? JSON.parse(token).access_token : null
    const headers: Record<string, string> = {}
    if (accessToken) headers['Authorization'] = `Bearer ${accessToken}`
    fetch(`${API_BASE_SE}/projects/${projectId}/character-cards`, { headers })
      .then(r => r.json())
      .then(cards => {
        const byName: Record<string, any> = {}
        cards.forEach((c: any) => { byName[c.name] = c })
        setCharCards(byName)
      })
      .catch(() => {})
  }, [projectId])

  const startEdit = () => {
    setEditText(typeof data === 'object' ? JSON.stringify(data, null, 2) : String(data ?? ''))
    setEditing(true)
  }

  const handleSave = () => {
    try {
      JSON.parse(editText)
      onChange?.(editText)
      setEditing(false)
    } catch {
      // invalid JSON, stay in edit mode
    }
  }

  if (editing) {
    return (
      <div className="space-y-2">
        <Textarea value={editText} onChange={(e) => setEditText(e.target.value)} rows={10} className="text-sm font-mono" />
        <div className="flex gap-2">
          <Button size="sm" onClick={handleSave}>保存</Button>
          <Button size="sm" variant="outline" onClick={() => setEditing(false)}>取消</Button>
        </div>
      </div>
    )
  }

  if (!data) return (
    <div className="text-center py-4">
      <p className="text-xs text-muted-foreground mb-2">暂无角色设定</p>
      <Button size="sm" variant="outline" onClick={startEdit}>手动添加</Button>
    </div>
  )
  if (typeof data === 'string') {
    try { data = JSON.parse(data) } catch { return <pre className="text-sm text-muted-foreground whitespace-pre-wrap bg-black/20 rounded-lg p-3">{data}</pre> }
  }
  if (!Array.isArray(data) || data.length === 0)
    return <p className="text-xs text-muted-foreground py-4 text-center">暂无角色设定</p>
  return (
    <div className="space-y-2">
      {data.map((char: Record<string, unknown>, idx: number) => {
        const cname = String(char.name || '')
        const card = charCards[cname]
        const hasImgs = card?.front_view_url && card?.side_view_url && card?.back_view_url
        return (
        <div key={idx} className="p-3 rounded-lg bg-muted/30 ring-1 ring-border/50 space-y-2">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 min-w-0">
              <div className="w-8 h-8 rounded-full bg-violet-500/10 flex items-center justify-center shrink-0">
                <Users className="w-4 h-4 text-violet-400" />
              </div>
              <div className="min-w-0">
                <p className="text-sm font-medium text-white/90">{cname}</p>
                {Boolean(char.role) && (
                  <Badge variant="outline" className="text-[10px] px-1.5 py-0 mt-0.5">{String(char.role)}</Badge>
                )}
              </div>
            </div>
            <CharacterThreeViewInline card={card} projectId={projectId} />
          </div>
          {Boolean(char.description) && (
            <p className="text-xs text-muted-foreground leading-relaxed pl-10">{String(char.description)}</p>
          )}
          {Boolean(char.arc) && (
            <p className="text-[11px] text-amber-400/80 italic pl-10">弧光: {String(char.arc)}</p>
          )}
          {/* Inline three-view image strip */}
          {(card?.front_view_url || card?.side_view_url || card?.back_view_url) && (
            <div className="grid grid-cols-3 gap-1.5 pl-10 mt-1">
              {[
                { label: '正面', url: card.front_view_url },
                { label: '侧面', url: card.side_view_url },
                { label: '背面', url: card.back_view_url },
              ].map(({ label, url }) => (
                <div key={label} className="space-y-0.5">
                  <span className="text-[9px] text-muted-foreground">{label}</span>
                  <div className="aspect-[3/4] bg-muted/50 rounded overflow-hidden">
                    {url ? (
                      <img src={url} alt={label} className="w-full h-full object-cover" loading="lazy"
                        onError={e => { (e.target as HTMLImageElement).style.display = 'none' }} />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-muted-foreground/20 text-[10px]">—</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )})}
      <div className="flex justify-end mt-2">
        <Button variant="ghost" size="sm" className="text-xs gap-1" onClick={startEdit}>
          <Pencil className="w-3 h-3" />编辑
        </Button>
      </div>
    </div>
  )
}

/** Inline three-view generate button with progress bar, shown in character rows */
function CharacterThreeViewInline({ card, projectId }: { card: any; projectId: string }) {
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [stageLabel, setStageLabel] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [doneUrls, setDoneUrls] = useState<Record<string,string>>({})

  const hasImages = card?.front_view_url || card?.side_view_url || card?.back_view_url || doneUrls.front_view_url

  const handleGen = async () => {
    if (!card?.id) return
    setLoading(true)
    setProgress(10)
    setStageLabel('生成中...')
    setError(null)
    try {
      const token = localStorage.getItem('ops-video-tokens')
      const accessToken = token ? JSON.parse(token).access_token : null
      const headers: Record<string, string> = { 'Content-Type': 'application/json' }
      if (accessToken) headers['Authorization'] = `Bearer ${accessToken}`

      const stages = [
        { pct: 25, label: '正在生成角色描述...', ms: 2000 },
        { pct: 45, label: '正在生成正面视图...', ms: 15000 },
        { pct: 65, label: '正在生成侧面视图...', ms: 15000 },
        { pct: 85, label: '正在生成背面视图...', ms: 15000 },
        { pct: 95, label: '正在上传OSS...', ms: 3000 },
      ]
      let stageIdx = 0
      const timer = setInterval(() => {
        stageIdx = Math.min(stageIdx + 1, stages.length - 1)
        setProgress(stages[stageIdx].pct)
        setStageLabel(stages[stageIdx].label)
      }, stages[0].ms)

      const resp = await fetch(
        `${API_BASE_SE}/projects/${projectId}/character-cards/${card.id}/three-view`,
        { method: 'POST', headers, body: '{}' }
      )
      clearInterval(timer)
      if (!resp.ok) throw new Error((await resp.json()).detail || '生成失败')
      const result = await resp.json()
      if (result.front_view_url) doneUrls.front_view_url = result.front_view_url
      if (result.side_view_url) doneUrls.side_view_url = result.side_view_url
      if (result.back_view_url) doneUrls.back_view_url = result.back_view_url
      setDoneUrls({...doneUrls})
      setProgress(100)
      setStageLabel('生成完成')
    } catch (e) {
      setError(e instanceof Error ? e.message : '生成失败')
      setStageLabel('生成失败')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col items-end gap-1 shrink-0">
        <Button size="sm" className="text-xs gap-1" disabled>
          <Loader2 className="w-3 h-3 animate-spin" />
          生成中
        </Button>
        <div className="w-24 bg-muted rounded-full h-1 overflow-hidden">
          <div className="h-full bg-gradient-to-r from-violet-500 to-cyan-500 rounded-full transition-all duration-700 ease-out" style={{width:`${progress}%`}} />
        </div>
        <span className="text-[8px] text-muted-foreground">{stageLabel}</span>
      </div>
    )
  }

  return (
    <div className="flex flex-col items-end gap-1 shrink-0">
      <Button
        variant={!!hasImages ? 'outline' : 'default'}
        size="sm"
        className="text-xs gap-1"
        onClick={handleGen}
        disabled={!card?.id}
      >
        <Sparkles className="w-3 h-3" />
        {hasImages ? '重新生成' : '生成三视图'}
      </Button>
      {error && <p className="text-[9px] text-destructive">{error}</p>}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Main Story Editor                                                    */
/* ------------------------------------------------------------------ */

export function StoryEditor({ projectId, className }: StoryEditorProps) {
  const { data: story, isLoading, error, refetch } = useStory(projectId)
  const updateMutation = useUpdateStory(projectId)
  const inspirationMutation = useGenerateInspiration(projectId)
  const generateStoryMutation = useGenerateStory(projectId)
  const generateOutlineMutation = useGenerateChapterOutline(projectId)
  const generateBodyMutation = useGenerateChapterBody(projectId)
  const { data: chapters } = useChapters(projectId)

  const [inspiration, setInspiration] = useState('')
  const [apiError, setApiError] = useState<string | null>(null)

  // Local edit buffer for batch save
  const [draft, setDraft] = useState<Story | null>(null)
  const [hasChanges, setHasChanges] = useState(false)

  useEffect(() => {
    if (story) {
      setDraft({ ...story })
      setHasChanges(false)
    }
  }, [story])

  const setField = (key: keyof Story, value: string | ChapterOutlineItem[]) => {
    setDraft(prev => {
      if (!prev) return prev
      return { ...prev, [key]: value }
    })
    setHasChanges(true)
  }

  const handleSave = async () => {
    if (!draft) return
    setApiError(null)
    try {
      await updateMutation.mutateAsync({
        logline: draft.logline,
        synopsis: draft.synopsis,
        worldbuilding: typeof draft.worldbuilding === 'string'
          ? (() => { try { return JSON.parse(draft.worldbuilding) } catch { return draft.worldbuilding } })()
          : draft.worldbuilding,
        characters: typeof draft.characters === 'string'
          ? (() => { try { return JSON.parse(draft.characters) } catch { return draft.characters } })()
          : draft.characters,
        chapter_outline: draft.chapter_outline,
      })
      setHasChanges(false)
    } catch (e) {
      setApiError(e instanceof Error ? e.message : '保存失败')
    }
  }

  const handleGenerateInspiration = async () => {
    if (!inspiration.trim()) return
    setApiError(null)
    try {
      await inspirationMutation.mutateAsync({ inspiration: inspiration.trim() })
      setInspiration('')
      await refetch()
    } catch (e) {
      setApiError(e instanceof Error ? e.message : '生成灵感失败')
    }
  }

  const handleGenerateStory = async () => {
    setApiError(null)
    try {
      await generateStoryMutation.mutateAsync()
      await refetch()
    } catch (e) {
      setApiError(e instanceof Error ? e.message : '生成故事失败')
    }
  }

  const handleGenerateOutline = async () => {
    setApiError(null)
    try {
      await generateOutlineMutation.mutateAsync()
      await refetch()
    } catch (e) {
      setApiError(e instanceof Error ? e.message : '生成大纲失败')
    }
  }

  const handleGenerateBody = async () => {
    setApiError(null)
    try {
      await generateBodyMutation.mutateAsync()
      await refetch()
    } catch (e) {
      setApiError(e instanceof Error ? e.message : '生成正文失败')
    }
  }

  const isGenerating = inspirationMutation.isPending || generateStoryMutation.isPending || generateOutlineMutation.isPending || generateBodyMutation.isPending
  const isSaving = updateMutation.isPending

  return (
    <div className={cn('flex flex-col h-full', className)}>
      {/* Header */}
      <div className="p-3 border-b border-border flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-muted-foreground" />
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
            故事
          </h3>
          {story && (
            <Badge variant="outline" className="text-xs">已创建</Badge>
          )}
        </div>
        {hasChanges && draft && (
          <Button size="sm" onClick={handleSave} disabled={isSaving}>
            {isSaving && <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />}
            <Save className="w-3.5 h-3.5 mr-1" />
            保存更改
          </Button>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-4 space-y-4">
          {/* API Error */}
          {apiError && (
            <div className="flex items-start gap-2 text-xs text-destructive bg-destructive/10 rounded-md p-3">
              <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
              <span>{apiError}</span>
            </div>
          )}

          {/* Loading */}
          {isLoading && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
            </div>
          )}

          {/* Query Error */}
          {error && !isLoading && (
            <div className="flex items-start gap-2 text-xs text-destructive bg-destructive/10 rounded-md p-3">
              <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
              <span>{error instanceof Error ? error.message : '加载失败'}</span>
            </div>
          )}

          {/* No story yet — Show interactive wizard */}
          {!isLoading && !story && !error && (
            <StoryWizard
              onComplete={async (wizardParams) => {
                setApiError(null)
                const apiParams: Record<string, string> = {
                  inspiration: wizardParams.inspiration,
                  genre: wizardParams.genre,
                  tone: wizardParams.tone,
                  target_length: wizardParams.target_length,
                }
                if (wizardParams.golden_finger) apiParams.golden_finger = wizardParams.golden_finger
                if (wizardParams.protagonist) apiParams.protagonist = wizardParams.protagonist
                if (wizardParams.relationship) apiParams.relationship = wizardParams.relationship
                if (wizardParams.worldbuilding_hints) apiParams.worldbuilding_hints = wizardParams.worldbuilding_hints

                try {
                  const token = localStorage.getItem('ops-video-tokens')
                  const accessToken = token ? JSON.parse(token).access_token : null
                  const resp = await fetch(
                    `${process.env.NEXT_PUBLIC_API_URL || '/api/v1'}/workflow/${projectId}/advance/inspiration`,
                    {
                      method: 'POST',
                      headers: {
                        'Content-Type': 'application/json',
                        ...(accessToken ? { 'Authorization': `Bearer ${accessToken}` } : {}),
                      },
                      body: JSON.stringify({ parameters: apiParams, execute: true }),
                    }
                  )
                  if (!resp.ok) {
                    const data = await resp.json()
                    throw new Error(data.detail || '生成故事失败')
                  }
                  await refetch()
                } catch (e) {
                  setApiError(e instanceof Error ? e.message : '生成故事失败')
                }
              }}
              isGenerating={inspirationMutation.isPending || generateStoryMutation.isPending}
            />
          )}

          {/* Story content */}
          {!isLoading && draft && (
            <div className="space-y-3">
              {/* AI Generation bar */}
              <Card className="border-dashed border-violet-500/30">
                <CardContent className="pt-4">
                  <div className="flex flex-wrap gap-2 items-center">
                    <Sparkles className="w-4 h-4 text-amber-500" />
                    <span className="text-xs text-muted-foreground">AI 辅助：</span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleGenerateInspiration}
                      disabled={!inspiration.trim() || isGenerating}
                    >
                      {generateStoryMutation.isPending && <Loader2 className="w-3 h-3 mr-1 animate-spin" />}
                      重新生成故事
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleGenerateOutline}
                      disabled={isGenerating}
                    >
                      {generateOutlineMutation.isPending && <Loader2 className="w-3 h-3 mr-1 animate-spin" />}
                      生成章节大纲
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleGenerateBody}
                      disabled={isGenerating || !(draft?.chapter_outline?.length)}
                    >
                      {generateBodyMutation.isPending && <Loader2 className="w-3 h-3 mr-1 animate-spin" />}
                      生成章节正文
                    </Button>
                    <Input
                      value={inspiration}
                      onChange={(e) => setInspiration(e.target.value)}
                      placeholder="输入灵感描述..."
                      className="text-xs h-8 w-48"
                    />
                  </div>
                </CardContent>
              </Card>

              {/* Logline */}
              <CollapsibleSection
                title="一句话简介"
                icon={<FileText className="w-4 h-4 text-muted-foreground" />}
              >
                <EditableField
                  label="Logline"
                  value={draft.logline}
                  onChange={(v) => setField('logline', v)}
                  placeholder="用一句话概括故事核心..."
                  multiline={false}
                />
              </CollapsibleSection>

              {/* Synopsis */}
              <CollapsibleSection
                title="故事概要"
                icon={<FileText className="w-4 h-4 text-muted-foreground" />}
              >
                <EditableField
                  label="Synopsis"
                  value={draft.synopsis}
                  onChange={(v) => setField('synopsis', v)}
                  placeholder="详细描述故事背景、主要情节和发展方向..."
                  rows={6}
                />
              </CollapsibleSection>

              {/* Worldbuilding */}
              <CollapsibleSection
                title="世界观"
                icon={<Globe className="w-4 h-4 text-muted-foreground" />}
                defaultOpen={false}
              >
                <WorldbuildingDisplay data={draft.worldbuilding} onChange={(v) => setField('worldbuilding', v)} />
              </CollapsibleSection>

              {/* Characters */}
              <CollapsibleSection
                title="角色设定"
                icon={<Users className="w-4 h-4 text-muted-foreground" />}
                defaultOpen={true}
                badge={draft?.characters?.length ? <span className="text-[10px] text-muted-foreground ml-1">{draft.characters.length}人</span> : undefined}
              >
                <CharactersDisplay data={draft.characters} onChange={(v) => setField('characters', v)} projectId={projectId} />
              </CollapsibleSection>

              <Separator />

              {/* Chapter Outline */}
              <CollapsibleSection
                title="章节大纲"
                icon={<FileText className="w-4 h-4 text-muted-foreground" />}
                badge={
                  (draft.chapter_outline?.length ?? 0) > 0 && (
                    <Badge variant="outline" className="text-[10px]">
                      {draft.chapter_outline!.length} 章
                    </Badge>
                  )
                }
              >
                <ChapterOutlineEditor
                  chapters={draft.chapter_outline ?? []}
                  onChange={(chapters) => setField('chapter_outline', chapters)}
                />
              </CollapsibleSection>

              {/* Chapter Body Preview */}
              {(chapters?.length ?? 0) > 0 && (
                <CollapsibleSection
                  title="章节正文"
                  icon={<ScrollText className="w-4 h-4 text-muted-foreground" />}
                  defaultOpen={false}
                  badge={
                    (chapters?.filter(c => c.body_text)?.length ?? 0) > 0 ? (
                      <Badge variant="outline" className="text-[10px]">
                        {chapters!.filter(c => c.body_text).length}/{chapters!.length} 章已生成
                      </Badge>
                    ) : undefined
                  }
                >
                  <div className="space-y-2">
                    {chapters?.map((ch) => (
                      <div key={ch.id} className="border border-border rounded-lg p-3">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge variant="outline" className="text-[10px]">
                            第 {ch.chapter_number} 章
                          </Badge>
                          <span className="text-xs font-medium">{ch.name}</span>
                          {ch.body_text ? (
                            <Badge variant="outline" className="text-[10px] bg-emerald-500/10 text-emerald-500 border-0 ml-auto">
                              已生成
                            </Badge>
                          ) : (
                            <Badge variant="outline" className="text-[10px] text-muted-foreground ml-auto">
                              待生成
                            </Badge>
                          )}
                        </div>
                        {ch.body_text ? (
                          <p className="text-xs text-muted-foreground line-clamp-3 leading-relaxed">
                            {ch.body_text.slice(0, 200)}
                            {ch.body_text.length > 200 ? '...' : ''}
                          </p>
                        ) : (
                          <p className="text-[11px] text-muted-foreground/50 italic">
                            点击上方「生成章节正文」按钮展开章节大纲为完整叙事
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </CollapsibleSection>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
