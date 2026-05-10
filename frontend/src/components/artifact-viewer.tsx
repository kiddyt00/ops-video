'use client'

import { useState, useCallback, useEffect } from 'react'
import { Check, Copy, Download, FileText, Image as ImageIcon, Music, Film, FileJson, Loader2, X, Maximize2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { FileRecord } from '@/lib/api/files'
import type { TaskStage } from '@/types/task'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
const BACKEND_ORIGIN = API_BASE_URL.replace('/api/v1', '')

const STAGE_FILE_TYPE_MAP: Record<TaskStage, string> = {
  script: 'script',
  storyboard: 'storyboard',
  image: 'image',
  audio: 'audio',
  video: 'video',
}

const FILE_TYPE_ICONS: Record<string, typeof FileText> = {
  script: FileText,
  storyboard: FileJson,
  image: ImageIcon,
  audio: Music,
  video: Film,
}

interface ArtifactViewerProps {
  stage: TaskStage
  files: FileRecord[]
  onFilesChange?: () => void
}

export function ArtifactViewer({ stage, files, onFilesChange }: ArtifactViewerProps) {
  const fileType = STAGE_FILE_TYPE_MAP[stage]
  const stageFiles = files.filter(f => f.file_type === fileType)

  if (!stageFiles.length) return null

  const isImage = fileType === 'image'
  const isVideo = fileType === 'video'
  const isAudio = fileType === 'audio'

  return (
    <div className="mt-3">
      {isImage && (
        <div className="grid gap-2 grid-cols-2 md:grid-cols-3">
          {stageFiles.map(f => <ImageThumb key={f.id} file={f} onFilesChange={onFilesChange} />)}
        </div>
      )}
      {isVideo && (
        <div className="space-y-3">
          {stageFiles.map(f => <VideoPreview key={f.id} file={f} />)}
        </div>
      )}
      {isAudio && (
        <div className="space-y-2">
          {stageFiles.map(f => <AudioPreview key={f.id} file={f} />)}
        </div>
      )}
      {!isImage && !isVideo && !isAudio && (
        <div className="space-y-2">
          {stageFiles.map(f => <FilePreview key={f.id} file={f} />)}
        </div>
      )}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Image thumbnail with lightbox                                      */
/* ------------------------------------------------------------------ */

function ImageThumb({
  file,
  onFilesChange,
}: {
  file: FileRecord
  onFilesChange?: () => void
}) {
  const [lightbox, setLightbox] = useState(false)
  const [selecting, setSelecting] = useState(false)

  const imgSrc = `${API_BASE_URL}/files/${file.id}/download`

  const handleSelect = useCallback(async () => {
    if (!file.variant_group_id || selecting) return
    setSelecting(true)
    try {
      await fetch(`${API_BASE_URL}/variants/${file.variant_group_id}/select`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_id: file.id }),
      })
      onFilesChange?.()
    } catch {
      // ignore
    } finally {
      setSelecting(false)
    }
  }, [file, selecting, onFilesChange])

  return (
    <>
      <Card
        className={cn(
          'overflow-hidden transition-all cursor-pointer',
          file.is_selected
            ? 'ring-2 ring-primary shadow-md'
            : 'ring-1 ring-transparent hover:ring-border',
        )}
      >
        <div className="aspect-square bg-muted relative group">
          <img
            src={imgSrc}
            alt={file.file_path.split('/').pop()}
            className="w-full h-full object-cover"
            loading="lazy"
            onClick={() => setLightbox(true)}
          />
          <button
            onClick={(e) => { e.stopPropagation(); setLightbox(true) }}
            className="absolute top-2 right-2 p-1.5 rounded-md bg-black/50 text-white opacity-0 group-hover:opacity-100 transition-opacity"
          >
            <Maximize2 className="w-3.5 h-3.5" />
          </button>
          {file.is_selected && (
            <Badge className="absolute top-1 left-1 text-xs" variant="default">已选</Badge>
          )}
          {selecting && (
            <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
              <Loader2 className="w-5 h-5 text-white animate-spin" />
            </div>
          )}
        </div>
        <CardContent className="p-1.5 flex items-center justify-between">
          <p className="text-xs text-muted-foreground truncate">{file.file_path.split('/').pop()}</p>
          <div className="flex items-center gap-1 shrink-0">
            {file.is_selected && <Check className="w-3.5 h-3.5 text-primary" />}
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0"
              onClick={(e) => { e.stopPropagation(); handleSelect() }}
              title="选为当前使用"
            >
              <Check className="w-3 h-3" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Lightbox */}
      {lightbox && (
        <div
          className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center cursor-zoom-out"
          onClick={() => setLightbox(false)}
        >
          <button
            className="absolute top-4 right-4 p-2 rounded-full bg-white/10 text-white hover:bg-white/20"
            onClick={() => setLightbox(false)}
          >
            <X className="w-6 h-6" />
          </button>
          <img
            src={imgSrc}
            alt={file.file_path.split('/').pop()}
            className="max-w-[90vw] max-h-[90vh] object-contain"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}
    </>
  )
}

/* ------------------------------------------------------------------ */
/* Video preview with inline player                                   */
/* ------------------------------------------------------------------ */

function VideoPreview({ file }: { file: FileRecord }) {
  const videoSrc = `${API_BASE_URL}/files/${file.id}/download`
  const name = file.file_path.split('/').pop() ?? file.id

  return (
    <Card className="overflow-hidden">
      <div className="bg-black">
        <video
          controls
          src={videoSrc}
          className="w-full max-h-[400px] object-contain"
          preload="metadata"
        />
      </div>
      <CardContent className="p-2 flex items-center justify-between">
        <div className="flex items-center gap-2 min-w-0">
          <Film className="w-4 h-4 text-muted-foreground shrink-0" />
          <span className="text-xs truncate">{name}</span>
          {file.is_selected && <Badge variant="secondary" className="text-xs shrink-0">已选</Badge>}
        </div>
        <a
          href={videoSrc}
          download
          className="shrink-0 text-xs text-muted-foreground hover:text-foreground inline-flex items-center gap-1 px-2 py-1 h-7 rounded-md hover:bg-muted transition-colors"
        >
          <Download className="w-3.5 h-3.5" />
          下载
        </a>
      </CardContent>
    </Card>
  )
}

/* ------------------------------------------------------------------ */
/* Audio preview with inline player                                   */
/* ------------------------------------------------------------------ */

function AudioPreview({ file }: { file: FileRecord }) {
  const audioSrc = `${API_BASE_URL}/files/${file.id}/download`
  const name = file.file_path.split('/').pop() ?? file.id

  const params = file.generation_params as Record<string, unknown> | undefined
  const typeLabel = params?.type ? String(params.type).toUpperCase() : 'AUDIO'

  return (
    <Card>
      <CardContent className="pt-3 pb-3 space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 min-w-0">
            <Music className="w-4 h-4 text-muted-foreground shrink-0" />
            <Badge variant="secondary" className="text-xs shrink-0">{typeLabel}</Badge>
            <span className="text-xs truncate">{name}</span>
            {file.is_selected && <Badge variant="secondary" className="text-xs shrink-0">已选</Badge>}
          </div>
          <a
            href={audioSrc}
            download
            className="shrink-0 text-xs text-muted-foreground hover:text-foreground inline-flex items-center gap-1 px-2 py-1 h-7 rounded-md hover:bg-muted transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            下载
          </a>
        </div>
        <audio controls src={audioSrc} className="w-full h-8" preload="metadata" />
      </CardContent>
    </Card>
  )
}

/* ------------------------------------------------------------------ */
/* File preview for script / storyboard                               */
/* ------------------------------------------------------------------ */

function FilePreview({ file }: { file: FileRecord }) {
  const name = file.file_path.split('/').pop() ?? file.id

  if (file.file_type === 'script') return <ScriptPreview file={file} />
  if (file.file_type === 'storyboard') return <StoryboardPreview file={file} />

  const Icon = FILE_TYPE_ICONS[file.file_type] ?? FileText
  return (
    <Card>
      <CardContent className="pt-3 pb-3 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 min-w-0">
          <Icon className="w-4 h-4 text-muted-foreground shrink-0" />
          <span className="text-sm truncate">{name}</span>
          {file.is_selected && <Badge variant="secondary" className="text-xs shrink-0">已选</Badge>}
        </div>
        <a
          href={`${API_BASE_URL}/files/${file.id}/download`}
          download
          className="shrink-0 text-sm text-muted-foreground hover:text-foreground inline-flex items-center gap-1 px-2 py-1 h-7 rounded-md hover:bg-muted transition-colors"
        >
          <Download className="w-3.5 h-3.5" />
          下载
        </a>
      </CardContent>
    </Card>
  )
}

/* ------------------------------------------------------------------ */
/* Script inline preview (auto-load)                                  */
/* ------------------------------------------------------------------ */

function ScriptPreview({ file }: { file: FileRecord }) {
  const [content, setContent] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    setLoading(true)
    fetch(`${API_BASE_URL}/files/${file.id}/download`)
      .then(r => r.text())
      .then(setContent)
      .catch(() => setContent('加载失败'))
      .finally(() => setLoading(false))
  }, [file.id])

  const handleCopy = useCallback(async () => {
    if (!content) return
    await navigator.clipboard.writeText(content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }, [content])

  return (
    <Card>
      <CardContent className="pt-3 pb-3 space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 min-w-0">
            <FileText className="w-4 h-4 text-muted-foreground shrink-0" />
            <span className="text-sm font-medium truncate">{file.file_path.split('/').pop()}</span>
            {file.is_selected && <Badge variant="secondary" className="text-xs shrink-0">已选</Badge>}
          </div>
          <div className="flex gap-1 shrink-0">
            {content && (
              <Button variant="ghost" size="sm" onClick={handleCopy} className="text-xs">
                {copied ? <Check className="w-3.5 h-3.5 mr-1" /> : <Copy className="w-3.5 h-3.5 mr-1" />}
                {copied ? '已复制' : '复制'}
              </Button>
            )}
          </div>
        </div>
        {loading && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            加载中...
          </div>
        )}
        {!loading && content && (
          <pre className="text-xs bg-muted rounded-md p-3 overflow-auto max-h-60 whitespace-pre-wrap font-mono">
            {content}
          </pre>
        )}
      </CardContent>
    </Card>
  )
}

/* ------------------------------------------------------------------ */
/* Storyboard visual panel cards                                      */
/* ------------------------------------------------------------------ */

function StoryboardPreview({ file }: { file: FileRecord }) {
  const [data, setData] = useState<{ panels?: Array<Record<string, unknown>> } | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(false)

  useEffect(() => {
    setLoading(true)
    fetch(`${API_BASE_URL}/files/${file.id}/download`)
      .then(r => r.text())
      .then(text => {
        // Strip markdown code fences if present
        let clean = text.trim()
        if (clean.startsWith('```')) {
          clean = clean.replace(/^```\w*\n/, '').replace(/\n```\s*$/, '')
        }
        return JSON.parse(clean)
      })
      .then(setData)
      .catch(() => setError(true))
      .finally(() => setLoading(false))
  }, [file.id])

  const name = file.file_path.split('/').pop()

  return (
    <Card>
      <CardContent className="pt-3 pb-3 space-y-2">
        <div className="flex items-center gap-2">
          <FileJson className="w-4 h-4 text-muted-foreground shrink-0" />
          <span className="text-sm font-medium truncate">{name}</span>
          {file.is_selected && <Badge variant="secondary" className="text-xs shrink-0">已选</Badge>}
        </div>
        {loading && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            加载中...
          </div>
        )}
        {error && <p className="text-xs text-destructive">解析失败</p>}
        {data?.panels && (
          <div className="space-y-2">
            {data.panels.map((panel: Record<string, unknown>, i: number) => (
              <div key={i} className="border rounded-md p-2 text-xs space-y-1 bg-muted/30">
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="text-[10px] px-1 py-0">Panel {i + 1}</Badge>
                  {Boolean(panel.emotion) && (
                    <span className="text-muted-foreground italic">{String(panel.emotion)}</span>
                  )}
                </div>
                {Boolean(panel.scene_description) && (
                  <p className="leading-relaxed">{String(panel.scene_description).slice(0, 200)}</p>
                )}
                {Boolean(panel.camera_angle) && (
                  <p className="text-[10px] text-muted-foreground">🎬 {String(panel.camera_angle)}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
