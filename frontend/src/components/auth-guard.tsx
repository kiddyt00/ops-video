'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Loader2 } from 'lucide-react'
import { useAuth } from '@/hooks/use-auth'

interface AuthGuardProps {
  children: React.ReactNode
  /** If true, redirects to /login when not authenticated */
  requireAuth?: boolean
  /** Optional fallback component while loading */
  fallback?: React.ReactNode
}

export function AuthGuard({ children, requireAuth = true, fallback }: AuthGuardProps) {
  const router = useRouter()
  const { isAuthenticated, isLoading } = useAuth()

  useEffect(() => {
    if (!isLoading && requireAuth && !isAuthenticated) {
      router.replace('/login')
    }
  }, [isLoading, isAuthenticated, requireAuth, router])

  if (isLoading) {
    return fallback ?? (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (requireAuth && !isAuthenticated) {
    return null
  }

  return <>{children}</>
}
