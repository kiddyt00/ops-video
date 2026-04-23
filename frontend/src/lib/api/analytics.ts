import { api } from '@/lib/api'

export interface VideoStatistics {
  duration: number
  duration_formatted: string
  frame_count: number
  frame_rate: number
  resolution: string
  file_size: number
  file_size_formatted: string
  codec: string
  has_audio: boolean
}

export interface TaskStatistics {
  total_tasks: number
  completed_tasks: number
  failed_tasks: number
  pending_tasks: number
  running_tasks: number
  average_duration: number
}

export interface FileStatistics {
  total_files: number
  total_size: number
  total_size_formatted: string
  by_type: Record<string, number>
}

export interface StageStatistics {
  stage: string
  total_tasks: number
  completed_tasks: number
  failed_tasks: number
  success_rate: number
}

export interface ProjectStatistics {
  project_id: string
  task_stats: TaskStatistics
  file_stats: FileStatistics
  video_stats: VideoStatistics | null
  stage_stats: StageStatistics[]
  created_at: string
  updated_at: string
  last_activity: string | null
}

export interface DashboardMetric {
  title: string
  value: string
  change?: string
  trend?: 'up' | 'down' | 'neutral'
}

export interface DashboardResponse {
  project_id: string
  project_name: string
  metrics: DashboardMetric[]
  statistics: ProjectStatistics
  recent_tasks: Array<{
    id: string
    stage: string
    status: string
    generator_type: string
    created_at: string
    completed_at: string | null
    error_message: string | null
  }>
  files_by_type: Record<string, number>
}

export interface ExportReport {
  project_id: string
  project_name: string
  exported_at: string
  version: string
  statistics: ProjectStatistics
  tasks: Array<Record<string, unknown>>
  files: Array<Record<string, unknown>>
  variants: Array<Record<string, unknown>>
}

export const analyticsApi = {
  /**
   * Get project statistics
   */
  getProjectStats: (projectId: string) =>
    api.get<ProjectStatistics>(`/analytics/projects/${projectId}/stats`).then(r => r.data),

  /**
   * Get dashboard data
   */
  getDashboardData: (projectId: string) =>
    api.get<DashboardResponse>(`/analytics/projects/${projectId}/dashboard`).then(r => r.data),

  /**
   * Export project report as JSON
   */
  exportReport: async (projectId: string) => {
    const response = await api.get(`/analytics/projects/${projectId}/report`, {
      responseType: 'blob',
    })
    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `report_${projectId}.json`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
    return response.data
  },

  /**
   * Get video statistics for all video files
   */
  getVideoStatistics: (projectId: string) =>
    api.get(`/analytics/projects/${projectId}/videos`).then(r => r.data),

  /**
   * Analyze a video file
   */
  analyzeVideo: (fileId: string) =>
    api.post(`/analytics/files/${fileId}/analyze`).then(r => r.data),
}
