import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { taskApi } from '@/lib/api/tasks'
import type { TaskCreate, TaskStatusUpdate } from '@/types/task'

export function useTasks(projectId?: string, opts?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ['tasks', projectId],
    queryFn: () => taskApi.list(projectId),
    enabled: (opts?.enabled ?? true) && !!projectId,
  })
}

export function useTask(id: string) {
  return useQuery({
    queryKey: ['tasks', id],
    queryFn: () => taskApi.get(id),
    enabled: !!id,
  })
}

export function useCreateTask() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: taskApi.create,
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: ['tasks', vars.project_id] })
      qc.invalidateQueries({ queryKey: ['workflow', vars.project_id] })
    },
  })
}

export function useRunTask() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: taskApi.run,
    onSuccess: (_, id) => qc.invalidateQueries({ queryKey: ['tasks', id] }),
  })
}

export function useUpdateTaskStatus(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: TaskStatusUpdate) => taskApi.updateStatus(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tasks', id] }),
  })
}

export function useDeleteTask() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: taskApi.remove,
    onSuccess: (_, id) => qc.invalidateQueries({ queryKey: ['tasks'] }),
  })
}
