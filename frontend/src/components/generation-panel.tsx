'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { Loader2, Sparkles, X, Minus, Maximize2, Pause, Play, Square, GripHorizontal } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import type { SSEEvent } from '@/hooks/use-event-stream'

interface GenerationPanelProps {
  visible: boolean
  events: SSEEvent[]
  isStreaming: boolean
  error: string | null
  onClose: () => void
  onPause?: () => void
  onContinue?: (message: string) => void
  onStop?: () => void
  onRestart?: () => void
}

const MIN_W = 320
const MIN_H = 200
const DEFAULT_W = 460
const DEFAULT_H = 520

export function GenerationPanel({
  visible, events, isStreaming, error, onClose,
  onPause, onContinue, onStop, onRestart,
}: GenerationPanelProps) {
  const [minimized, setMinimized] = useState(false)
  const [userInput, setUserInput] = useState('')
  const [isPaused, setIsPaused] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Drag state
  const [pos, setPos] = useState({ x: 0, y: 0 })
  const [initialized, setInitialized] = useState(false)
  const dragging = useRef(false)
  const dragOffset = useRef({ x: 0, y: 0 })
  const panelRef = useRef<HTMLDivElement>(null)

  // Resize state
  const [panelSize, setPanelSize] = useState({ w: DEFAULT_W, h: DEFAULT_H })
  const resizing = useRef(false)
  const resizeStart = useRef({ x: 0, y: 0, w: DEFAULT_W, h: DEFAULT_H })

  // Init position (bottom-right) on first visible
  useEffect(() => {
    if (visible && !initialized) {
      const vw = window.innerWidth
      const vh = window.innerHeight
      setPos({ x: vw - DEFAULT_W - 24, y: vh - DEFAULT_H - 24 })
      setInitialized(true)
    }
  }, [visible, initialized])

  // Reset when closed
  useEffect(() => {
    if (!visible) {
      setInitialized(false)
      setMinimized(false)
      setPanelSize({ w: DEFAULT_W, h: DEFAULT_H })
    }
  }, [visible])

  // Drag handlers
  const onDragStart = useCallback((e: React.MouseEvent) => {
    dragging.current = true
    dragOffset.current = { x: e.clientX - pos.x, y: e.clientY - pos.y }
    e.preventDefault()
  }, [pos])

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      if (!dragging.current) return
      const vw = window.innerWidth
      const vh = window.innerHeight
      const pw = panelSize.w
      const ph = minimized ? 48 : panelSize.h
      setPos({
        x: Math.max(0, Math.min(e.clientX - dragOffset.current.x, vw - pw)),
        y: Math.max(0, Math.min(e.clientY - dragOffset.current.y, vh - ph)),
      })
    }
    const onUp = () => { dragging.current = false }
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
    return () => {
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup', onUp)
    }
  }, [panelSize, minimized])

  // Resize handlers
  const onResizeStart = useCallback((e: React.MouseEvent) => {
    resizing.current = true
    resizeStart.current = { x: e.clientX, y: e.clientY, w: panelSize.w, h: panelSize.h }
    e.preventDefault()
    e.stopPropagation()
  }, [panelSize])

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      if (!resizing.current) return
      const dx = e.clientX - resizeStart.current.x
      const dy = e.clientY - resizeStart.current.y
      const vw = window.innerWidth
      const vh = window.innerHeight
      setPanelSize({
        w: Math.max(MIN_W, Math.min(resizeStart.current.w + dx, vw * 0.9)),
        h: Math.max(MIN_H, Math.min(resizeStart.current.h + dy, vh * 0.9)),
      })
    }
    const onUp = () => { resizing.current = false }
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
    return () => {
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup', onUp)
    }
  }, [])

  // Scroll
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [events, scrollToBottom])

  if (!visible) return null

  const contentText = events.filter(e => e.type === 'content').map(e => e.text).join('')
  const thinkingText = events.filter(e => e.type === 'thinking').map(e => e.text).join('\n')
  const errorText = events.filter(e => e.type === 'error').map(e => e.text).join('\n') || error

  const handleSend = () => {
    if (isPaused && userInput.trim()) {
      onContinue?.(userInput.trim())
      setUserInput('')
      setIsPaused(false)
    }
  }

  const handlePause = () => {
    setIsPaused(true)
    onPause?.()
  }

  const handleResume = () => {
    setIsPaused(false)
    onContinue?.('继续生成')
  }

  const headerH = 40
  const controlsH = 62
  const contentH = panelSize.h - headerH - controlsH

  return (
    <div
      ref={panelRef}
      className={cn(
        'fixed z-50 rounded-2xl border border-border bg-card/95 backdrop-blur-xl shadow-2xl transition-none select-none',
        minimized ? 'overflow-hidden' : 'flex flex-col',
      )}
      style={{
        left: pos.x,
        top: pos.y,
        width: panelSize.w,
        height: minimized ? headerH : panelSize.h,
      }}
    >
      {/* Header (drag handle) */}
      <div
        className="flex items-center justify-between px-4 py-2.5 border-b border-border/50 cursor-move shrink-0"
        onMouseDown={onDragStart}
      >
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-violet-400" />
          <span className="text-sm font-medium text-foreground/80">AI 生成</span>
          {isStreaming && (
            <Loader2 className="w-3.5 h-3.5 animate-spin text-sky-400" />
          )}
        </div>
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => setMinimized(!minimized)}>
            {minimized ? <Maximize2 className="w-3 h-3" /> : <Minus className="w-3 h-3" />}
          </Button>
          <Button variant="ghost" size="icon" className="h-6 w-6" onClick={onClose}>
            <X className="w-3 h-3" />
          </Button>
        </div>
      </div>

      {!minimized && (
        <>
          {/* Content */}
          <div className="flex-1 overflow-y-auto p-4 space-y-2 min-h-0" style={{ height: contentH }}>
            {thinkingText && (
              <div className="flex items-start gap-2 text-xs text-muted-foreground italic">
                <Loader2 className="w-3 h-3 animate-spin mt-0.5 shrink-0" />
                <span>{thinkingText}</span>
              </div>
            )}

            {contentText && (
              <div className="text-sm text-foreground/90 whitespace-pre-wrap leading-relaxed bg-muted/20 rounded-lg p-3 overflow-y-auto" style={{ maxHeight: contentH - 40 }}>
                {contentText}
              </div>
            )}

            {errorText && (
              <div className="flex items-start gap-2 text-xs text-rose-400 bg-rose-500/10 rounded-lg p-3">
                <span>⚠</span>
                <span>{errorText}</span>
              </div>
            )}

            {!isStreaming && !errorText && contentText && (
              <div className="text-xs text-emerald-400 text-center pt-2">✓ 生成完成</div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Controls */}
          <div className="border-t border-border/50 p-3 space-y-2 shrink-0">
            <div className="flex items-center gap-2">
              {isStreaming && (
                <>
                  {isPaused ? (
                    <Button variant="outline" size="sm" className="h-7 text-xs" onClick={handleResume}>
                      <Play className="w-3 h-3 mr-1" />继续
                    </Button>
                  ) : (
                    <Button variant="outline" size="sm" className="h-7 text-xs" onClick={handlePause}>
                      <Pause className="w-3 h-3 mr-1" />暂停
                    </Button>
                  )}
                  <Button variant="outline" size="sm" className="h-7 text-xs" onClick={onStop}>
                    <Square className="w-3 h-3 mr-1" />停止
                  </Button>
                </>
              )}
              {!isStreaming && contentText && onRestart && (
                <Button size="sm" className="h-7 text-xs" onClick={onRestart}>
                  重新生成
                </Button>
              )}
            </div>

            {isPaused && (
              <div className="flex gap-2">
                <input
                  className="flex-1 h-7 px-2 text-xs rounded-md bg-muted/30 border border-border text-foreground placeholder:text-muted-foreground"
                  placeholder="输入反馈指令..."
                  value={userInput}
                  onChange={(e) => setUserInput(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') handleSend() }}
                />
                <Button size="sm" className="h-7 text-xs" onClick={handleSend} disabled={!userInput.trim()}>
                  发送
                </Button>
              </div>
            )}
          </div>
        </>
      )}

      {/* Resize handle (bottom-right corner) */}
      {!minimized && (
        <div
          className="absolute bottom-0 right-0 w-5 h-5 cursor-se-resize flex items-center justify-center group"
          onMouseDown={onResizeStart}
        >
          <GripHorizontal className="w-3.5 h-3.5 text-muted-foreground/40 group-hover:text-muted-foreground/80 rotate-45 transition-colors" />
        </div>
      )}
    </div>
  )
}
