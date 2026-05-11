import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { chapterApi } from '@/lib/api/chapters'
import type { ChapterCreate, ChapterUpdate } from '@/types/chapter'

// Query Keys
const QUERY_KEYS = {
  list: (projectId: string) => ['chapters', projectId] as const,
  detail: (projectId: string, chapterId: string) => ['chapters', projectId, chapterId] as const,
}

// Queries
export function useChapters(projectId: string) {
  return useQuery({
    queryKey: QUERY_KEYS.list(projectId),
    queryFn: () => chapterApi.list(projectId),
    enabled: !!projectId,
  })
}

export function useChapter(projectId: string, chapterId: string) {
  return useQuery({
    queryKey: QUERY_KEYS.detail(projectId, chapterId),
    queryFn: () => chapterApi.get(projectId, chapterId),
    enabled: !!(projectId && chapterId),
  })
}

// Mutations
export function useCreateChapter(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: ChapterCreate) => chapterApi.create(projectId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.list(projectId) })
    },
  })
}

export function useUpdateChapter(projectId: string, chapterId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: ChapterUpdate) => chapterApi.update(projectId, chapterId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.list(projectId) })
      qc.invalidateQueries({ queryKey: QUERY_KEYS.detail(projectId, chapterId) })
    },
  })
}

export function useDeleteChapter(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ chapterId }: { chapterId: string }) =>
      chapterApi.remove(projectId, chapterId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.list(projectId) })
    },
  })
}
