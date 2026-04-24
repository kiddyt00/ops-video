'use client'

import { useState, useCallback } from 'react'
import { Check, Copy, Download, FileText, Image as ImageIcon, Music, Film, FileJson, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { FileRecord } from '@/lib/api/files'
import type { TaskStage } from '@/types/task'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

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

  return (
    <div className="mt-3">
      {isImage ? (
        <div className="grid gap-2 grid-cols-2 md:grid-cols-3">
          {stageFiles.map(f => <ImageThumb key={f.id} file={f} onFilesChange={onFilesChange} />)}
        </div>
      ) : (
        <div className="space-y-2">
          {stageFiles.map(f => <FilePreview key={f.id} file={f} />)}
        </div>
      )}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Image thumbnail with variant selection                              */
/* ------------------------------------------------------------------ */

function ImageThumb({
  file,
  onFilesChange,
}: {
  file: FileRecord
  onFilesChange?: () => void
}) {
  const [loaded, setLoaded] = useState(false)
  const [selecting, setSelecting] = useState(false)

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
      // ignore — user can retry
    } finally {
      setSelecting(false)
    }
  }, [file, selecting, onFilesChange])

  return (
    <Card
      className={cn(
        'overflow-hidden transition-all',
        file.is_selected
          ? 'ring-2 ring-primary shadow-md'
          : 'ring-1 ring-transparent hover:ring-border',
      )}
      onClick={handleSelect}
    >
      <div className="aspect-square bg-muted relative cursor-pointer">
        {loaded ? (
          <img
            src={`${API_BASE_URL}/files/${file.id}/download`}
            alt={file.file_path.split('/').pop()}
            className="w-full h-full object-cover"
            onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
          />
        ) : (
          <button
            onClick={(e) => { e.stopPropagation(); setLoaded(true) }}
            className="w-full h-full flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors"
          >
            <ImageIcon className="w-6 h-6" />
          </button>
        )}
        {file.is_selected && (
          <Badge className="absolute top-1 right-1 text-xs" variant="default">已选</Badge>
        )}
        {selecting && (
          <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
            <Loader2 className="w-5 h-5 text-white animate-spin" />
          </div>
        )}
      </div>
      <CardContent className="p-1.5 flex items-center justify-between">
        <p className="text-xs text-muted-foreground truncate">{file.file_path.split('/').pop()}</p>
        {file.is_selected && <Check className="w-3.5 h-3.5 text-primary shrink-0 ml-1" />}
      </CardContent>
    </Card>
  )
}

/* ------------------------------------------------------------------ */
/* File preview for script / storyboard / audio / video                */
/* ------------------------------------------------------------------ */

function FilePreview({ file }: { file: FileRecord }) {
  const Icon = FILE_TYPE_ICONS[file.file_type] ?? FileText
  const name = file.file_path.split('/').pop() ?? file.id

  if (file.file_type === 'script') {
    return <ScriptPreview file={file} />
  }
  if (file.file_type === 'storyboard') {
    return <StoryboardPreview file={file} />
  }

  return (
    <Card>
      <CardContent className="pt-3 pb-3 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 min-w-0">
          <Icon className="w-4 h-4 text-muted-foreground shrink-0" />
          <span className="text-sm truncate">{name}</span>
          {file.is_selected && (
            <Badge variant="secondary" className="text-xs shrink-0">已选</Badge>
          )}
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
/* Script inline preview                                               */
/* ------------------------------------------------------------------ */

function ScriptPreview({ file }: { file: FileRecord }) {
  const [content, setContent] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [copied, setCopied] = useState(false)

  const loadContent = useCallback(async () => {
    setLoading(true)
    try {
      const resp = await fetch(`${API_BASE_URL}/files/${file.id}/download`)
      const text = await resp.text()
      setContent(text)
    } catch {
      setContent('# 加载失败\n无法获取脚本内容')
    } finally {
      setLoading(false)
    }
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
            {file.is_selected && (
              <Badge variant="secondary" className="text-xs shrink-0">已选</Badge>
            )}
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
        {!loading && !content && (
          <Button variant="outline" size="sm" onClick={loadContent} className="text-xs">
            加载预览
          </Button>
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
/* Storyboard inline preview                                           */
/* ------------------------------------------------------------------ */

function StoryboardPreview({ file }: { file: FileRecord }) {
  const [content, setContent] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [copied, setCopied] = useState(false)

  const loadContent = useCallback(async () => {
    setLoading(true)
    try {
      const resp = await fetch(`${API_BASE_URL}/files/${file.id}/download`)
      const text = await resp.text()
      // Pretty-print JSON
      try {
        const parsed = JSON.parse(text)
        setContent(JSON.stringify(parsed, null, 2))
      } catch {
        setContent(text)
      }
    } catch {
      setContent('# 加载失败\n无法获取分镜内容')
    } finally {
      setLoading(false)
    }
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
            <FileJson className="w-4 h-4 text-muted-foreground shrink-0" />
            <span className="text-sm font-medium truncate">{file.file_path.split('/').pop()}</span>
            {file.is_selected && (
              <Badge variant="secondary" className="text-xs shrink-0">已选</Badge>
            )}
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
        {!loading && !content && (
          <Button variant="outline" size="sm" onClick={loadContent} className="text-xs">
            加载预览
          </Button>
        )}
        {!loading && content && (
          <pre className="text-xs bg-muted rounded-md p-3 overflow-auto max-h-80 whitespace-pre-wrap font-mono">
            {content}
          </pre>
        )}
      </CardContent>
    </Card>
  )
}
