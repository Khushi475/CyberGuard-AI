/** Login page (FR-01). */
import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { AlertCircle, Eye, EyeOff, Lock, Mail, Shield, Sparkles } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { Spinner } from '../components/ui'

const DEMO_ACCOUNTS = [
  { role: 'Administrator', email: 'admin@cyberguard.ai', password: 'admin123' },
  { role: 'Security Analyst', email: 'analyst@cyberguard.ai', password: 'analyst123' },
  { role: 'Viewer', email: 'viewer@cyberguard.ai', password: 'viewer123' },
]

const FEATURES = [
  'Hybrid rule-based, statistical and ML threat detection',
  'Explainable risk scoring from 0 to 100 with stated reasons',
  'Alert triage and full incident lifecycle management',
  'CSV log analysis with per-row validation feedback',
]

export default function Login() {
  const { login } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()
  const location = useLocation()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [remember, setRemember] = useState(true)
  const [showPassword, setShowPassword] = useState(false)
  const [errors, setErrors] = useState({})
  const [formError, setFormError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const validate = () => {
    const found = {}
    if (!email.trim()) found.email = 'Email address is required.'
    else if (!/^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$/.test(email.trim()))
      found.email = 'Enter a valid email address.'
    if (!password) found.password = 'Password is required.'
    setErrors(found)
    return Object.keys(found).length === 0
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setFormError('')
    if (!validate()) return

    setSubmitting(true)
    try {
      const user = await login(email.trim(), password, remember)
      toast.success(`Welcome back, ${user.full_name.split(' ')[0]}.`)
      navigate(location.state?.from || '/dashboard', { replace: true })
    } catch (error) {
      setFormError(error.message)
      if (error.isOffline) toast.error('Backend unavailable.')
    } finally {
      setSubmitting(false)
    }
  }

  const useDemoAccount = (account) => {
    setEmail(account.email)
    setPassword(account.password)
    setErrors({})
    setFormError('')
  }

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      {/* Brand / context panel */}
      <div className="relative hidden flex-col justify-between overflow-hidden border-r border-white/10 bg-navy-900/60 p-10 lg:flex">
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.16]"
          style={{
            backgroundImage:
              'linear-gradient(rgba(34,211,238,0.14) 1px, transparent 1px), linear-gradient(90deg, rgba(34,211,238,0.14) 1px, transparent 1px)',
            backgroundSize: '48px 48px',
          }}
          aria-hidden="true"
        />
        <div className="relative">
          <div className="flex items-center gap-3">
            <span className="rounded-xl border border-accent/30 bg-accent/10 p-2.5 text-accent">
              <Shield size={26} />
            </span>
            <div>
              <h1 className="text-lg font-semibold tracking-tight text-slate-100">CyberGuard AI</h1>
              <p className="text-xs uppercase tracking-wider text-slate-500">
                Intelligent Cyber Threat Detection System
              </p>
            </div>
          </div>

          <h2 className="mt-14 max-w-md text-3xl font-semibold leading-tight tracking-tight text-slate-100">
            Detect, investigate and resolve security events from a single console.
          </h2>
          <p className="mt-4 max-w-md text-sm leading-relaxed text-slate-400">
            A Security Operations Centre workflow built for the Software Engineering Lab: every
            detection is explainable, every status change is audited, and every figure on the
            dashboard comes from the live database.
          </p>

          <ul className="mt-8 space-y-3">
            {FEATURES.map((feature) => (
              <li key={feature} className="flex items-start gap-3 text-sm text-slate-300">
                <Sparkles size={15} className="mt-0.5 shrink-0 text-accent" />
                {feature}
              </li>
            ))}
          </ul>
        </div>

        <p className="relative max-w-md text-xs leading-relaxed text-slate-600">
          Academic prototype. It analyses simulated, defensive telemetry only - it performs no
          scanning, exploitation or offensive activity of any kind, and contains no real threat
          infrastructure.
        </p>
      </div>

      {/* Sign-in form */}
      <div className="flex items-center justify-center px-4 py-10 sm:px-8">
        <div className="w-full max-w-md">
          <div className="mb-8 flex items-center gap-3 lg:hidden">
            <span className="rounded-xl border border-accent/30 bg-accent/10 p-2.5 text-accent">
              <Shield size={24} />
            </span>
            <div>
              <h1 className="text-base font-semibold text-slate-100">CyberGuard AI</h1>
              <p className="text-xs text-slate-500">Threat Detection Console</p>
            </div>
          </div>

          <h2 className="text-2xl font-semibold tracking-tight text-slate-100">Sign in</h2>
          <p className="mt-1.5 text-sm text-slate-400">
            Use a demo account below to enter the console.
          </p>

          {formError && (
            <div className="mt-5 flex items-start gap-2.5 rounded-lg border border-danger/40 bg-danger/10 p-3.5">
              <AlertCircle size={16} className="mt-0.5 shrink-0 text-danger" />
              <p className="text-sm text-slate-200">{formError}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="mt-6 space-y-4" noValidate>
            <div>
              <label className="field-label" htmlFor="email">
                Email address
              </label>
              <div className="relative">
                <Mail
                  size={15}
                  className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500"
                />
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="admin@cyberguard.ai"
                  className={`field-input pl-9 ${errors.email ? 'field-input-error' : ''}`}
                  aria-invalid={Boolean(errors.email)}
                />
              </div>
              {errors.email && (
                <p className="field-error">
                  <AlertCircle size={12} />
                  {errors.email}
                </p>
              )}
            </div>

            <div>
              <label className="field-label" htmlFor="password">
                Password
              </label>
              <div className="relative">
                <Lock
                  size={15}
                  className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500"
                />
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="Enter your password"
                  className={`field-input px-9 ${errors.password ? 'field-input-error' : ''}`}
                  aria-invalid={Boolean(errors.password)}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((shown) => !shown)}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 rounded p-1 text-slate-500 transition-colors hover:text-slate-300"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
              {errors.password && (
                <p className="field-error">
                  <AlertCircle size={12} />
                  {errors.password}
                </p>
              )}
            </div>

            <label className="flex cursor-pointer select-none items-center gap-2.5 text-sm text-slate-400">
              <input
                type="checkbox"
                checked={remember}
                onChange={(event) => setRemember(event.target.checked)}
                className="h-4 w-4 cursor-pointer rounded border-white/20 bg-navy-950 text-accent focus:ring-accent/50"
              />
              Remember me on this device
            </label>

            <button type="submit" className="btn-primary w-full" disabled={submitting}>
              {submitting ? (
                <>
                  <Spinner size={16} />
                  Signing in...
                </>
              ) : (
                'Sign in to console'
              )}
            </button>
          </form>

          <div className="mt-8">
            <p className="mb-3 text-xs uppercase tracking-wider text-slate-500">Demo accounts</p>
            <div className="space-y-2">
              {DEMO_ACCOUNTS.map((account) => (
                <button
                  key={account.email}
                  type="button"
                  onClick={() => useDemoAccount(account)}
                  className="flex w-full items-center justify-between gap-3 rounded-lg border border-white/10 bg-navy-900/60 px-3.5 py-2.5 text-left transition-all hover:border-accent/40 hover:bg-navy-850"
                >
                  <span className="min-w-0">
                    <span className="block text-sm font-medium text-slate-200">{account.role}</span>
                    <span className="mono block truncate text-xs text-slate-500">
                      {account.email} / {account.password}
                    </span>
                  </span>
                  <span className="shrink-0 text-xs font-medium text-accent">Use</span>
                </button>
              ))}
            </div>
            <p className="mt-4 text-xs leading-relaxed text-slate-600">
              These are seeded demonstration credentials for a local academic prototype. Passwords
              are stored as salted PBKDF2 hashes; this is not production-grade authentication.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
