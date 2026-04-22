import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { generatorApi, type GeneratorInfo } from '@/lib/api/generators'

/**
 * Hook to list all available generators
 */
export function useGenerators() {
  return useQuery({
    queryKey: ['generators'],
    queryFn: generatorApi.list,
  })
}

/**
 * Hook to get a specific generator's info
 */
export function useGenerator(type: string) {
  return useQuery({
    queryKey: ['generators', type],
    queryFn: () => generatorApi.get(type),
    enabled: !!type,
  })
}

/**
 * Hook to trigger generation
 */
export function useGenerate() {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: ({ type, data }: { type: string; data: { project_id: string; parameters: Record<string, unknown> } }) =>
      generatorApi.generate(type, data),
    onSuccess: (_, { type, data }) => {
      // Invalidate related queries
      qc.invalidateQueries({ queryKey: ['tasks', data.project_id] })
      qc.invalidateQueries({ queryKey: ['workflow', data.project_id] })
      qc.invalidateQueries({ queryKey: ['generators', type] })
    },
  })
}

/**
 * Hook to generate script
 */
export function useGenerateScript() {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: ({ projectId, params }: { projectId: string; params: { topic: string; style?: string; duration?: string } }) =>
      generatorApi.generate('script', {
        project_id: projectId,
        parameters: params,
      }),
    onSuccess: (_, { projectId }) => {
      qc.invalidateQueries({ queryKey: ['tasks', projectId] })
      qc.invalidateQueries({ queryKey: ['workflow', projectId] })
    },
  })
}

/**
 * Hook to generate storyboard
 */
export function useGenerateStoryboard() {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: ({ projectId, params }: { projectId: string; params: { script_file_id?: string; panel_count?: number } }) =>
      generatorApi.generate('storyboard', {
        project_id: projectId,
        parameters: params,
      }),
    onSuccess: (_, { projectId }) => {
      qc.invalidateQueries({ queryKey: ['tasks', projectId] })
      qc.invalidateQueries({ queryKey: ['workflow', projectId] })
    },
  })
}

/**
 * Hook to generate images
 */
export function useGenerateImage() {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: ({ projectId, params }: { projectId: string; params: { prompt: string; negative_prompt?: string; storyboard_file_id?: string } }) =>
      generatorApi.generate('image', {
        project_id: projectId,
        parameters: params,
      }),
    onSuccess: (_, { projectId }) => {
      qc.invalidateQueries({ queryKey: ['tasks', projectId] })
      qc.invalidateQueries({ queryKey: ['workflow', projectId] })
    },
  })
}

/**
 * Hook to generate TTS audio
 */
export function useGenerateTTS() {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: ({ projectId, params }: { projectId: string; params: { text: string; voice?: string } }) =>
      generatorApi.generate('tts', {
        project_id: projectId,
        parameters: params,
      }),
    onSuccess: (_, { projectId }) => {
      qc.invalidateQueries({ queryKey: ['tasks', projectId] })
      qc.invalidateQueries({ queryKey: ['workflow', projectId] })
    },
  })
}

/**
 * Hook to generate BGM
 */
export function useGenerateBGM() {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: ({ projectId, params }: { projectId: string; params: { duration?: number; bpm?: number; mood?: string } }) =>
      generatorApi.generate('bgm', {
        project_id: projectId,
        parameters: params,
      }),
    onSuccess: (_, { projectId }) => {
      qc.invalidateQueries({ queryKey: ['tasks', projectId] })
      qc.invalidateQueries({ queryKey: ['workflow', projectId] })
    },
  })
}

/**
 * Hook to compose video
 */
export function useComposeVideo() {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: ({ projectId, params }: { projectId: string; params: { panels?: unknown[]; resolution?: [number, number]; fps?: number } }) =>
      generatorApi.generate('video_composer', {
        project_id: projectId,
        parameters: params,
      }),
    onSuccess: (_, { projectId }) => {
      qc.invalidateQueries({ queryKey: ['tasks', projectId] })
      qc.invalidateQueries({ queryKey: ['workflow', projectId] })
    },
  })
}
