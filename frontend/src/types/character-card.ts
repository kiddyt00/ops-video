export interface CharacterCard {
  id: string
  project_id: string
  name: string
  description: string
  front_view_url: string
  side_view_url: string
  back_view_url: string
  reference_images: string[] | null
  traits: Record<string, string> | null
  usage_count: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface CharacterCardCreate {
  name: string
  description: string
  front_view_url: string
  side_view_url: string
  back_view_url: string
}

export interface CharacterCardUpdate {
  name?: string
  description?: string
  front_view_url?: string
  side_view_url?: string
  back_view_url?: string
  is_active?: boolean
}
