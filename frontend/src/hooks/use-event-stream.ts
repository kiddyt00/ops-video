'use client'

import { useState, useRef, useCallback, useEffect } from 'react'

export interface SSEEvent {
  type: 'thinking' | 'content' | 'complete' | 'error'
  text: string
  result?: Record<string, unknown>
}

interface UseEventStreamReturn {
  events: SSEEvent[]
  isStreaming: boolean
  error: string | null
  startStream: (url: string, body: Record<string, unknown>) => void
  stopStream: () => void
  clear: () => void
}

export function useEventStream(): UseEventStreamReturn {
  const [events, setEvents] = useState<SSEEvent[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const stopStream = useCallback(() => {
    abortRef.current?.abort()
    abortRef.current = null
    setIsStreaming(false)
  }, [])

  const clear = useCallback(() => {
    setEvents([])
    setError(null)
  }, [])

  const startStream = useCallback(async (url: string, body: Record<string, unknown>) => {
    stopStream()
    setEvents([])
    setError(null)
    setIsStreaming(true)

    const controller = new AbortController()
    abortRef.current = controller

    try {
      const token = localStorage.getItem('ops-video-tokens')
      const accessToken = token ? JSON.parse(token).access_token : null
      const headers: Record<string, string> = { 'Content-Type': 'application/json' }
      if (accessToken) headers['Authorization'] = `Bearer ${accessToken}`

      const resp = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
        signal: controller.signal,
      })

      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({ detail: `HTTP ${resp.status}` }))
        throw new Error(errData.detail || 'Stream request failed')
      }

      const reader = resp.body?.getReader()
      if (!reader) throw new Error('No response body')

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        let currentEvent = ''
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEvent = line.slice(7).trim()
          } else if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              setEvents(prev => [...prev, { type: currentEvent as SSEEvent['type'], text: data.text || '', result: data.result }])
            } catch {
              // ignore parse errors for partial lines
            }
          }
        }
      }
    } catch (err) {
      if ((err as Error).name === 'AbortError') return
      setError((err as Error).message || 'Stream failed')
    } finally {
      setIsStreaming(false)
      abortRef.current = null
    }
  }, [stopStream])

  // Cleanup on unmount
  useEffect(() => {
    return () => stopStream()
  }, [stopStream])

  return { events, isStreaming, error, startStream, stopStream, clear }
}
