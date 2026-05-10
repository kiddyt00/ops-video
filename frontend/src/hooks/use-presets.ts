import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { presetApi } from '@/lib/api/presets'
import type { PresetCreate, PresetUpdate } from '@/types/preset'

export function usePresets(generatorType?: string) {
  return useQuery({
    queryKey: ['presets', generatorType],
    queryFn: () => presetApi.list(generatorType),
  })
}

export function useCreatePreset() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: presetApi.create,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['presets'] }),
  })
}

export function useUpdatePreset() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: PresetUpdate }) => presetApi.update(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['presets'] }),
  })
}

export function useDeletePreset() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: presetApi.remove,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['presets'] }),
  })
}
