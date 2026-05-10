'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Film, Loader2, AlertCircle, Eye, EyeOff, Clapperboard, Sparkles, ArrowRight } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAuth } from '@/hooks/use-auth'

export default function LoginPage() {
  const router = useRouter()
  const { login, register, isLoading: authLoading, error, clearError } = useAuth()

  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [showPassword, setShowPassword] = useState(false)
  const [focused, setFocused] = useState<string | null>(null)

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
      await register({ email: regEmail.trim(), username: regUsername.trim(), password: regPassword })
      router.push('/')
    } catch {
    } finally {
      setIsSubmitting(false)
    }
  }

  const switchMode = () => {
    setMode(prev => prev === 'login' ? 'register' : 'login')
    clearError()
    setFieldErrors({})
  }

  return (
    <div className="min-h-screen flex bg-[#0a0a12] relative overflow-hidden">
      {/* ─── Ambient background ───────────────────────────────── */}
      <div className="absolute inset-0 pointer-events-none">
        {/* Top-right glow */}
        <div className="absolute -top-40 -right-40 w-[600px] h-[600px] rounded-full bg-primary/10 blur-[120px]" />
        {/* Bottom-left glow */}
        <div className="absolute -bottom-60 -left-60 w-[700px] h-[700px] rounded-full bg-violet-500/8 blur-[140px]" />
        {/* Center accent */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] rounded-full bg-primary/5 blur-[100px]" />
        {/* Subtle grid */}
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
            backgroundSize: '60px 60px',
          }}
        />
      </div>

      {/* ─── Left Branding Panel ──────────────────────────────── */}
      <div className="hidden lg:flex w-[520px] flex-col justify-between p-12 relative z-10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary/20 flex items-center justify-center ring-1 ring-primary/30">
            <Clapperboard className="w-5 h-5 text-primary" />
          </div>
          <span className="text-xl font-bold tracking-tight text-white">Ops-Video</span>
        </div>

        <div className="space-y-6">
          <div className="space-y-3">
            <h1 className="text-5xl font-bold leading-tight text-white">
              用 AI 创作
              <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary via-violet-400 to-primary">
                属于你的漫剧
              </span>
            </h1>
            <p className="text-lg text-white/50 max-w-sm leading-relaxed">
              输入一个想法，AI 自动完成从剧本、分镜、图片到配音和视频合成的全流程创作。
            </p>
          </div>

          <div className="flex gap-6 pt-4">
            {[
              { label: '文生脚本', desc: 'LLM 智能编剧' },
              { label: '分镜生成', desc: '自动拆解镜头' },
              { label: 'AI 绘图', desc: '通义万相渲染' },
              { label: '视频合成', desc: '一键出片' },
            ].map((step, i) => (
              <div key={i} className="flex items-start gap-2">
                <div className="w-6 h-6 rounded-full bg-primary/10 ring-1 ring-primary/20 flex items-center justify-center shrink-0 mt-0.5">
                  <span className="text-[10px] font-bold text-primary">{i + 1}</span>
                </div>
                <div>
                  <p className="text-xs font-medium text-white/80">{step.label}</p>
                  <p className="text-[10px] text-white/30">{step.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <p className="text-xs text-white/20">
          由 AI 驱动 · 创作从未如此简单
        </p>
      </div>

      {/* ─── Right Form Panel ──────────────────────────────────── */}
      <div className="flex-1 flex items-center justify-center p-6 relative z-10">
        {/* Mobile logo */}
        <div className="absolute top-6 left-6 lg:hidden flex items-center gap-2">
          <Clapperboard className="w-5 h-5 text-primary" />
          <span className="text-sm font-bold text-white">Ops-Video</span>
        </div>

        <div className="w-full max-w-[400px] space-y-8">
          {/* Header */}
          <div className="text-center lg:text-left space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 ring-1 ring-primary/20 text-xs text-primary font-medium">
              <Sparkles className="w-3 h-3" />
              AI 漫剧生成平台
            </div>
            <h2 className="text-2xl font-bold text-white mt-3">
              {mode === 'login' ? '欢迎回来' : '创建账号'}
            </h2>
            <p className="text-sm text-white/40">
              {mode === 'login' ? '登录你的账号继续创作' : '注册后即可开始 AI 漫剧创作'}
            </p>
          </div>

          {/* Error */}
          {error && (
            <div className="flex items-start gap-2.5 text-sm text-red-400 bg-red-500/10 rounded-xl p-3.5 ring-1 ring-red-500/20 backdrop-blur-sm">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {/* Form */}
          <form
            onSubmit={mode === 'login' ? handleLogin : handleRegister}
            className="space-y-4"
            autoComplete="off"
          >
            {mode === 'register' && (
              <FieldWrapper label="用户名" error={fieldErrors.regUsername} focused={focused === 'regUsername'}>
                <Input
                  value={regUsername}
                  onChange={e => { setRegUsername(e.target.value); setFieldErrors(p => ({ ...p, regUsername: '' })) }}
                  onFocus={() => setFocused('regUsername')}
                  onBlur={() => setFocused(null)}
                  placeholder="你的昵称"
                  className={cn(fieldStyles, fieldErrors.regUsername && 'ring-red-500/50')}
                />
              </FieldWrapper>
            )}

            <FieldWrapper label="邮箱" error={fieldErrors[mode === 'login' ? 'loginEmail' : 'regEmail']} focused={focused === 'email'}>
              <Input
                type="email"
                value={mode === 'login' ? loginEmail : regEmail}
                onChange={e => {
                  const setter = mode === 'login' ? setLoginEmail : setRegEmail
                  setter(e.target.value)
                  setFieldErrors(p => ({ ...p, [mode === 'login' ? 'loginEmail' : 'regEmail']: '' }))
                }}
                onFocus={() => setFocused('email')}
                onBlur={() => setFocused(null)}
                placeholder="your@email.com"
                className={cn(fieldStyles, (fieldErrors.loginEmail || fieldErrors.regEmail) && 'ring-red-500/50')}
              />
            </FieldWrapper>

            <FieldWrapper label="密码" error={fieldErrors[mode === 'login' ? 'loginPassword' : 'regPassword']} focused={focused === 'password'}>
              <div className="relative">
                <Input
                  type={showPassword ? 'text' : 'password'}
                  value={mode === 'login' ? loginPassword : regPassword}
                  onChange={e => {
                    const setter = mode === 'login' ? setLoginPassword : setRegPassword
                    setter(e.target.value)
                    setFieldErrors(p => ({ ...p, [mode === 'login' ? 'loginPassword' : 'regPassword']: '' }))
                  }}
                  onFocus={() => setFocused('password')}
                  onBlur={() => setFocused(null)}
                  placeholder={mode === 'login' ? '输入密码' : '至少 8 个字符'}
                  className={cn(fieldStyles, 'pr-10', (fieldErrors.loginPassword || fieldErrors.regPassword) && 'ring-red-500/50')}
                />
                <button
                  type="button"
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/60 transition-colors"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </FieldWrapper>

            {mode === 'register' && (
              <FieldWrapper label="确认密码" error={fieldErrors.regConfirmPassword} focused={focused === 'confirm'}>
                <Input
                  type="password"
                  value={regConfirmPassword}
                  onChange={e => { setRegConfirmPassword(e.target.value); setFieldErrors(p => ({ ...p, regConfirmPassword: '' })) }}
                  onFocus={() => setFocused('confirm')}
                  onBlur={() => setFocused(null)}
                  placeholder="再次输入密码"
                  className={cn(fieldStyles, fieldErrors.regConfirmPassword && 'ring-red-500/50')}
                />
              </FieldWrapper>
            )}

            <Button
              type="submit"
              className="w-full h-12 rounded-xl bg-gradient-to-r from-primary to-violet-500 hover:from-primary/90 hover:to-violet-500/90 text-white font-medium text-sm shadow-lg shadow-primary/20 transition-all duration-300 hover:shadow-primary/30 hover:scale-[1.01] active:scale-[0.99]"
              disabled={isSubmitting || authLoading}
            >
              {isSubmitting || authLoading ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <ArrowRight className="w-4 h-4 mr-1.5" />
              )}
              {mode === 'login' ? '登录' : '创建账号'}
            </Button>
          </form>

          {/* Switch mode */}
          <div className="text-center">
            <button
              onClick={switchMode}
              className="text-sm text-white/40 hover:text-primary transition-colors"
            >
              {mode === 'login' ? '还没有账号？立即注册' : '已有账号？去登录'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── Field Wrapper ────────────────────────────────────────────────────

const fieldStyles = cn(
  'h-12 rounded-xl bg-white/[0.04] border-0 ring-1 ring-white/[0.08]',
  'text-white placeholder:text-white/20',
  'focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-0',
  'transition-all duration-200'
)

function FieldWrapper({
  label,
  error,
  focused,
  children,
}: {
  label: string
  error?: string
  focused?: boolean
  children: React.ReactNode
}) {
  return (
    <div className="space-y-1.5">
      <label className={cn(
        'text-xs font-medium transition-colors duration-200',
        focused ? 'text-primary' : 'text-white/40'
      )}>
        {label}
      </label>
      {children}
      {error && (
        <p className="text-xs text-red-400/80 pl-1">{error}</p>
      )}
    </div>
  )
}
