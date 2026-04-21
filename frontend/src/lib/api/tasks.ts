import { api } from '@/lib/api'
import type { Task, TaskCreate, TaskStatusUpdate } from '@/types/task'

export const taskApi = {
  list: (projectId?: string) => {
    const params = projectId ? { project_id: projectId } : {}
    return api.get<Task[]>('/tasks', { params }).then(r => r.data)
  },
  get: (id: string) => api.get<Task>(`/tasks/${id}`).then(r => r.data),
  create: (data: TaskCreate) => api.post<Task>('/tasks', data).then(r => r.data),
  updateStatus: (id: string, data: TaskStatusUpdate) =>
    api.put<Task>(`/tasks/${id}/status`, data).then(r => r.data),
  run: (id: string) => api.post<Task>(`/tasks/${id}/run`).then(r => r.data),
  remove: (id: string) => api.delete(`/tasks/${id}`),
  logs: (id: string) => api.get(`/tasks/${id}/logs`).then(r => r.data),
}
