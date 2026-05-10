'use client'

import { useState } from 'react'
import { Plus, Pencil, Trash2, Loader2, AlertCircle } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { usePresets, useCreatePreset, useUpdatePreset, useDeletePreset } from '@/hooks/use-presets'
import type { Preset } from '@/types/preset'

const GENERATOR_TYPES = [
  { value: 'script', label: '脚本生成' },
  { value: 'storyboard', label: '分镜生成' },
  { value: 'image', label: '图片生成' },
  { value: 'audio', label: '音频生成' },
  { value: 'video_composer', label: '视频合成' },
]

interface PresetManagerProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function PresetManager({ open, onOpenChange }: PresetManagerProps) {
  const { data: presets, isLoading } = usePresets()
  const createPreset = useCreatePreset()
  const updatePreset = useUpdatePreset()
  const deletePreset = useDeletePreset()

  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [formName, setFormName] = useState('')
  const [formType, setFormType] = useState('script')
  const [formDesc, setFormDesc] = useState('')
  const [formError, setFormError] = useState<string | null>(null)

  const resetForm = () => {
    setShowForm(false)
    setEditingId(null)
    setFormName('')
    setFormType('script')
    setFormDesc('')
    setFormError(null)
  }

  const handleEdit = (preset: Preset) => {
    setEditingId(preset.id)
    setFormName(preset.name)
    setFormType(preset.generator_type)
    setFormDesc(preset.description || '')
    setFormError(null)
    setShowForm(true)
  }

  const handleSave = async () => {
    if (!formName.trim()) {
      setFormError('名称不能为空')
      return
    }
    setFormError(null)
    try {
      if (editingId) {
        await updatePreset.mutateAsync({
          id: editingId,
          data: { name: formName.trim(), description: formDesc.trim() || undefined },
        })
      } else {
        await createPreset.mutateAsync({
          name: formName.trim(),
          generator_type: formType,
          description: formDesc.trim() || undefined,
          parameters: {},
        })
      }
      resetForm()
    } catch (e) {
      setFormError(e instanceof Error ? e.message : '保存失败')
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('确定删除此预设？')) return
    try {
      await deletePreset.mutateAsync(id)
    } catch (e) {
      alert(e instanceof Error ? e.message : '删除失败')
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>管理预设模板</DialogTitle>
          <DialogDescription>创建和管理你的生成参数预设</DialogDescription>
        </DialogHeader>

        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">
            {presets?.length ?? 0} 个预设
          </span>
          <Button size="sm" onClick={() => { resetForm(); setShowForm(true); }}>
            <Plus className="w-3.5 h-3.5 mr-1" />
            新建
          </Button>
        </div>

        <Separator />

        <ScrollArea className="max-h-64">
          {isLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
            </div>
          ) : presets && presets.length > 0 ? (
            <div className="space-y-1">
              {presets.map((preset: Preset) => (
                <div
                  key={preset.id}
                  className="flex items-center justify-between px-3 py-2 rounded-md hover:bg-muted/50 group"
                >
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium truncate">{preset.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {GENERATOR_TYPES.find(g => g.value === preset.generator_type)?.label ?? preset.generator_type}
                      {preset.description && ` · ${preset.description}`}
                    </p>
                  </div>
                  <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                    <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => handleEdit(preset)}>
                      <Pencil className="w-3.5 h-3.5" />
                    </Button>
                    <Button variant="ghost" size="icon" className="h-7 w-7 text-destructive" onClick={() => handleDelete(preset.id)}>
                      <Trash2 className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-sm text-muted-foreground">
              还没有预设模板，点击"新建"创建一个
            </div>
          )}
        </ScrollArea>

        {showForm && (
          <>
            <Separator />
            <div className="space-y-3">
              <h4 className="text-sm font-medium">{editingId ? '编辑预设' : '新建预设'}</h4>
              {formError && (
                <div className="flex items-start gap-2 text-xs text-destructive bg-destructive/10 rounded p-2">
                  <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                  <span>{formError}</span>
                </div>
              )}
              <div>
                <label className="text-xs font-medium mb-1 block">名称</label>
                <Input value={formName} onChange={e => setFormName(e.target.value)} placeholder="预设名称" />
              </div>
              {!editingId && (
                <div>
                  <label className="text-xs font-medium mb-1 block">类型</label>
                  <Select value={formType} onValueChange={setFormType}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {GENERATOR_TYPES.map(g => (
                        <SelectItem key={g.value} value={g.value}>{g.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
              <div>
                <label className="text-xs font-medium mb-1 block">描述（可选）</label>
                <Textarea
                  value={formDesc}
                  onChange={e => setFormDesc(e.target.value)}
                  placeholder="预设描述"
                  rows={2}
                />
              </div>
              <div className="flex gap-2 justify-end">
                <Button variant="outline" size="sm" onClick={resetForm}>取消</Button>
                <Button size="sm" onClick={handleSave} disabled={createPreset.isPending || updatePreset.isPending}>
                  {(createPreset.isPending || updatePreset.isPending) && <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" />}
                  保存
                </Button>
              </div>
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
