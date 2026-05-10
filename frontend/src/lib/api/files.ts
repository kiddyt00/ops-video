import { api } from '@/lib/api'

export interface FileRecord {
  id: string
  project_id: string
  task_id: string
  variant_group_id: string | null
  file_type: string
  file_path: string
  version: number
  is_selected: boolean
  generation_params?: Record<string, unknown>
  created_at: string
}

export interface VariantGroup {
  id: string
  project_id: string
  task_id: string
  stage: string
  parameters: Record<string, unknown>
  selected_file_id: string | null
  created_at: string
}

export const fileApi = {
  list: (projectId?: string) => {
    const params = projectId ? { project_id: projectId } : {}
    return api.get<FileRecord[]>('/files', { params }).then(r => r.data)
  },
  get: (id: string) => api.get<FileRecord>(`/files/${id}`).then(r => r.data),
  getUrl: (id: string) => api.get(`/files/${id}/url`).then(r => r.data),
  create: (data: { project_id: string; task_id: string; variant_group_id?: string; file_type: string; file_path: string; version?: number; is_selected?: boolean }) =>
    api.post<FileRecord>('/files', data).then(r => r.data),
  remove: (id: string) => api.delete(`/files/${id}`),
}

export const variantApi = {
  select: (variantGroupId: string, fileId: string) =>
    api.post(`/variants/${variantGroupId}/select`, { file_id: fileId }).then(r => r.data),
}
