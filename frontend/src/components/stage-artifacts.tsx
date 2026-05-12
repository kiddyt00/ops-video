'use client'

import { useState, useEffect } from 'react'
import { Download, Trash2, FileText, FileJson, Image as ImageIcon, Music, Film, Loader2, Maximize2, X, Check, Copy, ChevronDown, ChevronRight } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import type { FileRecord } from '@/lib/api/files'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api/v1'

/* ------------------------------------------------------------------ */
/* Image gallery with lightbox + delete                                */
/* ------------------------------------------------------------------ */

function ImageGallery({ files, onDelete }: { files: FileRecord[]; onDelete: (id: string) => void }) {
  const [lightbox, setLightbox] = useState<string | null>(null)

  return (
    <div className="space-y-2">
      <p className="text-[11px] text-zinc-500 uppercase tracking-wider px-1">生成图片 · {files.length} 张</p>
      <div className="grid grid-cols-2 gap-2">
        {files.map(f => {
          const src = `${API_BASE}/files/${f.id}/download`
          return (
            <div key={f.id} className="aspect-[4/5] rounded-xl overflow-hidden bg-zinc-900 ring-1 ring-white/5 hover:ring-violet-500/40 transition-all group relative">
              <img src={src} alt="" className="w-full h-full object-cover cursor-pointer" onClick={() => setLightbox(src)} />
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
                <div className="absolute top-2 right-2 flex gap-1">
                  <button onClick={(e) => { e.stopPropagation(); setLightbox(src) }} className="p-1.5 rounded-md bg-black/50 text-white/80 hover:text-white">
                    <Maximize2 className="w-3 h-3" />
                  </button>
                  <button onClick={(e) => { e.stopPropagation(); onDelete(f.id) }} className="p-1.5 rounded-md bg-red-500/30 text-red-300 hover:bg-red-500/50">
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              </div>
              {f.is_selected && <Badge className="absolute top-1 left-1 text-[10px]">已选</Badge>}
            </div>
          )
        })}
      </div>
      {lightbox && (
        <div className="fixed inset-0 z-50 bg-black/95 flex items-center justify-center cursor-zoom-out" onClick={() => setLightbox(null)}>
          <img src={lightbox} alt="" className="max-w-[95vw] max-h-[95vh] object-contain rounded-lg" onClick={e => e.stopPropagation()} />
          <a href={lightbox} download className="absolute bottom-6 right-6 p-2 rounded-full bg-white/10 text-white hover:bg-white/20"><Download className="w-5 h-5" /></a>
          <button onClick={() => setLightbox(null)} className="absolute top-4 right-4 p-2 rounded-full bg-white/10 text-white"><X className="w-5 h-5" /></button>
        </div>
      )}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Video player + delete                                              */
/* ------------------------------------------------------------------ */

function VideoGallery({ files, onDelete }: { files: FileRecord[]; onDelete: (id: string) => void }) {
  const [fullscreen, setFullscreen] = useState<string | null>(null)

  return (
    <div className="space-y-3">
      <p className="text-[11px] text-zinc-500 uppercase tracking-wider px-1">最终视频</p>
      {files.map(f => {
        const src = `${API_BASE}/files/${f.id}/download`
        return (
          <div key={f.id} className="rounded-xl overflow-hidden bg-black ring-1 ring-white/5 group">
            <video
              controls
              src={src}
              className="w-full max-h-[360px] object-contain cursor-pointer"
              preload="metadata"
              onClick={() => setFullscreen(src)}
            />
            <div className="flex items-center justify-between px-3 py-2 bg-zinc-900">
              <span className="text-xs text-zinc-400 truncate">{f.file_path.split('/').pop()}</span>
              <div className="flex gap-1">
                <button onClick={() => setFullscreen(src)} className="text-xs text-violet-400 hover:text-violet-300 flex items-center gap-1 px-2">
                  <Maximize2 className="w-3 h-3" />全屏
                </button>
                <a href={src} download className="text-xs text-zinc-500 hover:text-white flex items-center gap-1 px-2"><Download className="w-3 h-3" />下载</a>
                <button onClick={() => onDelete(f.id)} className="text-xs text-red-500 hover:text-red-400 flex items-center gap-1 px-2"><Trash2 className="w-3 h-3" />删除</button>
              </div>
            </div>
          </div>
        )
      })}
      {fullscreen && (
        <div className="fixed inset-0 z-50 bg-black/95 flex items-center justify-center" onClick={() => setFullscreen(null)}>
          <video
            controls
            autoPlay
            src={fullscreen}
            className="max-w-[95vw] max-h-[95vh] rounded-lg"
            onClick={e => e.stopPropagation()}
          />
          <button onClick={() => setFullscreen(null)} className="absolute top-4 right-4 p-2 rounded-full bg-white/10 text-white hover:bg-white/20">
            <X className="w-5 h-5" />
          </button>
        </div>
      )}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Audio player + delete                                              */
/* ------------------------------------------------------------------ */

function AudioGallery({ files, onDelete }: { files: FileRecord[]; onDelete: (id: string) => void }) {
  return (
    <div className="space-y-2">
      <p className="text-[11px] text-zinc-500 uppercase tracking-wider px-1">配音文件 · {files.length} 个</p>
      {files.map(f => {
        const src = `${API_BASE}/files/${f.id}/download`
        const params = f.generation_params as Record<string, unknown> | undefined
        const typeLabel = params?.type ? String(params.type).toUpperCase() : 'AUDIO'
        const panelIdx = params?.panel_index !== undefined ? `Panel ${params.panel_index}` : null
        return (
          <div key={f.id} className="rounded-xl bg-white/[0.03] ring-1 ring-white/5 p-3 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 min-w-0">
                <Music className="w-4 h-4 text-zinc-500 shrink-0" />
                <Badge variant="secondary" className="text-[10px] shrink-0">{typeLabel}</Badge>
                {panelIdx && <span className="text-[10px] text-zinc-500">{panelIdx}</span>}
              </div>
              <div className="flex gap-1 shrink-0">
                <a href={src} download><Download className="w-3.5 h-3.5 text-zinc-600 hover:text-white" /></a>
                <button onClick={() => onDelete(f.id)}><Trash2 className="w-3.5 h-3.5 text-red-600 hover:text-red-400" /></button>
              </div>
            </div>
            <audio controls src={src} className="w-full h-8" preload="metadata" />
          </div>
        )
      })}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Script content preview + delete                                    */
/* ------------------------------------------------------------------ */

function ScriptGallery({ files, onDelete }: { files: FileRecord[]; onDelete: (id: string) => void }) {
  return (
    <div className="space-y-3">
      <p className="text-[11px] text-zinc-500 uppercase tracking-wider px-1">剧本 · {files.length} 份</p>
      {files.map(f => <ScriptCard key={f.id} file={f} onDelete={onDelete} />)}
    </div>
  )
}

function ScriptCard({ file, onDelete }: { file: FileRecord; onDelete: (id: string) => void }) {
  const [content, setContent] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [copied, setCopied] = useState(false)
  const [collapsed, setCollapsed] = useState(true)

  useEffect(() => {
    if (collapsed) return
    setLoading(true)
    fetch(`${API_BASE}/files/${file.id}/download`)
      .then(r => r.text())
      .then(setContent)
      .catch(() => setContent('加载失败'))
      .finally(() => setLoading(false))
  }, [file.id, collapsed])

  return (
    <div className="rounded-xl bg-white/[0.03] ring-1 ring-white/5 p-3 space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 min-w-0">
          <FileText className="w-4 h-4 text-zinc-500 shrink-0" />
          <span className="text-sm truncate">{file.file_path.split('/').pop()}</span>
          {file.is_selected && <Badge variant="secondary" className="text-[10px] shrink-0">已选</Badge>}
        </div>
        <div className="flex gap-1 shrink-0">
          <button onClick={() => setCollapsed(!collapsed)} className="text-xs text-zinc-500 hover:text-white px-2">
            {collapsed ? '展开' : '收起'}
          </button>
          {content && (
            <button onClick={async () => { await navigator.clipboard.writeText(content); setCopied(true); setTimeout(() => setCopied(false), 2000) }} className="text-xs text-zinc-500 hover:text-white px-1">
              {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
            </button>
          )}
          <a href={`${API_BASE}/files/${file.id}/download`} download className="text-zinc-600 hover:text-white"><Download className="w-3.5 h-3.5" /></a>
          <button onClick={() => onDelete(file.id)}><Trash2 className="w-3.5 h-3.5 text-red-600 hover:text-red-400" /></button>
        </div>
      </div>
      {!collapsed && loading && (
        <div className="flex items-center gap-2 text-xs text-zinc-500"><Loader2 className="w-3 h-3 animate-spin" />加载中...</div>
      )}
      {!collapsed && !loading && content && (
        <pre className="text-xs bg-black/30 rounded-lg p-3 overflow-auto max-h-72 whitespace-pre-wrap font-mono leading-relaxed text-zinc-300">
          {content}
        </pre>
      )}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Storyboard visual panels + delete                                  */
/* ------------------------------------------------------------------ */

function StoryboardGallery({ files, onDelete }: { files: FileRecord[]; onDelete: (id: string) => void }) {
  return (
    <div className="space-y-3">
      <p className="text-[11px] text-zinc-500 uppercase tracking-wider px-1">分镜 · {files.length} 份</p>
      {files.map(f => <StoryboardCard key={f.id} file={f} onDelete={onDelete} />)}
    </div>
  )
}

function StoryboardCard({ file, onDelete }: { file: FileRecord; onDelete: (id: string) => void }) {
  const [data, setData] = useState<{ panels?: Array<Record<string, unknown>> } | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(false)
  const [collapsed, setCollapsed] = useState(true)

  useEffect(() => {
    if (collapsed) return
    setLoading(true)
    fetch(`${API_BASE}/files/${file.id}/download`)
      .then(r => r.text())
      .then(text => {
        let clean = text.trim()
        if (clean.startsWith('```')) clean = clean.replace(/^```\w*\n/, '').replace(/\n```\s*$/, '')
        return JSON.parse(clean)
      })
      .then(setData)
      .catch(() => setError(true))
      .finally(() => setLoading(false))
  }, [file.id, collapsed])

  return (
    <div className="rounded-xl bg-white/[0.03] ring-1 ring-white/5 p-3 space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 min-w-0">
          <FileJson className="w-4 h-4 text-zinc-500 shrink-0" />
          <span className="text-sm truncate">{file.file_path.split('/').pop()}</span>
          {file.is_selected && <Badge variant="secondary" className="text-[10px] shrink-0">已选</Badge>}
        </div>
        <div className="flex gap-1 shrink-0">
          <button onClick={() => setCollapsed(!collapsed)} className="text-xs text-zinc-500 hover:text-white px-2">
            {collapsed ? '展开' : '收起'}
          </button>
          <a href={`${API_BASE}/files/${file.id}/download`} download className="text-zinc-600 hover:text-white"><Download className="w-3.5 h-3.5" /></a>
          <button onClick={() => onDelete(file.id)}><Trash2 className="w-3.5 h-3.5 text-red-600 hover:text-red-400" /></button>
        </div>
      </div>
      {!collapsed && loading && (
        <div className="flex items-center gap-2 text-xs text-zinc-500"><Loader2 className="w-3 h-3 animate-spin" />加载中...</div>
      )}
      {!collapsed && error && <p className="text-xs text-red-400">解析失败</p>}
      {!collapsed && data?.panels && (
        <div className="space-y-2 max-h-96 overflow-auto">
          {data.panels.map((panel: Record<string, unknown>, i: number) => (
            <div key={i} className="border border-white/10 rounded-lg p-2 text-xs space-y-1 bg-black/20">
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-[10px] px-1 py-0 border-white/20">Panel {i + 1}</Badge>
                {Boolean(panel.emotion) && <span className="text-zinc-400 italic">{String(panel.emotion)}</span>}
              </div>
              {Boolean(panel.scene_description) && <p className="leading-relaxed text-zinc-300">{String(panel.scene_description).slice(0, 250)}</p>}
              {Boolean(panel.camera_angle) && <p className="text-[10px] text-zinc-500">🎬 {String(panel.camera_angle)}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Generic text/JSON preview for inspiration/story/chapter_outline   */
/* ------------------------------------------------------------------ */

function TextGallery({ files, onDelete }: { files: FileRecord[]; onDelete: (id: string) => void }) {
  return (
    <div className="space-y-3">
      <p className="text-[11px] text-zinc-500 uppercase tracking-wider px-1">生成文件 · {files.length} 份</p>
      {files.map(f => <ScriptCard key={f.id} file={f} onDelete={onDelete} />)}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Main export                                                        */
/* ------------------------------------------------------------------ */

interface Props {
  fileType: string
  files: FileRecord[]
  onFilesChange?: () => void
}

export function StageArtifacts({ fileType, files, onFilesChange }: Props) {
  const handleDelete = async (fileId: string) => {
    try {
      await fetch(`${API_BASE}/files/${fileId}`, { method: 'DELETE' })
      onFilesChange?.()
    } catch { /* ignore */ }
  }

  if (fileType === 'image') return <ImageGallery files={files} onDelete={handleDelete} />
  if (fileType === 'video') return <VideoGallery files={files} onDelete={handleDelete} />
  if (fileType === 'audio') return <AudioGallery files={files} onDelete={handleDelete} />
  if (fileType === 'script') return <ScriptGallery files={files} onDelete={handleDelete} />
  if (fileType === 'storyboard') return <StoryboardGallery files={files} onDelete={handleDelete} />
  // New stage file types — use generic text preview
  if (['inspiration', 'story', 'chapter_outline'].includes(fileType))
    return <TextGallery files={files} onDelete={handleDelete} />

  return (
    <div className="space-y-1">
      {files.map(f => (
        <div key={f.id} className="flex items-center gap-2 text-xs text-zinc-400 px-1">
          <FileText className="w-3 h-3" />
          <span className="truncate">{f.file_path.split('/').pop()}</span>
          <a href={`${API_BASE}/files/${f.id}/download`} download className="ml-auto"><Download className="w-3 h-3" /></a>
          <button onClick={() => handleDelete(f.id)}><Trash2 className="w-3 h-3 text-red-600" /></button>
        </div>
      ))}
    </div>
  )
}
