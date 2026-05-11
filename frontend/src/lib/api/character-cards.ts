import { api } from '@/lib/api'
import type { CharacterCard, CharacterCardCreate, CharacterCardUpdate } from '@/types/character-card'

export const characterCardApi = {
  list: (projectId: string) =>
    api.get<CharacterCard[]>(`/projects/${projectId}/character-cards`).then(r => r.data),

  create: (projectId: string, data: CharacterCardCreate) =>
    api.post<CharacterCard>(`/projects/${projectId}/character-cards`, data).then(r => r.data),

  update: (projectId: string, cardId: string, data: CharacterCardUpdate) =>
    api.put<CharacterCard>(`/projects/${projectId}/character-cards/${cardId}`, data).then(r => r.data),

  remove: (projectId: string, cardId: string) =>
    api.delete(`/projects/${projectId}/character-cards/${cardId}`),
}
