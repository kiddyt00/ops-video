/** Provider info returned by the providers API */
export interface ProviderInfo {
  id: string
  name: string
  provider: string
  model_name: string
  is_active: boolean
  is_builtin: boolean
}

/** Active provider info */
export interface ActiveProvider {
  id: string
  name: string
  provider: string
  model_name: string
  category: string
}
