export interface CharacterCard {
  id: string
  project_id: string
  name: string
  description: string
  front_image_url: string
  side_image_url: string
  back_image_url: string
  created_at: string
  updated_at: string
}

export interface CharacterCardCreate {
  name: string
  description: string
  front_image_url: string
  side_image_url: string
  back_image_url: string
}

export interface CharacterCardUpdate {
  name?: string
  description?: string
  front_image_url?: string
  side_image_url?: string
  back_image_url?: string
}
