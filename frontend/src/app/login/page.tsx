'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Film, Loader2, AlertCircle, Eye, EyeOff } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useAuth } from '@/hooks/use-auth'

export default function LoginPage() {
  const router = useRouter()
  const { login, register, isLoading: authLoading, error, clearError } = useAuth()

  const [activeTab, setActiveTab] = useState<'login' | 'register'>('login')
  const [showPassword, setShowPassword] = useState(false)

  // Login form
  const [loginEmail, setLoginEmail] = useState('')
  const [loginPassword, setLoginPassword] = useState('')

  // Register form
  const [regEmail, setRegEmail] = useState('')
  const [regUsername, setRegUsername] = useState('')
  const [regPassword, setRegPassword] = useState('')
  const [regConfirmPassword, setRegConfirmPassword] = useState('')

  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [isSubmitting, setIsSubmitting] = useState(false)

  const validateLogin = (): boolean => {
    const errors: Record<string, string> = {}
    if (!loginEmail.trim()) errors.loginEmail = '请输入邮箱'
    if (!loginPassword) errors.loginPassword = '请输入密码'
    setFieldErrors(errors)
    return Object.keys(errors).length === 0
  }

  const validateRegister = (): boolean => {
    const errors: Record<string, string> = {}
    if (!regEmail.trim()) errors.regEmail = '请输入邮箱'
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(regEmail)) errors.regEmail = '邮箱格式不正确'
    if (!regUsername.trim()) errors.regUsername = '请输入用户名'
    else if (regUsername.trim().length < 3) errors.regUsername = '用户名至少 3 个字符'
    if (!regPassword) errors.regPassword = '请输入密码'
    else if (regPassword.length < 8) errors.regPassword = '密码至少 8 个字符'
    if (regPassword !== regConfirmPassword) errors.regConfirmPassword = '两次密码不一致'
    setFieldErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validateLogin()) return
    clearError()
    setIsSubmitting(true)
    try {
      await login({ email: loginEmail.trim(), password: loginPassword })
      router.push('/')
    } catch {
      // error is already set in hook
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validateRegister()) return
    clearError()
    setIsSubmitting(true)
    try {
      await register({
        email: regEmail.trim(),
        username: regUsername.trim(),
        password: regPassword,
      })
      router.push('/')
    } catch {
      // error is already set in hook
    } finally {
      setIsSubmitting(false)
    }
  }

  const switchTab = (tab: string) => {
    setActiveTab(tab as 'login' | 'register')
    clearError()
    setFieldErrors({})
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-background to-primary/5 p-4">
      <Card className="w-full max-w-md border-border/50 shadow-xl">
        <CardHeader className="text-center pb-2">
          <div className="flex items-center justify-center gap-2 mb-2">
            <Film className="w-8 h-8 text-primary" />
            <span className="text-2xl font-bold tracking-tight">Ops-Video</span>
          </div>
          <CardDescription>AI 漫剧短片生成平台</CardDescription>
        </CardHeader>

        <CardContent>
          <Tabs value={activeTab} onValueChange={switchTab} className="w-full">
            <TabsList className="grid w-full grid-cols-2 mb-6">
              <TabsTrigger value="login">登录</TabsTrigger>
              <TabsTrigger value="register">注册</TabsTrigger>
            </TabsList>

            {/* ─── Login Form ──────────────────────────────────── */}
            <TabsContent value="login">
              <form onSubmit={handleLogin} className="space-y-4">
                {error && (
                  <div className="flex items-start gap-2 text-sm text-destructive bg-destructive/10 rounded-md p-3">
                    <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                    <span>{error}</span>
                  </div>
                )}

                <div>
                  <label className="text-sm font-medium mb-1.5 block">邮箱</label>
                  <Input
                    type="email"
                    value={loginEmail}
                    onChange={e => { setLoginEmail(e.target.value); setFieldErrors(p => ({ ...p, loginEmail: '' })) }}
                    placeholder="your@email.com"
                    className={cn(fieldErrors.loginEmail && 'border-destructive')}
                    autoComplete="email"
                  />
                  {fieldErrors.loginEmail && (
                    <p className="text-xs text-destructive mt-1">{fieldErrors.loginEmail}</p>
                  )}
                </div>

                <div>
                  <label className="text-sm font-medium mb-1.5 block">密码</label>
                  <div className="relative">
                    <Input
                      type={showPassword ? 'text' : 'password'}
                      value={loginPassword}
                      onChange={e => { setLoginPassword(e.target.value); setFieldErrors(p => ({ ...p, loginPassword: '' })) }}
                      placeholder="输入密码"
                      className={cn('pr-10', fieldErrors.loginPassword && 'border-destructive')}
                      autoComplete="current-password"
                    />
                    <button
                      type="button"
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                      onClick={() => setShowPassword(!showPassword)}
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  {fieldErrors.loginPassword && (
                    <p className="text-xs text-destructive mt-1">{fieldErrors.loginPassword}</p>
                  )}
                </div>

                <Button type="submit" className="w-full" disabled={isSubmitting || authLoading}>
                  {(isSubmitting || authLoading) && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                  登录
                </Button>
              </form>
            </TabsContent>

            {/* ─── Register Form ───────────────────────────────── */}
            <TabsContent value="register">
              <form onSubmit={handleRegister} className="space-y-4">
                {error && (
                  <div className="flex items-start gap-2 text-sm text-destructive bg-destructive/10 rounded-md p-3">
                    <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                    <span>{error}</span>
                  </div>
                )}

                <div>
                  <label className="text-sm font-medium mb-1.5 block">邮箱 <span className="text-destructive">*</span></label>
                  <Input
                    type="email"
                    value={regEmail}
                    onChange={e => { setRegEmail(e.target.value); setFieldErrors(p => ({ ...p, regEmail: '' })) }}
                    placeholder="your@email.com"
                    className={cn(fieldErrors.regEmail && 'border-destructive')}
                    autoComplete="email"
                  />
                  {fieldErrors.regEmail && <p className="text-xs text-destructive mt-1">{fieldErrors.regEmail}</p>}
                </div>

                <div>
                  <label className="text-sm font-medium mb-1.5 block">用户名 <span className="text-destructive">*</span></label>
                  <Input
                    value={regUsername}
                    onChange={e => { setRegUsername(e.target.value); setFieldErrors(p => ({ ...p, regUsername: '' })) }}
                    placeholder="至少 3 个字符"
                    className={cn(fieldErrors.regUsername && 'border-destructive')}
                    autoComplete="username"
                  />
                  {fieldErrors.regUsername && <p className="text-xs text-destructive mt-1">{fieldErrors.regUsername}</p>}
                </div>

                <div>
                  <label className="text-sm font-medium mb-1.5 block">密码 <span className="text-destructive">*</span></label>
                  <div className="relative">
                    <Input
                      type={showPassword ? 'text' : 'password'}
                      value={regPassword}
                      onChange={e => { setRegPassword(e.target.value); setFieldErrors(p => ({ ...p, regPassword: '' })) }}
                      placeholder="至少 8 个字符"
                      className={cn('pr-10', fieldErrors.regPassword && 'border-destructive')}
                      autoComplete="new-password"
                    />
                    <button
                      type="button"
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                      onClick={() => setShowPassword(!showPassword)}
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  {fieldErrors.regPassword && <p className="text-xs text-destructive mt-1">{fieldErrors.regPassword}</p>}
                </div>

                <div>
                  <label className="text-sm font-medium mb-1.5 block">确认密码 <span className="text-destructive">*</span></label>
                  <Input
                    type="password"
                    value={regConfirmPassword}
                    onChange={e => { setRegConfirmPassword(e.target.value); setFieldErrors(p => ({ ...p, regConfirmPassword: '' })) }}
                    placeholder="再次输入密码"
                    className={cn(fieldErrors.regConfirmPassword && 'border-destructive')}
                    autoComplete="new-password"
                  />
                  {fieldErrors.regConfirmPassword && <p className="text-xs text-destructive mt-1">{fieldErrors.regConfirmPassword}</p>}
                </div>

                <Button type="submit" className="w-full" disabled={isSubmitting || authLoading}>
                  {(isSubmitting || authLoading) && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                  注册
                </Button>
              </form>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  )
}
