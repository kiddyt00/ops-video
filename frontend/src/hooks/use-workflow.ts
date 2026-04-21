import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { workflowApi } from '@/lib/api/workflow'

export function useWorkflowStatus(projectId: string) {
  return useQuery({
    queryKey: ['workflow', projectId, 'status'],
    queryFn: () => workflowApi.getStatus(projectId),
    enabled: !!projectId,
  })
}

export function useWorkflowHistory(projectId: string) {
  return useQuery({
    queryKey: ['workflow', projectId, 'history'],
    queryFn: () => workflowApi.getHistory(projectId),
    enabled: !!projectId,
  })
}

export function useAdvanceWorkflow() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ projectId, params }: { projectId: string; params?: { generator_type?: string; parameters?: Record<string, unknown> } }) =>
      workflowApi.advance(projectId, params?.generator_type ? params : undefined),
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: ['workflow', vars.projectId] })
      qc.invalidateQueries({ queryKey: ['tasks', vars.projectId] })
    },
  })
}

export function useRollbackWorkflow() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ projectId, stage, fileId }: { projectId: string; stage: string; fileId?: string }) =>
      workflowApi.rollback(projectId, stage, fileId),
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: ['workflow', vars.projectId] })
      qc.invalidateQueries({ queryKey: ['tasks', vars.projectId] })
    },
  })
}

export function useFileLineage(fileId: string) {
  return useQuery({
    queryKey: ['lineage', fileId],
    queryFn: () => workflowApi.getLineage(fileId),
    enabled: !!fileId,
  })
}

export function useFileVersions(fileId: string) {
  return useQuery({
    queryKey: ['versions', fileId],
    queryFn: () => workflowApi.getVersions(fileId),
    enabled: !!fileId,
  })
}
