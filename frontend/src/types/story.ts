/* ------------------------------------------------------------------ */
/* Story types — Phase 17.1.6                                          */
/* ------------------------------------------------------------------ */

export interface ChapterOutlineItem {
  chapter_number: number
  title: string
  summary: string
  estimated_duration: number  // in seconds
}

export interface Story {
  id: string
  project_id: string
  logline: string
  synopsis: string
  worldbuilding: string
  characters: string
  chapter_outline: ChapterOutlineItem[]
  created_at: string
  updated_at: string
}

export interface StoryCreate {
  logline?: string
  synopsis?: string
  worldbuilding?: string
  characters?: string
  chapter_outline?: ChapterOutlineItem[]
}

export interface StoryUpdate {
  logline?: string
  synopsis?: string
  worldbuilding?: string
  characters?: string
  chapter_outline?: ChapterOutlineItem[]
}

export interface InspirationRequest {
  inspiration: string
}
