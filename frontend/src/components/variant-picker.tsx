'use client'

import { useState } from 'react'
import { cn } from '@/lib/utils'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Check, Image as ImageIcon, ScrollText, Music, Film } from 'lucide-react'
import type { FileType } from '@/types/file'

export interface Variant {
  file_id: string
  file_path: string
  file_type: FileType
  generation_params: Record<string, unknown>
  is_selected: boolean
  created_at: string
  thumbnail_url?: string
}

interface VariantPickerProps {
  variants: Variant[]
  selectedId?: string
  onSelect?: (fileId: string) => void
  onConfirm?: (fileId: string) => void
  showActions?: boolean
}

export function VariantPicker({
  variants,
  selectedId,
  onSelect,
  onConfirm,
  showActions = false,
}: VariantPickerProps) {
  const [hoveredId, setHoveredId] = useState<string | null>(null)

  if (!variants || variants.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <p>暂无变体</p>
        <p className="text-sm mt-1">生成后将显示在这里</p>
      </div>
    )
  }

  const getIcon = (fileType: FileType) => {
    switch (fileType) {
      case 'image': return ImageIcon
      case 'script': return ScrollText
      case 'audio': return Music
      case 'video': return Film
      default: return ImageIcon
    }
  }

  const handleSelect = (fileId: string) => {
    onSelect?.(fileId)
  }

  const handleConfirm = (fileId: string) => {
    onConfirm?.(fileId)
  }

  return (
    <div className="grid gap-4 grid-cols-2 auto-rows-fr">
      {variants.map((variant) => {
        const isSelected = selectedId === variant.file_id || variant.is_selected
        const Icon = getIcon(variant.file_type)

        return (
          <Card
            key={variant.file_id}
            className={cn(
              'relative overflow-hidden cursor-pointer transition-all duration-200',
              isSelected
                ? 'ring-2 ring-primary border-primary'
                : 'hover:border-muted-foreground/50'
            )}
            onMouseEnter={() => setHoveredId(variant.file_id)}
            onMouseLeave={() => setHoveredId(null)}
            onClick={() => handleSelect(variant.file_id)}
          >
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <Icon className="w-4 h-4 text-muted-foreground" />
                {isSelected && (
                  <Badge variant="default" className="h-5 text-xs">
                    <Check className="w-3 h-3 mr-1" />
                    已选择
                  </Badge>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-2">
              {/* Preview area */}
              <div className="aspect-square bg-muted rounded-md flex items-center justify-center overflow-hidden">
                {variant.file_type === 'image' && variant.thumbnail_url ? (
                  <img
                    src={variant.thumbnail_url}
                    alt="variant preview"
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="text-center p-4">
                    <Icon className="w-8 h-8 mx-auto text-muted-foreground mb-2" />
                    <p className="text-xs text-muted-foreground truncate max-w-[120px]">
                      {variant.file_path.split('/').pop()}
                    </p>
                  </div>
                )}
              </div>

              {/* Generation params summary */}
              <div className="space-y-1">
                <CardDescription className="text-xs">
                  {(variant.generation_params?.seed as number | undefined) && (
                    <span className="mr-2">Seed: {String(variant.generation_params.seed)}</span>
                  )}
                  {(variant.generation_params?.steps as number | undefined) && (
                    <span>Steps: {String(variant.generation_params.steps)}</span>
                  )}
                </CardDescription>
              </div>

              {/* Actions */}
              {showActions && (
                <div className="flex gap-2 pt-2">
                  <Button
                    size="sm"
                    className={cn(
                      'w-full text-xs',
                      isSelected ? 'bg-primary' : 'bg-muted'
                    )}
                    onClick={(e) => {
                      e.stopPropagation()
                      handleSelect(variant.file_id)
                    }}
                  >
                    选择
                  </Button>
                  <Button
                    size="sm"
                    variant="default"
                    className="w-full text-xs"
                    disabled={!isSelected}
                    onClick={(e) => {
                      e.stopPropagation()
                      handleConfirm(variant.file_id)
                    }}
                  >
                    确认并继续
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
