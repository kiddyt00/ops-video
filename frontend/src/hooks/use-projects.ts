import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { projectApi } from '@/lib/api/projects'
import type { ProjectCreate, ProjectUpdate } from '@/types/project'

export function useProjects() {
  return useQuery({
    queryKey: ['projects'],
    queryFn: projectApi.list,
  })
}

export function useProject(id: string) {
  return useQuery({
    queryKey: ['projects', id],
    queryFn: () => projectApi.get(id),
    enabled: !!id,
  })
}

export function useCreateProject() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: projectApi.create,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['projects'] }),
  })
}

export function useUpdateProject(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: ProjectUpdate) => projectApi.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['projects'] })
      qc.invalidateQueries({ queryKey: ['projects', id] })
    },
  })
}

export function useDeleteProject() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: projectApi.remove,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['projects'] }),
  })
}
