'use client'

import { useState } from 'react'
import {
  Brain, Paintbrush, Mic, Music, Clapperboard, Cpu, Sparkles,
  Plus, Pencil, Trash2, Play, Loader2, AlertCircle, CheckCircle2,
  X, Power, PowerOff, FlaskConical, Zap
} from 'lucide-react'
import { AppShell } from '@/components/app-shell'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
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
  id: string
  name: string
  category: string
  provider: string
  model_name: string
  api_key: string | null
  api_base_url: string | null
  is_enabled: boolean
  is_builtin: boolean
  config: Record<string, unknown>
  created_at: string
  updated_at: string
}

interface ModelForm {
  name: string; category: string; provider: string; model_name: string
  api_key?: string; api_base_url?: string
}

const emptyForm: ModelForm = {
  name: '', category: 'llm', provider: 'dashscope', model_name: '',
  api_key: '', api_base_url: '',
}

// ─── Category Config ──────────────────────────────────────────────────

const CATEGORIES: Record<string, { label: string; icon: typeof Brain; color: string; providers: { value: string; label: string }[] }> = {
  llm: { label: '大语言模型', icon: Brain, color: '#6366f1',
    providers: [{ value: 'dashscope', label: 'DashScope' }, { value: 'openai', label: 'OpenAI' }, { value: 'ollama', label: 'Ollama' }] },
  wanx: { label: '文生图', icon: Paintbrush, color: '#f59e0b',
    providers: [{ value: 'dashscope', label: '通义万相' }, { value: 'siliconflow', label: 'SiliconFlow' }] },
  tts: { label: '文生音频', icon: Mic, color: '#10b981',
    providers: [{ value: 'edge_tts', label: 'Edge TTS' }] },
  bgm: { label: '音乐生成', icon: Music, color: '#ec4899',
    providers: [{ value: 'scipy', label: 'SciPy 合成' }] },
  video: { label: '视频合成', icon: Clapperboard, color: '#06b6d4',
    providers: [{ value: 'ffmpeg', label: 'FFmpeg' }] },
}

// ─── API ──────────────────────────────────────────────────────────────

const modelsApi = {
  list: () => api.get<AIModel[]>('/models').then(r => r.data),
  create: (data: ModelForm & { config?: Record<string, unknown> }) => api.post<AIModel>('/models', data).then(r => r.data),
  update: (id: string, data: Partial<ModelForm>) => api.put<AIModel>(`/models/${id}`, data).then(r => r.data),
  delete: (id: string) => api.delete(`/models/${id}`),
  toggle: (id: string) => api.post<AIModel>(`/models/${id}/toggle`).then(r => r.data),
  test: (id: string, prompt?: string) => api.post<{ success: boolean; message: string; latency_ms: number; result: string }>(`/models/${id}/test`, { prompt }).then(r => r.data),
}

// ─── Main Page ────────────────────────────────────────────────────────

export default function ModelsPage() {
  const qc = useQueryClient()
  const { data: models, isLoading, error } = useQuery({ queryKey: ['ai-models'], queryFn: modelsApi.list })

  const [formOpen, setFormOpen] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [form, setForm] = useState<ModelForm>(emptyForm)
  const [formError, setFormError] = useState<string | null>(null)

  const [testResult, setTestResult] = useState<Record<string, { running: boolean; result?: string; error?: string; latency?: number }>>({})

  const createMut = useMutation({ mutationFn: modelsApi.create, onSuccess: () => { qc.invalidateQueries({ queryKey: ['ai-models'] }); setFormOpen(false) } })
  const updateMut = useMutation({ mutationFn: ({ id, data }: { id: string; data: Partial<ModelForm> }) => modelsApi.update(id, data), onSuccess: () => { qc.invalidateQueries({ queryKey: ['ai-models'] }); setFormOpen(false) } })
  const deleteMut = useMutation({ mutationFn: modelsApi.delete, onSuccess: () => qc.invalidateQueries({ queryKey: ['ai-models'] }) })
  const toggleMut = useMutation({ mutationFn: modelsApi.toggle, onSuccess: () => qc.invalidateQueries({ queryKey: ['ai-models'] }) })

  const openCreate = () => { setEditingId(null); setForm(emptyForm); setFormError(null); setFormOpen(true) }
  const openEdit = (m: AIModel) => {
    setEditingId(m.id)
    setForm({ name: m.name, category: m.category, provider: m.provider, model_name: m.model_name, api_key: m.api_key || '', api_base_url: m.api_base_url || '' })
    setFormError(null)
    setFormOpen(true)
  }

  const handleSave = () => {
    if (!form.name.trim()) { setFormError('名称不能为空'); return }
    if (!form.model_name.trim()) { setFormError('模型名称不能为空'); return }
    setFormError(null)
    if (editingId) updateMut.mutate({ id: editingId, data: form })
    else createMut.mutate(form)
  }

  const handleTest = async (model: AIModel) => {
    setTestResult(prev => ({ ...prev, [model.id]: { running: true } }))
    try {
      const r = await modelsApi.test(model.id)
      setTestResult(prev => ({ ...prev, [model.id]: { running: false, result: r.result, latency: r.latency_ms } }))
    } catch (e) {
      setTestResult(prev => ({ ...prev, [model.id]: { running: false, error: e instanceof Error ? e.message : 'Test failed' } }))
    }
    setTimeout(() => setTestResult(prev => { const n = { ...prev }; delete n[model.id]; return n }), 8000)
  }

  const grouped = models ? Object.entries(CATEGORIES).map(([cat, cfg]) => ({
    ...cfg, key: cat, models: models.filter(m => m.category === cat)
  })).filter(g => g.models.length > 0) : []

  return (
    <AppShell>
      <ScrollArea className="h-full">
        <div className="p-6 max-w-5xl mx-auto">
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-primary/10 ring-1 ring-primary/20 flex items-center justify-center">
                <Cpu className="w-5 h-5 text-primary" />
              </div>
              <div>
                <h2 className="text-2xl font-bold">模型管理</h2>
                <p className="text-sm text-muted-foreground">配置和管理 AI 模型接入</p>
              </div>
            </div>
            <Button onClick={openCreate}><Plus className="w-4 h-4 mr-1.5" />添加模型</Button>
          </div>

          {isLoading ? (
            <div className="space-y-4">{[1,2,3].map(i => <Skeleton key={i} className="h-20 w-full" />)}</div>
          ) : (
            <div className="space-y-8">
              {grouped.map(group => (
                <section key={group.key}>
                  <div className="flex items-center gap-2 mb-3">
                    <group.icon className="w-4 h-4" style={{ color: group.color }} />
                    <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">{group.label}</h3>
                    <Badge variant="outline" className="text-[10px]">{group.models.length}</Badge>
                  </div>
                  <div className="space-y-2">
                    {group.models.map(model => {
                      const test = testResult[model.id]
                      return (
                        <Card key={model.id} className={cn('border-border/50 transition-all', !model.is_enabled && 'opacity-50')}>
                          <CardHeader className="py-3 px-4">
                            <div className="flex items-center gap-4">
                              <button
                                onClick={() => toggleMut.mutate(model.id)}
                                className={cn('shrink-0 transition-colors cursor-pointer', model.is_enabled ? 'text-emerald-400' : 'text-muted-foreground')}
                                title={model.is_enabled ? '已启用，点击禁用' : '已禁用，点击启用'}
                              >
                                {model.is_enabled ? <Power className="w-5 h-5" /> : <PowerOff className="w-5 h-5" />}
                              </button>

                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2">
                                  <span className="font-medium text-sm">{model.name}</span>
                                  {!model.is_enabled && <Badge className="text-[10px] bg-muted">已禁用</Badge>}
                                  {model.is_builtin && <Badge className="text-[10px] bg-primary/10 text-primary border-primary/20">内置</Badge>}
                                  {model.api_key && <Badge className="text-[10px] bg-emerald-500/10 text-emerald-400 border-emerald-500/20">已配置</Badge>}
                                </div>
                                <p className="text-xs text-muted-foreground mt-0.5">
                                  {model.provider} · {model.model_name}
                                  {model.api_base_url && ` · ${model.api_base_url}`}
                                </p>
                                {test && (
                                  <div className={cn('mt-2 text-xs rounded-lg p-2', test.error ? 'bg-red-500/10 text-red-400' : 'bg-emerald-500/10 text-emerald-400')}>
                                    {test.running ? (
                                      <span className="flex items-center gap-1"><Loader2 className="w-3 h-3 animate-spin" />测试中...</span>
                                    ) : test.error ? (
                                      `失败: ${test.error}`
                                    ) : (
                                      <span>✅ {test.result?.substring(0, 200)}{test.latency ? ` (${test.latency}ms)` : ''}</span>
                                    )}
                                  </div>
                                )}
                              </div>

                              <div className="flex items-center gap-1 shrink-0">
                                {model.is_enabled && (
                                  <Button variant="ghost" size="icon" className="h-8 w-8" title="测试连接" onClick={() => handleTest(model)} disabled={test?.running}>
                                    {test?.running ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
                                  </Button>
                                )}
                                <Button variant="ghost" size="icon" className="h-8 w-8" title="编辑" onClick={() => openEdit(model)}>
                                  <Pencil className="w-3.5 h-3.5" />
                                </Button>
                                {!model.is_builtin && (
                                  <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive" title="删除" onClick={() => { if (confirm('确定删除？')) deleteMut.mutate(model.id) }}>
                                    <Trash2 className="w-3.5 h-3.5" />
                                  </Button>
                                )}
                              </div>
                            </div>
                          </CardHeader>
                        </Card>
                      )
                    })}
                  </div>
                </section>
              ))}
            </div>
          )}
        </div>
      </ScrollArea>

      {/* ─── Add/Edit Dialog ────────────────────────────────────── */}
      <Dialog open={formOpen} onOpenChange={setFormOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{editingId ? '编辑模型' : '添加模型'}</DialogTitle>
            <DialogDescription>配置 AI 模型接入参数</DialogDescription>
          </DialogHeader>

          <div className="space-y-3 py-4">
            {formError && (
              <div className="flex items-center gap-2 text-sm text-destructive bg-destructive/10 rounded-lg p-2.5">
                <AlertCircle className="w-4 h-4 shrink-0" /><span>{formError}</span>
              </div>
            )}

            <div>
              <label className="text-xs font-medium mb-1 block">名称</label>
              <Input value={form.name} onChange={e => setForm(p => ({ ...p, name: e.target.value }))} placeholder="例如: 通义千问 (Qwen-Plus)" />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-medium mb-1 block">分类</label>
                <Select value={form.category} onValueChange={v => { if (v) setForm(p => ({ ...p, category: v, provider: CATEGORIES[v]?.providers[0]?.value || '' })) }}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {Object.entries(CATEGORIES).map(([k, v]) => <SelectItem key={k} value={k}>{v.label}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-xs font-medium mb-1 block">提供商</label>
                <Select value={form.provider} onValueChange={v => { if (v) setForm(p => ({ ...p, provider: v })) }}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {(CATEGORIES[form.category]?.providers || []).map(p => <SelectItem key={p.value} value={p.value}>{p.label}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div>
              <label className="text-xs font-medium mb-1 block">模型名称</label>
              <Input value={form.model_name} onChange={e => setForm(p => ({ ...p, model_name: e.target.value }))} placeholder="例如: qwen-plus" />
            </div>

            <div>
              <label className="text-xs font-medium mb-1 block">API Key</label>
              <Input value={form.api_key} onChange={e => setForm(p => ({ ...p, api_key: e.target.value }))} placeholder="sk-..." type="password" />
            </div>

            <div>
              <label className="text-xs font-medium mb-1 block">API Base URL</label>
              <Input value={form.api_base_url} onChange={e => setForm(p => ({ ...p, api_base_url: e.target.value }))} placeholder="https://api.example.com/v1" />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setFormOpen(false)}>取消</Button>
            <Button onClick={handleSave} disabled={createMut.isPending || updateMut.isPending}>
              {(createMut.isPending || updateMut.isPending) && <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />}
              {editingId ? '保存' : '添加'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </AppShell>
  )
}
