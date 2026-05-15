export type ChapterStatus = 'pending' | 'running' | 'completed' | 'failed'

export interface Chapter {
  id: string
  project_id: string
  chapter_number: number
  name: string
  description: string | null
  body_text: string | null
  status: ChapterStatus
  thumbnail_url: string | null
  video_file_id: string | null
  current_stage: string | null
  created_at: string
  updated_at: string
}

export interface ChapterCreate {
  name: string
  description?: string | null
}

export interface ChapterUpdate {
  name?: string
  description?: string | null
}
