/** Toast notifications - the application's single feedback channel. */
import { createContext, useCallback, useContext, useMemo, useRef, useState } from 'react'
import { AlertTriangle, CheckCircle2, Info, X, XCircle } from 'lucide-react'

const ToastContext = createContext(null)

const ICONS = {
  success: CheckCircle2,
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
}

const STYLES = {
  success: 'border-safe/40 bg-safe/10 text-safe',
  error: 'border-danger/40 bg-danger/10 text-danger',
  warning: 'border-warn/40 bg-warn/10 text-warn',
  info: 'border-info/40 bg-info/10 text-info',
}

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])
  const counter = useRef(0)

  const dismiss = useCallback((id) => {
    setToasts((current) => current.filter((toast) => toast.id !== id))
  }, [])

  const push = useCallback(
    (message, type = 'info', duration = 4600) => {
      counter.current += 1
      const id = counter.current
      setToasts((current) => [...current.slice(-3), { id, message, type }])
      if (duration > 0) window.setTimeout(() => dismiss(id), duration)
      return id
    },
    [dismiss],
  )

  const value = useMemo(
    () => ({
      toast: push,
      success: (message, duration) => push(message, 'success', duration),
      error: (message, duration) => push(message, 'error', duration ?? 6500),
      warning: (message, duration) => push(message, 'warning', duration),
      info: (message, duration) => push(message, 'info', duration),
      dismiss,
    }),
    [push, dismiss],
  )

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div
        className="pointer-events-none fixed right-4 top-4 z-[100] flex w-[min(24rem,calc(100vw-2rem))] flex-col gap-2"
        role="status"
        aria-live="polite"
      >
        {toasts.map((toast) => {
          const Icon = ICONS[toast.type] || Info
          return (
            <div
              key={toast.id}
              className={`pointer-events-auto flex animate-slide-in items-start gap-3 rounded-lg border ${
                STYLES[toast.type]
              } bg-navy-900/95 p-3.5 shadow-panel backdrop-blur`}
            >
              <Icon size={18} className="mt-0.5 shrink-0" />
              <p className="flex-1 text-sm leading-snug text-slate-200">{toast.message}</p>
              <button
                type="button"
                onClick={() => dismiss(toast.id)}
                className="shrink-0 rounded p-0.5 text-slate-400 transition-colors hover:text-slate-100"
                aria-label="Dismiss notification"
              >
                <X size={15} />
              </button>
            </div>
          )
        })}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const context = useContext(ToastContext)
  if (!context) throw new Error('useToast must be used inside a ToastProvider')
  return context
}
