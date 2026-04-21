import { api } from '@/lib/api'
import type { Project, ProjectCreate, ProjectUpdate } from '@/types/project'

export const projectApi = {
  list: () => api.get<Project[]>('/projects').then(r => r.data),
  get: (id: string) => api.get<Project>(`/projects/${id}`).then(r => r.data),
  create: (data: ProjectCreate) => api.post<Project>('/projects', data).then(r => r.data),
  update: (id: string, data: ProjectUpdate) => api.put<Project>(`/projects/${id}`, data).then(r => r.data),
  remove: (id: string) => api.delete(`/projects/${id}`),
}
