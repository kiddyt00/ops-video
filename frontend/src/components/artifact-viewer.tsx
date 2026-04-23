'use client'

import { useState } from 'react'
import { Download, FileText, Image as ImageIcon, Music, Film, FileJson } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
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
}

export function ArtifactViewer({ stage, files }: ArtifactViewerProps) {
  const fileType = STAGE_FILE_TYPE_MAP[stage]
  const stageFiles = files.filter(f => f.file_type === fileType)

  if (!stageFiles.length) return null

  const isImage = fileType === 'image'

  return (
    <div className="mt-3">
      {isImage ? (
        <div className="grid gap-2 grid-cols-2 md:grid-cols-3">
          {stageFiles.map(f => <ImageThumb key={f.id} file={f} />)}
        </div>
      ) : (
        <div className="space-y-1">
          {stageFiles.map(f => <FileRow key={f.id} file={f} />)}
        </div>
      )}
    </div>
  )
}

function ImageThumb({ file }: { file: FileRecord }) {
  const [loaded, setLoaded] = useState(false)

  return (
    <Card className="overflow-hidden">
      <div className="aspect-square bg-muted relative">
        {loaded ? (
          <img
            src={`${API_BASE_URL}/files/${file.id}/download`}
            alt={file.file_path.split('/').pop()}
            className="w-full h-full object-cover"
            onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
          />
        ) : (
          <button
            onClick={() => setLoaded(true)}
            className="w-full h-full flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors"
          >
            <ImageIcon className="w-6 h-6" />
          </button>
        )}
        {file.is_selected && (
          <Badge className="absolute top-1 right-1 text-xs" variant="default">已选</Badge>
        )}
      </div>
      <CardContent className="p-1.5">
        <p className="text-xs text-muted-foreground truncate">{file.file_path.split('/').pop()}</p>
      </CardContent>
    </Card>
  )
}

function FileRow({ file }: { file: FileRecord }) {
  const Icon = FILE_TYPE_ICONS[file.file_type] ?? FileText
  const name = file.file_path.split('/').pop() ?? file.id

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
        <Button variant="ghost" size="sm" className="shrink-0" asChild>
          <a href={`${API_BASE_URL}/files/${file.id}/download`} download>
            <Download className="w-3.5 h-3.5 mr-1" />
            下载
          </a>
        </Button>
      </CardContent>
    </Card>
  )
}
