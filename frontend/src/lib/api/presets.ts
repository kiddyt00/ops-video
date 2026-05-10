import { api } from '@/lib/api'
import type { Preset, PresetCreate, PresetUpdate } from '@/types/preset'

export const presetApi = {
  list: (generatorType?: string) =>
    api.get<Preset[]>('/presets', { params: generatorType ? { generator_type: generatorType } : {} }).then(r => r.data),

  get: (id: string) =>
    api.get<Preset>(`/presets/${id}`).then(r => r.data),

  create: (data: PresetCreate) =>
    api.post<Preset>('/presets', data).then(r => r.data),

  update: (id: string, data: PresetUpdate) =>
    api.put<Preset>(`/presets/${id}`, data).then(r => r.data),

  remove: (id: string) =>
    api.delete(`/presets/${id}`),
}
