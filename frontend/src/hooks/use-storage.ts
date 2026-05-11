import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { storageApi } from '@/lib/api/storage'
import type { StorageProviderForm } from '@/lib/api/storage'

// ─── Query Keys ───────────────────────────────────────────────────────

const QUERY_KEYS = {
  all: ['storage-providers'] as const,
  detail: (id: string) => ['storage-providers', id] as const,
}

// ─── Queries ──────────────────────────────────────────────────────────

export function useStorageProviders() {
  return useQuery({
    queryKey: QUERY_KEYS.all,
    queryFn: storageApi.list,
  })
}

export function useStorageProvider(id: string) {
  return useQuery({
    queryKey: QUERY_KEYS.detail(id),
    queryFn: () => storageApi.get(id),
    enabled: !!id,
  })
}

// ─── Mutations ────────────────────────────────────────────────────────

export function useCreateStorageProvider() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: StorageProviderForm) => storageApi.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.all })
    },
  })
}

export function useUpdateStorageProvider(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<StorageProviderForm>) => storageApi.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.all })
      qc.invalidateQueries({ queryKey: QUERY_KEYS.detail(id) })
    },
  })
}

export function useDeleteStorageProvider() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: storageApi.del,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.all })
    },
  })
}

export function useTestStorageProvider() {
  return useMutation({
    mutationFn: storageApi.test,
  })
}

export function useActivateStorageProvider() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: storageApi.activate,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.all })
    },
  })
}
