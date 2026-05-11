import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { characterCardApi } from '@/lib/api/character-cards'
import type { CharacterCardCreate, CharacterCardUpdate } from '@/types/character-card'

// ─── Query Keys ───────────────────────────────────────────────────────

const QUERY_KEYS = {
  list: (projectId: string) => ['character-cards', projectId] as const,
}

// ─── Queries ──────────────────────────────────────────────────────────

export function useCharacterCards(projectId: string) {
  return useQuery({
    queryKey: QUERY_KEYS.list(projectId),
    queryFn: () => characterCardApi.list(projectId),
    enabled: !!projectId,
  })
}

// ─── Mutations ────────────────────────────────────────────────────────

export function useCreateCharacterCard(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: CharacterCardCreate) => characterCardApi.create(projectId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.list(projectId) })
    },
  })
}

export function useUpdateCharacterCard(projectId: string, cardId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: CharacterCardUpdate) => characterCardApi.update(projectId, cardId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.list(projectId) })
    },
  })
}

export function useDeleteCharacterCard(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ cardId }: { cardId: string }) => characterCardApi.remove(projectId, cardId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.list(projectId) })
    },
  })
}
