import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { storyApi } from '@/lib/api/stories'
import type { StoryCreate, StoryUpdate, InspirationRequest } from '@/types/story'

// ─── Query Keys ───────────────────────────────────────────────────────

const QUERY_KEYS = {
  story: (projectId: string) => ['story', projectId] as const,
}

// ─── Queries ──────────────────────────────────────────────────────────

export function useStory(projectId: string) {
  return useQuery({
    queryKey: QUERY_KEYS.story(projectId),
    queryFn: () => storyApi.get(projectId),
    enabled: !!projectId,
    retry: false,
  })
}

// ─── Mutations ────────────────────────────────────────────────────────

export function useCreateStory(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: StoryCreate) => storyApi.create(projectId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.story(projectId) })
    },
  })
}

export function useUpdateStory(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: StoryUpdate) => storyApi.update(projectId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.story(projectId) })
    },
  })
}

export function useDeleteStory(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => storyApi.remove(projectId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.story(projectId) })
    },
  })
}

export function useGenerateInspiration(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: InspirationRequest) => storyApi.generateInspiration(projectId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.story(projectId) })
    },
  })
}

export function useGenerateStory(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => storyApi.generateStory(projectId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.story(projectId) })
    },
  })
}

export function useGenerateChapterOutline(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => storyApi.generateChapterOutline(projectId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.story(projectId) })
    },
  })
}
