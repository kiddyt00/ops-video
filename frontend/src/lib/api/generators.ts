import { api } from '@/lib/api'

export interface GeneratorInfo {
  name: string
  type: string
  description: string
  parameters: Record<string, { type: string; required: boolean; default?: unknown; description: string }>
}

export const generatorApi = {
  list: () => api.get<GeneratorInfo[]>('/generators').then(r => r.data),
  get: (type: string) => api.get<GeneratorInfo>(`/generators/${type}`).then(r => r.data),
  generate: (type: string, data: { project_id: string; parameters: Record<string, unknown> }) =>
    api.post(`/generators/${type}/generate`, data).then(r => r.data),
}
