import { api } from '@/lib/api'

export const workflowApi = {
  getStatus: (projectId: string) =>
    api.get(`/workflow/${projectId}/status`).then(r => r.data),
  getHistory: (projectId: string) =>
    api.get(`/workflow/${projectId}/history`).then(r => r.data),
  advance: (projectId: string, params?: { generator_type?: string; parameters?: Record<string, unknown> }) =>
    api.post(`/workflow/${projectId}/advance`, params).then(r => r.data),
  advanceToStage: (projectId: string, stage: string, parameters?: Record<string, unknown>) =>
    api.post(`/workflow/${projectId}/advance/${stage}`, parameters).then(r => r.data),
  rollback: (projectId: string, stage: string, fileId?: string) =>
    api.post(`/workflow/${projectId}/rollback/${stage}`, { file_id: fileId }).then(r => r.data),
  compareVariants: (variantGroupId: string) =>
    api.get(`/workflow/variants/${variantGroupId}/compare`).then(r => r.data),
  getLineage: (fileId: string) =>
    api.get(`/workflow/files/${fileId}/lineage`).then(r => r.data),
  getVersions: (fileId: string) =>
    api.get(`/workflow/files/${fileId}/versions`).then(r => r.data),
}
