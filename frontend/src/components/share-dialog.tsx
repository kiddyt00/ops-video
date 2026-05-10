'use client'

import { useState } from 'react'
import { Share2, X, Loader2, AlertCircle, UserPlus } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Separator } from '@/components/ui/separator'
import { ScrollArea } from '@/components/ui/scroll-area'
import { api } from '@/lib/api'
import { useProjectShares, useShareProject, useUnshareProject } from '@/hooks/use-projects'
import type { User } from '@/lib/api/auth'

interface ShareInfo {
  id: string
  project_id: string
  owner_id: string
  shared_with_user_id: string
  permission: string
  created_at: string
}

interface ShareDialogProps {
  projectId: string
  trigger?: React.ReactNode
}

const PERMISSION_LABELS: Record<string, string> = {
  view: '只读',
  edit: '编辑',
}

export function ShareDialog({ projectId, trigger }: ShareDialogProps) {
  const [open, setOpen] = useState(false)
  const [email, setEmail] = useState('')
  const [permission, setPermission] = useState('view')
  const [searching, setSearching] = useState(false)
  const [foundUser, setFoundUser] = useState<User | null>(null)
  const [error, setError] = useState<string | null>(null)

  const { data: shares, isLoading: loadingShares } = useProjectShares(projectId)
  const shareMutation = useShareProject()
  const unshareMutation = useUnshareProject()

  const handleSearch = async () => {
    if (!email.trim()) return
    setError(null)
    setFoundUser(null)
    setSearching(true)
    try {
      const user = await api.get<User>(`/users/search?email=${encodeURIComponent(email.trim())}`).then(r => r.data)
      setFoundUser(user)
    } catch (e) {
      setError(e instanceof Error ? e.message : '未找到该用户')
    } finally {
      setSearching(false)
    }
  }

  const handleShare = async () => {
    if (!foundUser) return
    setError(null)
    try {
      await shareMutation.mutateAsync({
        projectId,
        data: { shared_with_user_id: foundUser.id, permission },
      })
      setEmail('')
      setFoundUser(null)
      setPermission('view')
    } catch (e) {
      setError(e instanceof Error ? e.message : '分享失败')
    }
  }

  const handleUnshare = async (userId: string) => {
    try {
      await unshareMutation.mutateAsync({ projectId, userId })
    } catch (e) {
      setError(e instanceof Error ? e.message : '取消分享失败')
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      {trigger ? (
        <div onClick={() => setOpen(true)} className="cursor-pointer inline-flex">{trigger}</div>
      ) : (
        <DialogTrigger className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-input bg-background hover:bg-muted text-sm transition-colors cursor-pointer">
          <Share2 className="w-3.5 h-3.5" />
          分享
        </DialogTrigger>
      )}

      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>项目分享</DialogTitle>
          <DialogDescription>与其他用户共享此项目</DialogDescription>
        </DialogHeader>

        {error && (
          <div className="flex items-start gap-2 text-xs text-destructive bg-destructive/10 rounded p-2">
            <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* Add share */}
        <div className="space-y-2">
          <label className="text-xs font-medium">添加用户</label>
          <div className="flex gap-2">
            <div className="flex-1">
              <Input
                value={email}
                onChange={e => { setEmail(e.target.value); setFoundUser(null); setError(null) }}
                placeholder="输入用户邮箱"
                onKeyDown={e => e.key === 'Enter' && handleSearch()}
              />
            </div>
            <Button
              variant="secondary"
              size="sm"
              onClick={handleSearch}
              disabled={!email.trim() || searching}
            >
              {searching ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : '查找'}
            </Button>
          </div>

          {foundUser && (
            <div className="flex items-center gap-2 p-2 bg-muted/50 rounded-md">
              <UserPlus className="w-4 h-4 text-primary" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{foundUser.username}</p>
                <p className="text-xs text-muted-foreground truncate">{foundUser.email}</p>
              </div>
              <Select value={permission} onValueChange={(v) => v != null && setPermission(v)}>
                <SelectTrigger className="w-20 h-8 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="view">只读</SelectItem>
                  <SelectItem value="edit">编辑</SelectItem>
                </SelectContent>
              </Select>
              <Button size="sm" onClick={handleShare} disabled={shareMutation.isPending}>
                {shareMutation.isPending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : '添加'}
              </Button>
            </div>
          )}
        </div>

        <Separator />

        {/* Existing shares */}
        <div>
          <h4 className="text-sm font-medium mb-2">
            已分享的用户
            {shares && shares.length > 0 && (
              <span className="text-muted-foreground ml-1">({shares.length})</span>
            )}
          </h4>

          {loadingShares ? (
            <div className="flex justify-center py-4">
              <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
            </div>
          ) : shares && shares.length > 0 ? (
            <ScrollArea className="max-h-48">
              <div className="space-y-1">
                {shares.map((s: ShareInfo) => (
                  <div
                    key={s.id}
                    className="flex items-center justify-between px-3 py-2 rounded-md hover:bg-muted/50 group"
                  >
                    <div className="min-w-0 flex-1">
                      <p className="text-sm truncate">{s.shared_with_user_id.substring(0, 8)}...</p>
                      <p className="text-xs text-muted-foreground">
                        {PERMISSION_LABELS[s.permission] ?? s.permission}
                      </p>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity"
                      onClick={() => handleUnshare(s.shared_with_user_id)}
                    >
                      <X className="w-3.5 h-3.5 text-destructive" />
                    </Button>
                  </div>
                ))}
              </div>
            </ScrollArea>
          ) : (
            <p className="text-sm text-muted-foreground text-center py-4">
              尚未分享给任何人
            </p>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
