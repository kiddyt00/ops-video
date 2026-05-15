import { api } from '@/lib/api'
import type { Story, StoryCreate, StoryUpdate, InspirationRequest } from '@/types/story'

export const storyApi = {
  get: (projectId: string) =>
    api.get<Story | null>(`/projects/${projectId}/story`).then(r => r.data),

  create: (projectId: string, data: StoryCreate) =>
    api.post<Story>(`/projects/${projectId}/story`, data).then(r => r.data),

  update: (projectId: string, data: StoryUpdate) =>
    api.put<Story>(`/projects/${projectId}/story`, data).then(r => r.data),

  remove: (projectId: string) =>
    api.delete(`/projects/${projectId}/story`),

  generateInspiration: (projectId: string, data: InspirationRequest) =>
    api.post<Story>(`/workflow/${projectId}/advance/inspiration`, data).then(r => r.data),

  generateStory: (projectId: string) =>
    api.post<Story>(`/workflow/${projectId}/advance/story`).then(r => r.data),

  generateChapterOutline: (projectId: string) =>
    api.post<Story>(`/workflow/${projectId}/advance/chapter_outline`).then(r => r.data),

  generateChapterBody: (projectId: string) =>
    api.post<Story>(`/workflow/${projectId}/advance/chapter_body`).then(r => r.data),
}
