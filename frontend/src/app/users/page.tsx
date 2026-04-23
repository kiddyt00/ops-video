'use client'

import { useState } from 'react'
import { Users, Shield, UserCheck, UserX, Loader2, AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { AppShell } from '@/components/app-shell'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'

interface User {
  id: string
  email: string
  username: string
  full_name: string | null
  role: 'user' | 'admin'
  is_active: boolean
  is_verified: boolean
  last_login_at: string | null
  created_at: string
}

async function fetchUsers(): Promise<User[]> {
  const { data } = await api.get<User[]>('/users')
  return data
}

async function updateUserRole(userId: string, role: string): Promise<void> {
  await api.put(`/users/${userId}`, { role })
}

async function toggleUserActive(userId: string, isActive: boolean): Promise<void> {
  await api.put(`/users/${userId}`, { is_active: isActive })
}

export default function UsersPage() {
  const queryClient = useQueryClient()
  const { data: users, isLoading, error } = useQuery({
    queryKey: ['users'],
    queryFn: fetchUsers,
  })

  const updateRole = useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: string }) => updateUserRole(userId, role),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] }),
  })

  const toggleActive = useMutation({
    mutationFn: ({ userId, isActive }: { userId: string; isActive: boolean }) => toggleUserActive(userId, isActive),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] }),
  })

  return (
    <AppShell>
      <ScrollArea className="h-full">
        <div className="p-6 max-w-4xl mx-auto">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-semibold flex items-center gap-2">
              <Users className="w-6 h-6" />
              用户管理
            </h2>
            <span className="text-sm text-muted-foreground">
              {users?.length ?? 0} 位用户
            </span>
          </div>

          {error && (
            <div className="flex items-start gap-2 text-sm text-destructive bg-destructive/10 rounded-md p-3 mb-4">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>加载用户列表失败，请确认您有管理员权限</span>
            </div>
          )}

          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : users && users.length > 0 ? (
            <div className="space-y-2">
              {users.map(user => (
                <Card key={user.id}>
                  <CardContent className="pt-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={cn(
                          'w-10 h-10 rounded-full flex items-center justify-center',
                          user.role === 'admin' ? 'bg-primary/20' : 'bg-muted'
                        )}>
                          {user.role === 'admin' ? (
                            <Shield className="w-5 h-5 text-primary" />
                          ) : (
                            <UserCheck className="w-5 h-5 text-muted-foreground" />
                          )}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{user.username}</span>
                            <Badge variant={user.role === 'admin' ? 'default' : 'secondary'} className="text-xs">
                              {user.role === 'admin' ? '管理员' : '用户'}
                            </Badge>
                            {user.is_active ? (
                              <Badge variant="outline" className="text-xs text-green-500">活跃</Badge>
                            ) : (
                              <Badge variant="outline" className="text-xs text-red-500">已禁用</Badge>
                            )}
                          </div>
                          <p className="text-xs text-muted-foreground">{user.email}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Select
                          value={user.role ?? 'user'}
                          onValueChange={(v) => { if (v) updateRole.mutate({ userId: user.id, role: v }) }}
                        >
                          <SelectTrigger className="w-[100px]">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="user">用户</SelectItem>
                            <SelectItem value="admin">管理员</SelectItem>
                          </SelectContent>
                        </Select>
                        <Button
                          variant={user.is_active ? 'outline' : 'default'}
                          size="sm"
                          onClick={() => toggleActive.mutate({ userId: user.id, isActive: !user.is_active })}
                        >
                          {user.is_active ? (
                            <UserX className="w-3.5 h-3.5" />
                          ) : (
                            <UserCheck className="w-3.5 h-3.5" />
                          )}
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <div className="text-center py-20">
              <Users className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">暂无用户数据</p>
            </div>
          )}
        </div>
      </ScrollArea>
    </AppShell>
  )
}
