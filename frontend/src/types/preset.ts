export interface Preset {
  id: string
  user_id: string | null
  name: string
  generator_type: string
  description: string | null
  parameters: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface PresetCreate {
  name: string
  generator_type: string
  description?: string | null
  parameters?: Record<string, unknown>
}

export interface PresetUpdate {
  name?: string
  description?: string | null
  parameters?: Record<string, unknown>
}
