'use client'

import { useState } from 'react'
import {
  Brain, Paintbrush, Mic, Music, Clapperboard, Cpu,
  Plus, Pencil, Trash2, Play, Loader2, AlertCircle,
  Power, PowerOff, Images, Zap, ExternalLink, Check
} from 'lucide-react'
import { AppShell } from '@/components/app-shell'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { cn } from '@/lib/utils'

// ─── Types ────────────────────────────────────────────────────────────

interface AIModel {
  id: string; name: string; category: string; provider: string; model_name: string
  api_key: string | null; api_base_url: string | null
  is_enabled: boolean; is_builtin: boolean
}

interface ModelForm {
  name: string; category: string; provider: string; model_name: string
  api_key?: string; api_base_url?: string
}

const emptyForm: ModelForm = { name: '', category: 'llm', provider: '', model_name: '' }

// ─── Categories ───────────────────────────────────────────────────────

const CATS: readonly { key: string; label: string; desc: string; icon: typeof Brain; color: string }[] = [
  { key: 'llm',       label: '大语言模型',  desc: '剧本创作 / 分镜拆解',       icon: Brain,        color: '#818cf8' },
  { key: 'text2img',  label: '文生图',      desc: '文本 → 漫画图片',           icon: Paintbrush,   color: '#f59e0b' },
  { key: 'i2v',       label: '图生视频',    desc: '图片 → 动态视频',           icon: Images,       color: '#22d3ee' },
  { key: 'tts',       label: '文生音频',    desc: '文本 → 语音旁白',           icon: Mic,          color: '#34d399' },
  { key: 'bgm',       label: '音乐生成',    desc: '自动生成背景音乐',          icon: Music,        color: '#f472b6' },
  { key: 'video',     label: '视频合成',    desc: '图片+音频 → 成片',          icon: Clapperboard, color: '#a78bfa' },
]
const CAT_MAP = Object.fromEntries(CATS.map(c => [c.key, c]))

// ─── API ──────────────────────────────────────────────────────────────

const api_ = {
  list: () => api.get<AIModel[]>('/models').then(r => r.data),
  create: (d: ModelForm) => api.post<AIModel>('/models', d).then(r => r.data),
  update: (id: string, d: Partial<ModelForm>) => api.put<AIModel>(`/models/${id}`, d).then(r => r.data),
  del: (id: string) => api.delete(`/models/${id}`),
  toggle: (id: string) => api.post<AIModel>(`/models/${id}/toggle`).then(r => r.data),
  test: (id: string, p?: string) => api.post<{ success: boolean; message: string; latency_ms: number; result: string }>(
    `/models/${id}/test`, { prompt: p }).then(r => r.data),
}

// ─── Component ────────────────────────────────────────────────────────

export default function ModelsPage() {
  const qc = useQueryClient()
  const { data: models, isLoading } = useQuery({ queryKey: ['ai-models'], queryFn: api_.list })

  const [dialog, setDialog] = useState<{ open: boolean; id?: string }>({ open: false })
  const [form, setForm] = useState<ModelForm>(emptyForm)
  const [formErr, setFormErr] = useState('')
  const [tests, setTests] = useState<Record<string, { running: boolean; ok?: boolean; msg?: string; ms?: number }>>({})

  const createMut = useMutation({ mutationFn: api_.create, onSuccess: () => { qc.invalidateQueries({ queryKey: ['ai-models'] }); setDialog({ open: false }) } })
  const updateMut = useMutation({ mutationFn: ({ id, data }: { id: string; data: Partial<ModelForm> }) => api_.update(id, data), onSuccess: () => { qc.invalidateQueries({ queryKey: ['ai-models'] }); setDialog({ open: false }) } })
  const delMut = useMutation({ mutationFn: api_.del, onSuccess: () => qc.invalidateQueries({ queryKey: ['ai-models'] }) })
  const toggleMut = useMutation({ mutationFn: api_.toggle, onSuccess: () => qc.invalidateQueries({ queryKey: ['ai-models'] }) })

  const openNew = () => { setForm(emptyForm); setFormErr(''); setDialog({ open: true }) }
  const openEdit = (m: AIModel) => {
    setForm({ name: m.name, category: m.category, provider: m.provider, model_name: m.model_name, api_key: m.api_key || '', api_base_url: m.api_base_url || '' })
    setFormErr(''); setDialog({ open: true, id: m.id })
  }
  const save = () => {
    if (!form.name.trim()) { setFormErr('名称不能为空'); return }
    if (!form.model_name.trim()) { setFormErr('模型名不能为空'); return }
    setFormErr('')
    if (dialog.id) updateMut.mutate({ id: dialog.id, data: form })
    else createMut.mutate(form)
  }
  const doTest = async (m: AIModel) => {
    setTests(p => ({ ...p, [m.id]: { running: true } }))
    try {
      const r = await api_.test(m.id)
      setTests(p => ({ ...p, [m.id]: { running: false, ok: r.success, msg: r.result, ms: r.latency_ms } }))
    } catch (e) {
      setTests(p => ({ ...p, [m.id]: { running: false, ok: false, msg: e instanceof Error ? e.message : '失败' } }))
    }
    setTimeout(() => setTests(p => { const n = { ...p }; delete n[m.id]; return n }), 10000)
  }

  const grouped = models ? CATS.map(c => ({ ...c, items: models.filter(m => m.category === c.key) })).filter(g => g.items.length > 0) : []

  return (
    <AppShell>
      <ScrollArea className="h-full">
        {/* Hero */}
        <div className="relative overflow-hidden border-b border-white/[0.04] bg-gradient-to-b from-primary/[0.03] to-transparent">
          <div className="max-w-5xl mx-auto px-6 py-10">
            <div className="flex items-start justify-between">
              <div>
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 ring-1 ring-primary/20 text-xs text-primary font-medium mb-4">
                  <Zap className="w-3 h-3" /> 模型中心
                </div>
                <h2 className="text-3xl font-bold text-white">AI 模型配置</h2>
                <p className="text-sm text-white/40 mt-2 max-w-md">
                  管理接入的 AI 模型，配置 API Key 后可启用真实生成能力
                </p>
              </div>
              <Button onClick={openNew} size="sm" className="gap-1.5">
                <Plus className="w-4 h-4" />添加模型
              </Button>
            </div>
          </div>
        </div>

        <div className="max-w-5xl mx-auto px-6 py-8">
          {isLoading ? (
            <div className="space-y-6">
              {[1,2,3].map(i => <Skeleton key={i} className="h-24 w-full rounded-xl" />)}
            </div>
          ) : grouped.length === 0 ? (
            <div className="text-center py-20">
              <Cpu className="w-12 h-12 mx-auto text-white/10 mb-4" />
              <p className="text-white/30 mb-4">暂无模型配置</p>
              <Button onClick={openNew} variant="outline" size="sm"><Plus className="w-3.5 h-3.5 mr-1.5" />添加第一个模型</Button>
            </div>
          ) : (
            <div className="space-y-10">
              {grouped.map(group => (
                <section key={group.key}>
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: group.color + '18' }}>
                      <group.icon className="w-4 h-4" style={{ color: group.color }} />
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-white">{group.label}</h3>
                      <p className="text-xs text-white/30">{group.desc}</p>
                    </div>
                    <Badge variant="outline" className="text-[10px] ml-auto">{group.items.length}</Badge>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2">
                    {group.items.map(m => {
                      const t = tests[m.id]
                      const cat = CAT_MAP[m.category]
                      return (
                        <div
                          key={m.id}
                          className={cn(
                            'group relative rounded-xl border border-white/[0.06] bg-white/[0.02] hover:bg-white/[0.04] hover:border-white/[0.1] transition-all duration-200',
                            !m.is_enabled && 'opacity-40 hover:opacity-60'
                          )}
                        >
                          {/* Top bar with category indicator */}
                          <div className="absolute top-0 left-0 right-0 h-0.5 rounded-t-xl" style={{ backgroundColor: cat?.color + '40' }} />

                          <div className="p-4 pt-3">
                            <div className="flex items-start justify-between gap-3">
                              <div className="min-w-0 flex-1">
                                <div className="flex items-center gap-2 flex-wrap">
                                  <h4 className="text-sm font-medium text-white truncate">{m.name}</h4>
                                  {m.is_builtin && <Badge className="text-[9px] bg-white/5 text-white/40 border-white/10">内置</Badge>}
                                  {m.api_key && <Badge className="text-[9px] bg-emerald-500/10 text-emerald-400 border-emerald-500/20">
                                    <Check className="w-2.5 h-2.5 mr-0.5" />已配置</Badge>}
                                </div>
                                <p className="text-xs text-white/30 mt-1 truncate">
                                  {m.provider || '—'} · {m.model_name}
                                </p>
                              </div>

                              {/* Toggle */}
                              <button
                                onClick={() => toggleMut.mutate(m.id)}
                                className={cn(
                                  'shrink-0 w-9 h-5 rounded-full relative transition-colors cursor-pointer',
                                  m.is_enabled ? 'bg-emerald-500/30' : 'bg-white/[0.06]'
                                )}
                              >
                                <div className={cn(
                                  'absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform',
                                  m.is_enabled ? 'left-4' : 'left-0.5'
                                )} />
                              </button>
                            </div>

                            {/* Test result */}
                            {t && (
                              <div className={cn('mt-3 text-xs rounded-lg p-2.5', t.ok ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400')}>
                                {t.running ? <span className="flex items-center gap-1.5"><Loader2 className="w-3 h-3 animate-spin" />测试中...</span>
                                : t.ok ? <span>✅ {t.msg?.substring(0, 150)}{t.ms ? <span className="text-white/30 ml-1">· {t.ms}ms</span> : ''}</span>
                                : <span>❌ {t.msg}</span>}
                              </div>
                            )}

                            {/* Actions */}
                            <div className="flex items-center gap-1 mt-3 pt-3 border-t border-white/[0.04]">
                              {m.is_enabled && (
                                <Button variant="ghost" size="sm" className="h-7 text-xs gap-1 text-white/40 hover:text-white" onClick={() => doTest(m)} disabled={t?.running}>
                                  {t?.running ? <Loader2 className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3" />}测试
                                </Button>
                              )}
                              <Button variant="ghost" size="sm" className="h-7 text-xs gap-1 text-white/40 hover:text-white ml-auto" onClick={() => openEdit(m)}>
                                <Pencil className="w-3 h-3" />编辑
                              </Button>
                              {!m.is_builtin && (
                                <Button variant="ghost" size="sm" className="h-7 text-xs gap-1 text-white/40 hover:text-red-400" onClick={() => { if (confirm('确定删除？')) delMut.mutate(m.id) }}>
                                  <Trash2 className="w-3 h-3" />删除
                                </Button>
                              )}
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </section>
              ))}
            </div>
          )}
        </div>
      </ScrollArea>

      {/* ─── Dialog ───────────────────────────────────────────────── */}
      <Dialog open={dialog.open} onOpenChange={v => setDialog({ open: v })}>
        <DialogContent className="max-w-md bg-[#111118] border-white/[0.06]">
          <DialogHeader>
            <DialogTitle className="text-white">{dialog.id ? '编辑模型' : '添加模型'}</DialogTitle>
            <DialogDescription>配置 AI 模型接入参数</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            {formErr && <div className="flex items-center gap-2 text-sm text-red-400 bg-red-500/10 rounded-lg p-2.5"><AlertCircle className="w-4 h-4 shrink-0" />{formErr}</div>}

            <div>
              <label className="text-xs text-white/40 mb-1.5 block">名称</label>
              <Input value={form.name} onChange={e => setForm(p => ({ ...p, name: e.target.value }))} placeholder="例如: Qwen-Plus"
                className="h-10 bg-white/[0.03] border-white/[0.08] text-white placeholder:text-white/15 rounded-lg" />
            </div>

            <div>
              <label className="text-xs text-white/40 mb-1.5 block">分类</label>
              <Select value={form.category} onValueChange={v => { if (v) setForm(p => ({ ...p, category: v })) }}>
                <SelectTrigger className="h-10 bg-white/[0.03] border-white/[0.08] text-white rounded-lg">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-[#111118] border-white/[0.08]">
                  {CATS.map(c => (
                    <SelectItem key={c.key} value={c.key} className="text-white focus:bg-white/[0.06]">
                      <span className="flex items-center gap-2"><c.icon className="w-3.5 h-3.5" style={{color:c.color}} />{c.label}</span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-white/40 mb-1.5 block">供应商</label>
                <Input value={form.provider} onChange={e => setForm(p => ({ ...p, provider: e.target.value }))} placeholder="DashScope"
                  className="h-10 bg-white/[0.03] border-white/[0.08] text-white placeholder:text-white/15 rounded-lg" />
              </div>
              <div>
                <label className="text-xs text-white/40 mb-1.5 block">模型名</label>
                <Input value={form.model_name} onChange={e => setForm(p => ({ ...p, model_name: e.target.value }))} placeholder="qwen-plus"
                  className="h-10 bg-white/[0.03] border-white/[0.08] text-white placeholder:text-white/15 rounded-lg" />
              </div>
            </div>

            <div>
              <label className="text-xs text-white/40 mb-1.5 block">API Key</label>
              <Input value={form.api_key || ''} onChange={e => setForm(p => ({ ...p, api_key: e.target.value }))} placeholder="sk-..." type="password"
                className="h-10 bg-white/[0.03] border-white/[0.08] text-white placeholder:text-white/15 rounded-lg" />
            </div>

            <div>
              <label className="text-xs text-white/40 mb-1.5 block">API Base URL</label>
              <Input value={form.api_base_url || ''} onChange={e => setForm(p => ({ ...p, api_base_url: e.target.value }))} placeholder="https://dashscope.aliyuncs.com/compatible-mode/v1"
                className="h-10 bg-white/[0.03] border-white/[0.08] text-white placeholder:text-white/15 rounded-lg" />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialog({ open: false })} className="border-white/[0.08] text-white/60 hover:text-white">取消</Button>
            <Button onClick={save} disabled={createMut.isPending || updateMut.isPending} className="gap-1.5">
              {(createMut.isPending || updateMut.isPending) && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              {dialog.id ? '保存' : '添加'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </AppShell>
  )
}
