export type FileType = 'image' | 'audio' | 'video' | 'script' | 'storyboard' | 'other'

export interface File {
  id: string
  project_id: string
  variant_group_id: string | null
  task_id: string | null
  file_path: string
  file_type: FileType
  file_size: number | null
  generation_params: Record<string, unknown>
  metadata: Record<string, unknown>
  version: string
  parent_file_id: string | null
  is_selected: boolean
  selected_at: string | null
  created_at: string
  updated_at: string
}

export interface VariantGroup {
  id: string
  project_id: string
  task_id: string
  stage: string
  selected_file_id: string | null
  parameters: Record<string, unknown>
  files: File[]
  created_at: string
  updated_at: string
}
