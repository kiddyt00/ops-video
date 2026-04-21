'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Film, Plus, Loader2, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { useProjects, useCreateProject, useDeleteProject } from '@/hooks/use-projects'

export default function ProjectsPage() {
  const router = useRouter()
  const { data: projects, isLoading } = useProjects()
  const createProject = useCreateProject()
  const deleteProject = useDeleteProject()
  const [showDialog, setShowDialog] = useState(false)
  const [newName, setNewName] = useState('')
  const [newDesc, setNewDesc] = useState('')

  const handleCreate = async () => {
    if (!newName.trim()) return
    await createProject.mutateAsync({
      name: newName.trim(),
      description: newDesc.trim() || null,
    })
    setNewName('')
    setNewDesc('')
    setShowDialog(false)
  }

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (confirm('确定删除此项目？')) {
      await deleteProject.mutateAsync(id)
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="h-14 border-b border-border flex items-center justify-between px-6">
        <div className="flex items-center gap-2">
          <Film className="w-5 h-5 text-primary" />
          <h1 className="font-bold text-lg">Ops-Video</h1>
        </div>
        <Button onClick={() => setShowDialog(true)}>
          <Plus className="w-4 h-4 mr-1.5" />
          新建项目
        </Button>
      </header>

      <main className="max-w-5xl mx-auto p-6">
        <h2 className="text-2xl font-semibold mb-6">我的项目</h2>

        {isLoading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <Card key={i}>
                <CardHeader>
                  <Skeleton className="h-5 w-3/4" />
                  <Skeleton className="h-4 w-full mt-2" />
                </CardHeader>
              </Card>
            ))}
          </div>
        ) : projects && projects.length > 0 ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {projects.map(project => (
              <Card
                key={project.id}
                className="cursor-pointer hover:border-primary transition-colors group relative"
                onClick={() => router.push(`/projects/${project.id}`)}
              >
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span className="truncate">{project.name}</span>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="opacity-0 group-hover:opacity-100 transition-opacity h-7 w-7"
                      onClick={(e) => handleDelete(project.id, e)}
                    >
                      <Trash2 className="w-3.5 h-3.5 text-destructive" />
                    </Button>
                  </CardTitle>
                  <CardDescription>
                    {project.description || '暂无描述'}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex gap-1.5 flex-wrap">
                    {['script', 'storyboard', 'image', 'audio', 'video'].map(s => (
                      <Badge key={s} variant="secondary" className="text-xs">{s}</Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <div className="text-center py-20">
            <Film className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground mb-4">还没有项目，创建一个开始吧</p>
            <Button onClick={() => setShowDialog(true)}>
              <Plus className="w-4 h-4 mr-1.5" />
              新建项目
            </Button>
          </div>
        )}
      </main>

      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>新建项目</DialogTitle>
            <DialogDescription>为你的漫剧短片创建一个新项目</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <label className="text-sm font-medium mb-1.5 block">项目名称</label>
              <Input
                value={newName}
                onChange={e => setNewName(e.target.value)}
                placeholder="输入项目名称"
                autoFocus
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-1.5 block">描述（可选）</label>
              <Input
                value={newDesc}
                onChange={e => setNewDesc(e.target.value)}
                placeholder="项目描述"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDialog(false)}>取消</Button>
            <Button onClick={handleCreate} disabled={!newName.trim() || createProject.isPending}>
              {createProject.isPending && <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />}
              创建
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
