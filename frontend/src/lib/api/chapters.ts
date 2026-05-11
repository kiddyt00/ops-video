import { api } from '@/lib/api'
import type { Chapter, ChapterCreate, ChapterUpdate } from '@/types/chapter'

export const chapterApi = {
  list: (projectId: string) =>
    api.get<Chapter[]>(`/projects/${projectId}/chapters`).then(r => r.data),

  get: (projectId: string, chapterId: string) =>
    api.get<Chapter>(`/projects/${projectId}/chapters/${chapterId}`).then(r => r.data),

  create: (projectId: string, data: ChapterCreate) =>
    api.post<Chapter>(`/projects/${projectId}/chapters`, data).then(r => r.data),

  update: (projectId: string, chapterId: string, data: ChapterUpdate) =>
    api.put<Chapter>(`/projects/${projectId}/chapters/${chapterId}`, data).then(r => r.data),

  remove: (projectId: string, chapterId: string) =>
    api.delete(`/projects/${projectId}/chapters/${chapterId}`),
}
