import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { projectApi } from '@/lib/api/projects'
import type { ProjectCreate, ProjectUpdate } from '@/types/project'

// ─── Query Keys ───────────────────────────────────────────────────────

const QUERY_KEYS = {
  all: ['projects'] as const,
  mine: ['projects', 'mine'] as const,
  shared: ['projects', 'shared'] as const,
  recycle: ['projects', 'recycle'] as const,
  detail: (id: string) => ['projects', id] as const,
  shares: (id: string) => ['projects', id, 'shares'] as const,
}

// ─── Queries ──────────────────────────────────────────────────────────

export function useProjects() {
  return useQuery({
    queryKey: QUERY_KEYS.all,
    queryFn: projectApi.list,
  })
}

export function useMyProjects() {
  return useQuery({
    queryKey: QUERY_KEYS.mine,
    queryFn: projectApi.listMine,
  })
}

export function useSharedProjects() {
  return useQuery({
    queryKey: QUERY_KEYS.shared,
    queryFn: projectApi.listSharedWithMe,
  })
}

export function useRecycleBin() {
  return useQuery({
    queryKey: QUERY_KEYS.recycle,
    queryFn: projectApi.getRecycleBin,
  })
}

export function useProject(id: string) {
  return useQuery({
    queryKey: QUERY_KEYS.detail(id),
    queryFn: () => projectApi.get(id),
    enabled: !!id,
  })
}

// ─── Mutations ────────────────────────────────────────────────────────

export function useCreateProject() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: projectApi.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.all })
      qc.invalidateQueries({ queryKey: QUERY_KEYS.mine })
    },
  })
}

export function useUpdateProject(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: ProjectUpdate) => projectApi.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.all })
      qc.invalidateQueries({ queryKey: QUERY_KEYS.mine })
      qc.invalidateQueries({ queryKey: QUERY_KEYS.detail(id) })
    },
  })
}

export function useDeleteProject() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: projectApi.remove,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.all })
      qc.invalidateQueries({ queryKey: QUERY_KEYS.mine })
    },
  })
}

export function useRestoreProject() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: projectApi.restore,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.mine })
      qc.invalidateQueries({ queryKey: QUERY_KEYS.recycle })
    },
  })
}

export function usePermanentDeleteProject() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: projectApi.permanentDelete,
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEYS.recycle }),
  })
}

// ─── Sharing ──────────────────────────────────────────────────────────

export function useProjectShares(projectId: string) {
  return useQuery({
    queryKey: QUERY_KEYS.shares(projectId),
    queryFn: () => projectApi.listShares(projectId),
    enabled: !!projectId,
  })
}

export function useShareProject() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ projectId, data }: { projectId: string; data: { shared_with_user_id: string; permission: string } }) =>
      projectApi.share(projectId, data),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.shares(vars.projectId) })
    },
  })
}

export function useUnshareProject() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ projectId, userId }: { projectId: string; userId: string }) =>
      projectApi.unshare(projectId, userId),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.shares(vars.projectId) })
    },
  })
}
