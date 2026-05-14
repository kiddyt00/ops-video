import { useMutation, useQueryClient } from '@tanstack/react-query'
import { characterCardApi } from '@/lib/api/character-cards'

const LIST_KEY = (projectId: string) => ['character-cards', projectId]

export function useSyncCharacterCards(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => characterCardApi.sync(projectId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: LIST_KEY(projectId) })
    },
  })
}

export function useGenerateThreeView(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ cardId, style_tags, strict }: {
      cardId: string; style_tags?: string[]; strict?: boolean
    }) => characterCardApi.generateThreeView(projectId, cardId, style_tags, strict),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: LIST_KEY(projectId) })
    },
  })
}

export function useGenerateAllThreeViews(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ style_tags, strict }: { style_tags?: string[]; strict?: boolean }) =>
      characterCardApi.generateAllThreeViews(projectId, style_tags, strict),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: LIST_KEY(projectId) })
    },
  })
}
