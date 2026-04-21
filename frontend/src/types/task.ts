export type TaskStage = 'script' | 'storyboard' | 'image' | 'audio' | 'video'

export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'

export interface Task {
  id: string
  project_id: string
  stage: TaskStage
  status: TaskStatus
  generator_type: string
  parameters: Record<string, unknown>
  output_file_ids: string[]
  parent_task_id: string | null
  started_at: string | null
  completed_at: string | null
  error_message: string | null
  created_at: string
  updated_at: string
}

export interface TaskCreate {
  project_id: string
  stage: TaskStage
  generator_type: string
  parameters?: Record<string, unknown>
  parent_task_ids?: string[]
}

export interface TaskStatusUpdate {
  status: TaskStatus
  reason?: string
}
