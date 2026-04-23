import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { analyticsApi } from '@/lib/api/analytics'

/**
 * Hook to get project statistics
 */
export function useProjectStats(projectId?: string) {
  return useQuery({
    queryKey: ['analytics', 'stats', projectId],
    queryFn: () => analyticsApi.getProjectStats(projectId!),
    enabled: !!projectId,
    refetchInterval: 5000, // Refresh every 5 seconds
  })
}

/**
 * Hook to get dashboard data
 */
export function useDashboardData(projectId?: string) {
  return useQuery({
    queryKey: ['analytics', 'dashboard', projectId],
    queryFn: () => analyticsApi.getDashboardData(projectId!),
    enabled: !!projectId,
    refetchInterval: 5000, // Refresh every 5 seconds
  })
}

/**
 * Hook to get video statistics
 */
export function useVideoStatistics(projectId?: string) {
  return useQuery({
    queryKey: ['analytics', 'videos', projectId],
    queryFn: () => analyticsApi.getVideoStatistics(projectId!),
    enabled: !!projectId,
  })
}

/**
 * Hook to export report
 */
export function useExportReport() {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: async (projectId: string) => {
      await analyticsApi.exportReport(projectId)
    },
    onSuccess: () => {
      // Invalidate queries to refresh data
      qc.invalidateQueries({ queryKey: ['analytics'] })
    },
  })
}

/**
 * Hook to analyze a video file
 */
export function useAnalyzeVideo() {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: async (fileId: string) => {
      return await analyticsApi.analyzeVideo(fileId)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['analytics'] })
      qc.invalidateQueries({ queryKey: ['files'] })
    },
  })
}
