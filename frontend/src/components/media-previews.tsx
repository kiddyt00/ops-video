'use client'

import { useState } from 'react'
import { Image as ImageIcon, Music, Film } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { useFiles } from '@/hooks/use-files'
import type { FileType } from '@/types/file'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

function fileDownloadUrl(fileId: string): string {
  return `${API_BASE_URL}/files/${fileId}/url`
}

export function MediaPreviews({ projectId }: { projectId: string }) {
  const { data: files, isLoading } = useFiles(projectId)

  if (isLoading) {
    return (
      <div className="mt-6">
        <h2 className="text-xl font-semibold mb-4">生成的文件</h2>
        <div className="grid gap-4 md:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-40 w-full rounded-md" />
          ))}
        </div>
      </div>
    )
  }

  if (!files || files.length === 0) {
    return null
  }

  const imageFiles = files.filter(f => f.file_type === 'image')
  const videoFiles = files.filter(f => f.file_type === 'video')
  const audioFiles = files.filter(f => f.file_type === 'audio')
  const scriptFiles = files.filter(f => f.file_type === 'script')
  const storyboardFiles = files.filter(f => f.file_type === 'storyboard')

  return (
    <div className="mt-6 space-y-6">
      {scriptFiles.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-2">脚本文件</h3>
          <div className="grid gap-2 md:grid-cols-2">
            {scriptFiles.map(f => (
              <Card key={f.id}>
                <CardContent className="pt-4">
                  <p className="text-sm font-medium truncate">{f.file_path.split('/').pop()}</p>
                  <p className="text-xs text-muted-foreground">{new Date(f.created_at).toLocaleString('zh-CN')}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {storyboardFiles.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-2">分镜文件</h3>
          <div className="grid gap-2 md:grid-cols-2">
            {storyboardFiles.map(f => (
              <Card key={f.id}>
                <CardContent className="pt-4">
                  <p className="text-sm font-medium truncate">{f.file_path.split('/').pop()}</p>
                  <p className="text-xs text-muted-foreground">{new Date(f.created_at).toLocaleString('zh-CN')}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {imageFiles.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-2">
            <ImageIcon className="w-4 h-4 inline mr-1" />
            图片 ({imageFiles.length})
          </h3>
          <div className="grid gap-3 grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
            {imageFiles.map(f => (
              <ImageCard key={f.id} file={f} />
            ))}
          </div>
        </div>
      )}

      {audioFiles.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-2">
            <Music className="w-4 h-4 inline mr-1" />
            音频 ({audioFiles.length})
          </h3>
          <div className="grid gap-2 md:grid-cols-2">
            {audioFiles.map(f => (
              <AudioCard key={f.id} file={f} />
            ))}
          </div>
        </div>
      )}

      {videoFiles.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-2">
            <Film className="w-4 h-4 inline mr-1" />
            视频 ({videoFiles.length})
          </h3>
          <div className="grid gap-4 md:grid-cols-2">
            {videoFiles.map(f => (
              <VideoCard key={f.id} file={f} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function ImageCard({ file }: { file: { id: string; file_path: string; created_at: string; generation_params?: Record<string, unknown> } }) {
  const [url, setUrl] = useState<string | null>(null)

  const handleLoad = async () => {
    try {
      const resp = await fetch(fileDownloadUrl(file.id))
      const data = await resp.json()
      setUrl(`${API_BASE_URL}/files/${file.id}/download`)
    } catch {
      setUrl(`${API_BASE_URL}/files/${file.id}/download`)
    }
  }

  return (
    <Card className="overflow-hidden">
      <div className="aspect-square bg-muted relative">
        {url ? (
          <img
            src={url}
            alt={file.file_path.split('/').pop()}
            className="w-full h-full object-cover"
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = 'none'
            }}
          />
        ) : (
          <button onClick={handleLoad} className="w-full h-full flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors">
            <ImageIcon className="w-8 h-8" />
          </button>
        )}
      </div>
      <CardContent className="p-2">
        <p className="text-xs text-muted-foreground truncate">{file.file_path.split('/').pop()}</p>
      </CardContent>
    </Card>
  )
}

function AudioCard({ file }: { file: { id: string; file_path: string; created_at: string; generation_params?: Record<string, unknown> } }) {
  const [audioUrl, setAudioUrl] = useState<string | null>(null)

  const handleLoad = () => {
    setAudioUrl(`${API_BASE_URL}/files/${file.id}/download`)
  }

  const params = file.generation_params as Record<string, unknown> | undefined
  const typeLabel = params?.type ? String(params.type).toUpperCase() : 'AUDIO'

  return (
    <Card>
      <CardContent className="pt-4 space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Music className="w-4 h-4 text-muted-foreground" />
            <Badge variant="secondary" className="text-xs">{typeLabel}</Badge>
          </div>
          <p className="text-xs text-muted-foreground truncate max-w-[120px]">{file.file_path.split('/').pop()}</p>
        </div>
        {audioUrl ? (
          <audio controls src={audioUrl} className="w-full h-8" />
        ) : (
          <Button variant="outline" size="sm" className="w-full text-xs" onClick={handleLoad}>
            加载播放器
          </Button>
        )}
      </CardContent>
    </Card>
  )
}

function VideoCard({ file }: { file: { id: string; file_path: string; created_at: string } }) {
  const [videoUrl, setVideoUrl] = useState<string | null>(null)

  const handleLoad = () => {
    setVideoUrl(`${API_BASE_URL}/files/${file.id}/download`)
  }

  return (
    <Card className="overflow-hidden">
      <div className="aspect-[9/16] bg-muted max-h-[400px]">
        {videoUrl ? (
          <video controls src={videoUrl} className="w-full h-full object-contain" />
        ) : (
          <div className="flex flex-col items-center justify-center h-full gap-2">
            <Film className="w-12 h-12 text-muted-foreground" />
            <Button variant="outline" size="sm" onClick={handleLoad}>
              加载视频
            </Button>
          </div>
        )}
      </div>
      <CardContent className="p-2">
        <p className="text-xs text-muted-foreground truncate">{file.file_path.split('/').pop()}</p>
      </CardContent>
    </Card>
  )
}
