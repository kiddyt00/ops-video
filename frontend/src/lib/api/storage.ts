import { api } from '@/lib/api'

// ─── Types ────────────────────────────────────────────────────────────

export interface StorageProvider {
  id: string
  name: string
  provider_type: string
  access_key: string
  secret_key: string
  bucket: string
  endpoint: string | null
  region: string | null
  path_prefix: string | null
  extra_config: Record<string, unknown> | null
  is_active: boolean
  is_default: boolean
  last_tested_at: string | null
  last_test_status: string | null
  last_test_error: string | null
  created_at: string
  updated_at: string
}

export interface StorageProviderForm {
  name: string
  provider_type: string
  access_key: string
  secret_key: string
  bucket: string
  endpoint?: string
  region?: string
  path_prefix?: string
  extra_config?: Record<string, unknown>
}

export interface StorageTestResult {
  success: boolean
  message: string
  latency_ms: number | null
  provider_name: string | null
  bucket: string | null
}

// ─── API functions ────────────────────────────────────────────────────

export const storageApi = {
  list: () =>
    api.get<StorageProvider[]>('/storage-providers').then(r => r.data),

  get: (id: string) =>
    api.get<StorageProvider>(`/storage-providers/${id}`).then(r => r.data),

  create: (data: StorageProviderForm) =>
    api.post<StorageProvider>('/storage-providers', data).then(r => r.data),

  update: (id: string, data: Partial<StorageProviderForm>) =>
    api.put<StorageProvider>(`/storage-providers/${id}`, data).then(r => r.data),

  del: (id: string) =>
    api.delete(`/storage-providers/${id}`),

  test: (id: string) =>
    api.post<StorageTestResult>(`/storage-providers/${id}/test`).then(r => r.data),

  activate: (id: string) =>
    api.post<StorageProvider>(`/storage-providers/${id}/activate`).then(r => r.data),
}
