'use client'

import { useState } from 'react'
import { cn } from '@/lib/utils'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Play, RefreshCw, Settings, AlertCircle } from 'lucide-react'
import { type TaskStage } from '@/types/task'
import { STAGE_PARAMS, type ParamField } from '@/lib/stage-params'

interface ParameterPanelProps {
  className?: string
  stage?: TaskStage | null
  parameters?: Record<string, unknown>
  onGenerate?: (params: Record<string, unknown>) => void
  onAdvance?: () => void
  onRollback?: () => void
  canGenerate?: boolean
  canAdvance?: boolean
  children?: React.ReactNode
}

const STAGE_LABELS: Record<string, string> = {
  script: '脚本生成',
  storyboard: '分镜生成',
  image: '图片生成',
  audio: '音频生成',
  video: '视频合成',
}

function validateField(field: ParamField, value: string | number | undefined): string | null {
  if (field.required && (!value || (typeof value === 'string' && !value.trim()))) {
    return `${field.label} 不能为空`
  }
  if (typeof value === 'number') {
    if (field.min !== undefined && value < field.min) return `${field.label} 不能小于 ${field.min}`
    if (field.max !== undefined && value > field.max) return `${field.label} 不能大于 ${field.max}`
  }
  return null
}

export function ParameterPanel({
  className,
  stage,
  parameters,
  onGenerate,
  onAdvance,
  onRollback,
  canGenerate = false,
  canAdvance = false,
  children,
}: ParameterPanelProps) {
  const fields = stage ? STAGE_PARAMS[stage] ?? [] : []
  const [formValues, setFormValues] = useState<Record<string, string | number>>(() => {
    const defaults: Record<string, string | number> = {}
    for (const f of fields) {
      defaults[f.key] = f.default ?? ''
    }
    return defaults
  })
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [apiError, setApiError] = useState<string | null>(null)

  // Reset form when stage changes
  useState // (lint helper — reset in useEffect below)
  const handleStageChange = (newStage: TaskStage | null | undefined) => {
    const newFields = newStage ? STAGE_PARAMS[newStage] ?? [] : []
    const defaults: Record<string, string | number> = {}
    for (const f of newFields) {
      defaults[f.key] = f.default ?? ''
    }
    setFormValues(defaults)
    setErrors({})
    setApiError(null)
  }

  // Watch for stage changes
  const prevStageRef = { current: stage as TaskStage | null | undefined }
  if (prevStageRef.current !== stage) {
    handleStageChange(stage)
    prevStageRef.current = stage
  }

  const updateField = (key: string, value: string | number) => {
    setFormValues((prev) => ({ ...prev, [key]: value }))
    if (errors[key]) {
      setErrors((prev) => {
        const next = { ...prev }
        delete next[key]
        return next
      })
    }
    if (apiError) setApiError(null)
  }

  const handleGenerate = () => {
    setApiError(null)
    const newErrors: Record<string, string> = {}
    for (const f of fields) {
      const err = validateField(f, formValues[f.key])
      if (err) newErrors[f.key] = err
    }
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors)
      return
    }
    onGenerate?.(formValues)
  }

  if (!stage) {
    return (
      <div className={cn('w-72 border-l border-border bg-muted/20 flex flex-col shrink-0', className)}>
        <div className="p-3 border-b border-border">
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">参数面板</h3>
        </div>
        <div className="flex-1 flex items-center justify-center p-4">
          <p className="text-sm text-muted-foreground text-center">选择一个阶段开始</p>
        </div>
      </div>
    )
  }

  return (
    <div className={cn('w-72 border-l border-border bg-muted/20 flex flex-col shrink-0', className)}>
      <div className="p-3 border-b border-border">
        <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">参数面板</h3>
      </div>
      <ScrollArea className="flex-1">
        <div className="p-3 space-y-3">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">{STAGE_LABELS[stage] || stage}</CardTitle>
              <CardDescription>当前阶段操作</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {apiError && (
                <div className="flex items-start gap-2 text-xs text-destructive bg-destructive/10 rounded-md p-2">
                  <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                  <span>{apiError}</span>
                </div>
              )}
              {onGenerate && (
                <Button size="sm" className="w-full" onClick={handleGenerate} disabled={!canGenerate}>
                  <Play className="w-3.5 h-3.5 mr-1.5" />
                  生成
                </Button>
              )}
              {onAdvance && (
                <Button
                  size="sm"
                  variant="secondary"
                  className="w-full"
                  onClick={onAdvance}
                  disabled={!canAdvance}
                >
                  推进到下一阶段
                </Button>
              )}
              {onRollback && (
                <Button size="sm" variant="outline" className="w-full" onClick={onRollback}>
                  <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
                  回退
                </Button>
              )}
            </CardContent>
          </Card>

          {fields.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-1.5">
                  <Settings className="w-3.5 h-3.5" />
                  参数
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {fields.map((field) => (
                  <div key={field.key}>
                    <label className="text-sm font-medium mb-1.5 flex items-center gap-1">
                      {field.label}
                      {field.required && <span className="text-destructive">*</span>}
                    </label>
                    {field.type === 'textarea' ? (
                      <Textarea
                        value={formValues[field.key] as string}
                        onChange={(e) => updateField(field.key, e.target.value)}
                        placeholder={field.placeholder}
                        rows={field.rows ?? 3}
                        className={cn(errors[field.key] && 'border-destructive')}
                      />
                    ) : field.type === 'number' ? (
                      <Input
                        type="number"
                        value={formValues[field.key] as number}
                        min={field.min}
                        max={field.max}
                        step="any"
                        onChange={(e) => updateField(field.key, parseFloat(e.target.value) || 0)}
                        className={cn(errors[field.key] && 'border-destructive')}
                      />
                    ) : field.type === 'select' ? (
                      <Select
                        value={String(formValues[field.key] ?? '')}
                        onValueChange={(v) => { if (v != null) updateField(field.key, v) }}
                      >
                        <SelectTrigger className={cn('w-full', errors[field.key] && 'border-destructive')}>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {field.options?.map((opt) => (
                            <SelectItem key={String(opt.value)} value={String(opt.value)}>
                              {opt.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    ) : (
                      <Input
                        value={formValues[field.key] as string}
                        onChange={(e) => updateField(field.key, e.target.value)}
                        placeholder={field.placeholder}
                        className={cn(errors[field.key] && 'border-destructive')}
                      />
                    )}
                    {errors[field.key] && (
                      <p className="text-xs text-destructive mt-1">{errors[field.key]}</p>
                    )}
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {children}
        </div>
      </ScrollArea>
    </div>
  )
}
