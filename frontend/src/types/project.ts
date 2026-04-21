export interface Project {
  id: string
  name: string
  description: string | null
  settings: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export interface ProjectCreate {
  name: string
  description?: string | null
  settings?: Record<string, unknown> | null
}

export interface ProjectUpdate {
  name?: string
  description?: string | null
  settings?: Record<string, unknown> | null
}
