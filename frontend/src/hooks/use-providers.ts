import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { providerApi } from '@/lib/api/providers'
import { api } from '@/lib/api'
import type { ProjectUpdate } from '@/types/project'

export function useImageProviders() {
  return useQuery({
    queryKey: ['providers', 'text2img'],
    queryFn: () => providerApi.list('text2img'),
  })
}

export function useActiveImageProvider() {
  return useQuery({
    queryKey: ['providers', 'text2img', 'active'],
    queryFn: () => providerApi.getActive('text2img'),
  })
}

export function useUpdateProjectSettings(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: ProjectUpdate) =>
      api.put(`/projects/${projectId}`, data).then(r => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['project', projectId] })
    },
  })
}
