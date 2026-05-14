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

  sync: (projectId: string) =>
    api.post<{ created: number; skipped: number; cards: CharacterCard[] }>(
      `/projects/${projectId}/character-cards/sync`
    ).then(r => r.data),

  generateThreeView: (projectId: string, cardId: string, styleTags?: string[], strict?: boolean) =>
    api.post<{
      card_id: string; card_name?: string;
      front_view_url?: string; side_view_url?: string; back_view_url?: string;
    }>(`/projects/${projectId}/character-cards/${cardId}/three-view`, {
      style_tags: styleTags ?? [],
      strict: strict ?? false,
    }).then(r => r.data),

  generateAllThreeViews: (projectId: string, styleTags?: string[], strict?: boolean) =>
    api.post<{
      total: number; success: number; failed: number; skipped: number; details: any[];
    }>(`/projects/${projectId}/character-cards/generate-all-three-views`, {
      style_tags: styleTags ?? [],
      strict: strict ?? false,
    }).then(r => r.data),
}
