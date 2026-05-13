'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { Loader2, Sparkles, X, Minus, Maximize2, Pause, Play, Square } from 'lucide-react'
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

export function GenerationPanel({
  visible, events, isStreaming, error, onClose,
  onPause, onContinue, onStop, onRestart,
}: GenerationPanelProps) {
  const [minimized, setMinimized] = useState(false)
  const [userInput, setUserInput] = useState('')
  const [isPaused, setIsPaused] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

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

  return (
    <div className={cn(
      'fixed bottom-4 right-4 z-50 w-[420px] rounded-2xl border border-white/10 bg-[#0d0d1a]/95 backdrop-blur-xl shadow-2xl transition-all duration-300',
      minimized ? 'h-12 overflow-hidden' : 'h-[500px]',
    )}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-white/5 cursor-move">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-violet-400" />
          <span className="text-sm font-medium text-white/80">AI 生成</span>
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
          <div className="flex-1 h-[340px] overflow-y-auto p-4 space-y-2">
            {thinkingText && (
              <div className="flex items-start gap-2 text-xs text-zinc-400 italic">
                <Loader2 className="w-3 h-3 animate-spin mt-0.5 shrink-0" />
                <span>{thinkingText}</span>
              </div>
            )}

            {contentText && (
              <div className="text-sm text-white/90 whitespace-pre-wrap leading-relaxed bg-white/[0.02] rounded-lg p-3 max-h-[260px] overflow-y-auto">
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
          <div className="border-t border-white/5 p-3 space-y-2">
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

            {/* Feedback input (when paused) */}
            {isPaused && (
              <div className="flex gap-2">
                <input
                  className="flex-1 h-7 px-2 text-xs rounded-md bg-white/5 border border-white/10 text-white placeholder:text-zinc-600"
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
    </div>
  )
}
