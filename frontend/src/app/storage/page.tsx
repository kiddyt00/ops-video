'use client'

import { useState } from 'react'
import {
  HardDrive, Plus, Pencil, Trash2, Zap, Loader2, AlertCircle,
  CheckCircle2, XCircle, Power, Play, Server, Globe, Key, Database
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
import { cn } from '@/lib/utils'
import {
  useStorageProviders,
  useCreateStorageProvider,
  useUpdateStorageProvider,
  useDeleteStorageProvider,
  useTestStorageProvider,
  useActivateStorageProvider,
} from '@/hooks/use-storage'
import type { StorageProvider, StorageProviderForm, StorageTestResult } from '@/lib/api/storage'

// ─── Constants ────────────────────────────────────────────────────────

const PROVIDER_TYPES = [
  { key: 's3', label: 'Amazon S3', desc: 'AWS S3 对象存储' },
  { key: 's3_compatible', label: 'S3 兼容', desc: 'MinIO / Cloudflare R2 等' },
  { key: 'oss', label: '阿里云 OSS', desc: '阿里云对象存储' },
  { key: 'cos', label: '腾讯云 COS', desc: '腾讯云对象存储' },
  { key: 'local', label: '本地存储', desc: '本地文件系统' },
] as const

const emptyForm: StorageProviderForm = {
  name: '',
  provider_type: 's3',
  access_key: '',
  secret_key: '',
  bucket: '',
  endpoint: '',
  region: '',
}

const TYPE_ICON: Record<string, typeof Server> = {
  s3: Server,
  s3_compatible: Globe,
  oss: Database,
  cos: Database,
  local: HardDrive,
}

const TYPE_COLORS: Record<string, string> = {
  s3: '#f59e0b',
  s3_compatible: '#818cf8',
  oss: '#22d3ee',
  cos: '#f472b6',
  local: '#34d399',
}

// ─── Component ────────────────────────────────────────────────────────

export default function StoragePage() {
  const { data: providers, isLoading } = useStorageProviders()

  const [dialog, setDialog] = useState<{ open: boolean; id?: string }>({ open: false })
  const [form, setForm] = useState<StorageProviderForm>(emptyForm)
  const [formErr, setFormErr] = useState('')

  const [tests, setTests] = useState<Record<string, { running: boolean; result?: StorageTestResult }>>({})

  const createMut = useCreateStorageProvider()
  const updateMut = useUpdateStorageProvider(dialog.id || '')
  const delMut = useDeleteStorageProvider()
  const testMut = useTestStorageProvider()
  const activateMut = useActivateStorageProvider()

  const openNew = () => {
    setForm(emptyForm)
    setFormErr('')
    setDialog({ open: true })
  }

  const openEdit = (p: StorageProvider) => {
    setForm({
      name: p.name,
      provider_type: p.provider_type,
      access_key: p.access_key,
      secret_key: '',
      bucket: p.bucket,
      endpoint: p.endpoint || '',
      region: p.region || '',
    })
    setFormErr('')
    setDialog({ open: true, id: p.id })
  }

  const save = () => {
    if (!form.name.trim()) { setFormErr('名称不能为空'); return }
    if (!form.provider_type) { setFormErr('请选择存储类型'); return }
    if (!form.bucket.trim()) { setFormErr('Bucket 不能为空'); return }
    if (!form.access_key.trim()) { setFormErr('Access Key 不能为空'); return }
    if (!dialog.id && !form.secret_key.trim()) { setFormErr('Secret Key 不能为空'); return }
    setFormErr('')

    const data: StorageProviderForm = {
      ...form,
      endpoint: form.endpoint || undefined,
      region: form.region || undefined,
    }
    // Omit secret_key if empty on edit
    if (dialog.id && !form.secret_key) {
      delete (data as Partial<StorageProviderForm>).secret_key
    }

    if (dialog.id) updateMut.mutate(data as Partial<StorageProviderForm>)
    else createMut.mutate(data)
  }

  const doTest = async (p: StorageProvider) => {
    setTests(prev => ({ ...prev, [p.id]: { running: true } }))
    try {
      const result = await testMut.mutateAsync(p.id)
      setTests(prev => ({ ...prev, [p.id]: { running: false, result } }))
    } catch {
      setTests(prev => ({ ...prev, [p.id]: { running: false, result: { success: false, message: '测试请求失败', latency_ms: null, provider_name: null, bucket: null } } }))
    }
    setTimeout(() => {
      setTests(prev => { const n = { ...prev }; delete n[p.id]; return n })
    }, 15000)
  }

  const doActivate = (p: StorageProvider) => {
    if (!p.is_active && !confirm(`确定将 "${p.name}" 设为当前活跃存储？`)) return
    activateMut.mutate(p.id)
  }

  const doDelete = (p: StorageProvider) => {
    if (p.is_active) {
      alert('无法删除当前活跃的存储配置')
      return
    }
    if (!confirm(`确定删除 "${p.name}"？此操作不可撤销。`)) return
    delMut.mutate(p.id)
  }

  const isPending = createMut.isPending || updateMut.isPending

  return (
    <AppShell>
      <ScrollArea className="h-full">
        {/* Hero */}
        <div className="relative overflow-hidden border-b border-border bg-gradient-to-b from-primary/[0.03] to-transparent">
          <div className="max-w-5xl mx-auto px-6 py-10">
            <div className="flex items-start justify-between">
              <div>
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 ring-1 ring-primary/20 text-xs text-primary font-medium mb-4">
                  <HardDrive className="w-3 h-3" /> 存储管理
                </div>
                <h2 className="text-3xl font-bold text-foreground">存储配置</h2>
                <p className="text-sm text-muted-foreground mt-2 max-w-md">
                  管理对象存储供应商配置，支持 S3、OSS、COS 等多种云存储
                </p>
              </div>
              <Button onClick={openNew} size="sm" className="gap-1.5">
                <Plus className="w-4 h-4" />添加存储
              </Button>
            </div>
          </div>
        </div>

        <div className="max-w-5xl mx-auto px-6 py-8">
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map(i => <Skeleton key={i} className="h-20 w-full rounded-xl" />)}
            </div>
          ) : providers?.length === 0 ? (
            <div className="text-center py-20">
              <HardDrive className="w-12 h-12 mx-auto text-muted-foreground/20 mb-4" />
              <p className="text-muted-foreground mb-4">暂无存储配置</p>
              <Button onClick={openNew} variant="outline" size="sm">
                <Plus className="w-3.5 h-3.5 mr-1.5" />添加第一个存储
              </Button>
            </div>
          ) : (
            <div className="space-y-3">
              {providers?.map(p => {
                const t = tests[p.id]
                const TypeIcon = TYPE_ICON[p.provider_type] || Server
                const typeColor = TYPE_COLORS[p.provider_type] || '#818cf8'

                return (
                  <div
                    key={p.id}
                    className={cn(
                      'group relative rounded-xl border bg-card shadow-sm ring-1 ring-foreground/5 transition-all duration-200',
                      p.is_active
                        ? 'border-primary/30 bg-primary/[0.03]'
                        : 'border-white/[0.06] hover:bg-white/[0.04] hover:border-white/[0.1]'
                    )}
                  >
                    {p.is_active && (
                      <div className="absolute top-0 left-0 right-0 h-0.5 rounded-t-xl bg-primary/60" />
                    )}

                    <div className="p-4">
                      <div className="flex items-start gap-4">
                        {/* Icon */}
                        <div
                          className="w-10 h-10 rounded-lg flex items-center justify-center shrink-0"
                          style={{ backgroundColor: typeColor + '18' }}
                        >
                          <TypeIcon className="w-5 h-5" style={{ color: typeColor }} />
                        </div>

                        {/* Info */}
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <h4 className="text-sm font-medium text-foreground">{p.name}</h4>
                            <Badge variant="outline" className="text-[10px] border-border text-muted-foreground">
                              {PROVIDER_TYPES.find(t => t.key === p.provider_type)?.label || p.provider_type}
                            </Badge>
                            {p.is_active && (
                              <Badge className="text-[10px] bg-emerald-500/10 text-emerald-400 border-emerald-500/20">
                                <CheckCircle2 className="w-2.5 h-2.5 mr-0.5" />活跃
                              </Badge>
                            )}
                          </div>

                          <div className="flex items-center gap-4 mt-1 text-xs text-muted-foreground">
                            <span className="truncate">{p.bucket}</span>
                            {p.endpoint && (
                              <span className="truncate hidden sm:inline">{p.endpoint}</span>
                            )}
                            {p.region && <span>{p.region}</span>}
                          </div>

                          {/* Last test status */}
                          {p.last_tested_at && !t && (
                            <div className="mt-2 flex items-center gap-1.5 text-xs">
                              {p.last_test_status === 'success' ? (
                                <span className="text-emerald-400/60">
                                  <CheckCircle2 className="w-3 h-3 inline mr-0.5" />
                                  上次测试通过
                                </span>
                              ) : p.last_test_status === 'failed' ? (
                                <span className="text-red-400/60" title={p.last_test_error || undefined}>
                                  <XCircle className="w-3 h-3 inline mr-0.5" />
                                  上次测试失败
                                </span>
                              ) : null}
                              <span className="text-muted-foreground/40">·</span>
                              <span className="text-muted-foreground/40">
                                {new Date(p.last_tested_at).toLocaleString('zh-CN')}
                              </span>
                            </div>
                          )}

                          {/* Current test result */}
                          {t && (
                            <div className={cn(
                              'mt-2 text-xs rounded-lg p-2.5',
                              t.result?.success ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
                            )}>
                              {t.running ? (
                                <span className="flex items-center gap-1.5">
                                  <Loader2 className="w-3 h-3 animate-spin" />测试中...
                                </span>
                              ) : t.result?.success ? (
                                <span>
                                  ✅ {t.result.message}
                                  {t.result.latency_ms && (
                                    <span className="text-white/30 ml-1">· {t.result.latency_ms}ms</span>
                                  )}
                                </span>
                              ) : (
                                <span>❌ {t.result?.message || '连接失败'}</span>
                              )}
                            </div>
                          )}
                        </div>

                        {/* Actions */}
                        <div className="flex items-center gap-1 shrink-0">
                          <Button
                            variant="ghost" size="sm"
                            className="h-7 text-xs gap-1 text-muted-foreground hover:text-foreground"
                            onClick={() => doTest(p)}
                            disabled={t?.running}
                          >
                            {t?.running ? (
                              <Loader2 className="w-3 h-3 animate-spin" />
                            ) : (
                              <Play className="w-3 h-3" />
                            )}
                            测试
                          </Button>

                          {!p.is_active ? (
                            <Button
                              variant="ghost" size="sm"
                              className="h-7 text-xs gap-1 text-muted-foreground hover:text-emerald-500"
                              onClick={() => doActivate(p)}
                              disabled={activateMut.isPending}
                            >
                              {activateMut.isPending ? (
                                <Loader2 className="w-3 h-3 animate-spin" />
                              ) : (
                                <Power className="w-3 h-3" />
                              )}
                              激活
                            </Button>
                          ) : (
                            <Button
                              variant="ghost" size="sm"
                              className="h-7 text-xs gap-1 text-emerald-400/60 cursor-default"
                              disabled
                            >
                              <CheckCircle2 className="w-3 h-3" />已激活
                            </Button>
                          )}

                          <Button
                            variant="ghost" size="sm"
                            className="h-7 text-xs gap-1 text-muted-foreground hover:text-foreground"
                            onClick={() => openEdit(p)}
                          >
                            <Pencil className="w-3 h-3" />编辑
                          </Button>

                          <Button
                            variant="ghost" size="sm"
                            className="h-7 text-xs gap-1 text-white/40 hover:text-red-400"
                            onClick={() => doDelete(p)}
                            disabled={delMut.isPending}
                          >
                            {delMut.isPending ? (
                              <Loader2 className="w-3 h-3 animate-spin" />
                            ) : (
                              <Trash2 className="w-3 h-3" />
                            )}
                            删除
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </ScrollArea>

      {/* ─── Dialog ───────────────────────────────────────────────── */}
      <Dialog open={dialog.open} onOpenChange={v => setDialog({ open: v })}>
        <DialogContent className="max-w-md bg-card border-border">
          <DialogHeader>
            <DialogTitle className="text-white">{dialog.id ? '编辑存储' : '添加存储'}</DialogTitle>
            <DialogDescription>配置对象存储供应商参数</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            {formErr && (
              <div className="flex items-center gap-2 text-sm text-red-400 bg-red-500/10 rounded-lg p-2.5">
                <AlertCircle className="w-4 h-4 shrink-0" />{formErr}
              </div>
            )}

            <div>
              <label className="text-xs text-muted-foreground mb-1.5 block">名称</label>
              <Input
                value={form.name}
                onChange={e => setForm(p => ({ ...p, name: e.target.value }))}
                placeholder="例如: 阿里云主存储"
                className="h-10 bg-background border-input text-foreground placeholder:text-muted-foreground rounded-lg"
              />
            </div>

            <div>
              <label className="text-xs text-muted-foreground mb-1.5 block">存储类型</label>
              <Select
                value={form.provider_type}
                onValueChange={v => { if (v) setForm(p => ({ ...p, provider_type: v })) }}
              >
                <SelectTrigger className="h-10 bg-background border-input text-foreground rounded-lg">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-card border-border">
                  {PROVIDER_TYPES.map(t => (
                    <SelectItem key={t.key} value={t.key} className="text-foreground focus:bg-accent">
                      <span className="flex items-center gap-2">
                        {t.label}
                        <span className="text-white/30 text-xs">— {t.desc}</span>
                      </span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-muted-foreground mb-1.5 block">Access Key</label>
                <Input
                  value={form.access_key}
                  onChange={e => setForm(p => ({ ...p, access_key: e.target.value }))}
                  placeholder="LTAI..."
                  className="h-10 bg-background border-input text-foreground placeholder:text-muted-foreground rounded-lg"
                />
              </div>
              <div>
                <label className="text-xs text-muted-foreground mb-1.5 block">
                  Secret Key{dialog.id && <span className="text-muted-foreground/40 ml-1">(留空不修改)</span>}
                </label>
                <Input
                  value={form.secret_key}
                  onChange={e => setForm(p => ({ ...p, secret_key: e.target.value }))}
                  placeholder={dialog.id ? '••••••••' : 'sk-...'}
                  type="password"
                  className="h-10 bg-background border-input text-foreground placeholder:text-muted-foreground rounded-lg"
                />
              </div>
            </div>

            <div>
              <label className="text-xs text-muted-foreground mb-1.5 block">Bucket</label>
              <Input
                value={form.bucket}
                onChange={e => setForm(p => ({ ...p, bucket: e.target.value }))}
                placeholder="my-bucket"
                className="h-10 bg-background border-input text-foreground placeholder:text-muted-foreground rounded-lg"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-muted-foreground mb-1.5 block">
                  Endpoint<span className="text-muted-foreground/40 ml-1">(可选)</span>
                </label>
                <Input
                  value={form.endpoint || ''}
                  onChange={e => setForm(p => ({ ...p, endpoint: e.target.value }))}
                  placeholder="https://oss-cn-hangzhou.aliyuncs.com"
                  className="h-10 bg-background border-input text-foreground placeholder:text-muted-foreground rounded-lg"
                />
              </div>
              <div>
                <label className="text-xs text-muted-foreground mb-1.5 block">
                  Region<span className="text-muted-foreground/40 ml-1">(可选)</span>
                </label>
                <Input
                  value={form.region || ''}
                  onChange={e => setForm(p => ({ ...p, region: e.target.value }))}
                  placeholder="cn-hangzhou"
                  className="h-10 bg-background border-input text-foreground placeholder:text-muted-foreground rounded-lg"
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDialog({ open: false })}
              className="border-border text-muted-foreground hover:text-foreground"
            >
              取消
            </Button>
            <Button onClick={save} disabled={isPending} className="gap-1.5">
              {isPending && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              {dialog.id ? '保存' : '添加'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </AppShell>
  )
}
