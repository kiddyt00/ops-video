'use client'

import { useState, useEffect } from 'react'
import { Loader2, Check, Server, AlertCircle } from 'lucide-react'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useImageProviders, useActiveImageProvider, useUpdateProjectSettings } from '@/hooks/use-providers'
import { useProject } from '@/hooks/use-projects'
import type { ProviderInfo } from '@/types/provider'

interface ProviderSelectorProps {
  projectId: string
}

export function ProviderSelector({ projectId }: ProviderSelectorProps) {
  const { data: providers, isLoading: loadingProviders } = useImageProviders()
  const { data: activeProvider } = useActiveImageProvider()
  const { data: project } = useProject(projectId)
  const updateSettings = useUpdateProjectSettings(projectId)

  // Current selection: project override or global default
  const currentOverride = project?.settings?.image_provider as string | undefined
  const [selected, setSelected] = useState<string | null>(currentOverride || '')
  const [saved, setSaved] = useState<string | null>(currentOverride || '')

  // Sync when project data loads
  useEffect(() => {
    const override = project?.settings?.image_provider as string | undefined
    setSelected(override || '')
    setSaved(override || '')
  }, [project?.settings?.image_provider])

  const handleSave = async () => {
    try {
      await updateSettings.mutateAsync({
        settings: {
          ...(project?.settings || {}),
          image_provider: selected || null,
        },
      })
      setSaved(selected)
    } catch {
      // Error handled by mutation
    }
  }

  const handleReset = () => {
    setSelected('')
    setSaved('')
  }

  const hasChanges = selected !== saved
  const activeName = providers?.find((p: ProviderInfo) => p.is_active)

  return (
    <div className="space-y-4">
      <div className="flex items-start gap-3">
        <Server className="w-5 h-5 text-muted-foreground shrink-0 mt-0.5" />
        <div className="flex-1 space-y-3">
          <div>
            <h3 className="text-sm font-medium">图片生成引擎</h3>
            <p className="text-xs text-muted-foreground mt-1">
              选择用于生成漫画图片的 AI 引擎。未设置时使用全局默认。
            </p>
          </div>

          {loadingProviders ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="w-4 h-4 animate-spin" />
              加载中...
            </div>
          ) : providers && providers.length > 0 ? (
            <div className="space-y-3">
              <Select value={selected} onValueChange={(v) => setSelected(v)}>
                <SelectTrigger className="w-full max-w-xs">
                  <SelectValue placeholder="使用全局默认" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">使用全局默认 ({activeName?.name || '通义万相 Wan2.6'})</SelectItem>
                  {providers.map((p: ProviderInfo) => (
                    <SelectItem key={p.id} value={p.provider}>
                      <span className="flex items-center gap-2">
                        {p.name}
                        {p.is_active && (
                          <Badge variant="outline" className="text-[10px] px-1 py-0">默认</Badge>
                        )}
                      </span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {selected && (
                <div className="flex items-center gap-2">
                  <Badge variant="secondary" className="text-xs">
                    项目级覆盖：{providers?.find((p: ProviderInfo) => p.provider === selected)?.name || selected}
                  </Badge>
                </div>
              )}

              {hasChanges && (
                <div className="flex items-center gap-2">
                  <Button size="sm" onClick={handleSave} disabled={updateSettings.isPending}>
                    {updateSettings.isPending && <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" />}
                    保存
                  </Button>
                  <Button variant="ghost" size="sm" onClick={handleReset}>
                    取消
                  </Button>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <AlertCircle className="w-4 h-4" />
              暂无可用 Provider
            </div>
          )}
        </div>
      </div>

      {updateSettings.isSuccess && hasChanges && (
        <div className="flex items-center gap-2 text-xs text-green-600">
          <Check className="w-3.5 h-3.5" />
          已保存
        </div>
      )}
    </div>
  )
}
