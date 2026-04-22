import { useQuery, useQueryClient } from '@tanstack/react-query'
import { fileApi, variantApi } from '@/lib/api/files'

export function useFiles(projectId?: string) {
  return useQuery({
    queryKey: ['files', projectId],
    queryFn: () => fileApi.list(projectId),
    enabled: !!projectId,
  })
}

export function useFile(id?: string) {
  return useQuery({
    queryKey: ['files', id],
    queryFn: () => fileApi.get(id!),
    enabled: !!id,
  })
}

export function useFileUrl(id?: string) {
  return useQuery({
    queryKey: ['file-url', id],
    queryFn: () => fileApi.getUrl(id!),
    enabled: !!id,
  })
}

export function useSelectVariant() {
  const qc = useQueryClient()
  return {
    mutateAsync: async (variantGroupId: string, fileId: string) => {
      const result = await variantApi.select(variantGroupId, fileId)
      qc.invalidateQueries({ queryKey: ['files'] })
      qc.invalidateQueries({ queryKey: ['workflow'] })
      return result
    },
  }
}
