import { api } from '@/lib/api'
import type { Project, ProjectCreate, ProjectUpdate } from '@/types/project'

interface ShareInfo {
  id: string
  project_id: string
  owner_id: string
  shared_with_user_id: string
  permission: string
  created_at: string
}

export const projectApi = {
  list: () => api.get<Project[]>('/projects').then(r => r.data),

  listMine: () => api.get<Project[]>('/projects/me').then(r => r.data),

  listSharedWithMe: () => api.get<Project[]>('/projects/shared-with-me').then(r => r.data),

  getRecycleBin: () => api.get<Project[]>('/projects/recycle-bin').then(r => r.data),

  get: (id: string) => api.get<Project>(`/projects/${id}`).then(r => r.data),

  create: (data: ProjectCreate) => api.post<Project>('/projects', data).then(r => r.data),

  update: (id: string, data: ProjectUpdate) => api.put<Project>(`/projects/${id}`, data).then(r => r.data),

  /** Soft delete (move to recycle bin) */
  remove: (id: string) => api.delete(`/projects/${id}`),

  /** Restore from recycle bin */
  restore: (id: string) => api.post<Project>(`/projects/${id}/restore`).then(r => r.data),

  /** Permanently delete */
  permanentDelete: (id: string) => api.delete(`/projects/${id}/permanent`),

  // ─── Sharing ────────────────────────────────────────────────

  share: (projectId: string, data: { shared_with_user_id: string; permission: string }) =>
    api.post<ShareInfo>(`/projects/${projectId}/share`, data).then(r => r.data),

  listShares: (projectId: string) =>
    api.get<ShareInfo[]>(`/projects/${projectId}/shares`).then(r => r.data),

  unshare: (projectId: string, userId: string) =>
    api.delete(`/projects/${projectId}/share/${userId}`),

  updateSharePermission: (projectId: string, userId: string, permission: string) =>
    api.put<ShareInfo>(`/projects/${projectId}/share/${userId}`, { permission }).then(r => r.data),
}
