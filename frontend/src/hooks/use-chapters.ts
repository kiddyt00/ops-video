import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { chapterApi } from '@/lib/api/chapters'
import type { ChapterCreate } from '@/types/chapter'

const KEYS = {
  list: (pid: string) => ['chapters', pid] as const,
  detail: (pid: string, cid: string) => ['chapters', pid, cid] as const,
}

export function useChapters(projectId: string) {
  return useQuery({
    queryKey: KEYS.list(projectId),
    queryFn: () => chapterApi.list(projectId),
    enabled: !!projectId,
  })
}

export function useChapter(projectId: string, chapterId: string) {
  return useQuery({
    queryKey: KEYS.detail(projectId, chapterId),
    queryFn: () => chapterApi.get(projectId, chapterId),
    enabled: !!(projectId && chapterId),
  })
}

export function useSyncChapters(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => chapterApi.syncFromStory(projectId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEYS.list(projectId) })
    },
  })
}

export function useCreateChapter(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: ChapterCreate) => chapterApi.create(projectId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEYS.list(projectId) })
    },
  })
}

export function useDeleteChapter(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ chapterId }: { chapterId: string }) =>
      chapterApi.remove(projectId, chapterId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEYS.list(projectId) })
    },
  })
}
