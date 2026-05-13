import { api } from '@/lib/api'
import type { ProviderInfo, ActiveProvider } from '@/types/provider'

export const providerApi = {
  list: (category?: string) =>
    api.get<ProviderInfo[]>('/providers', {
      params: { category: category || 'text2img' },
    }).then(r => r.data),

  getActive: (category?: string) =>
    api.get<ActiveProvider | null>('/providers/active', {
      params: { category: category || 'text2img' },
    }).then(r => r.data),
}
