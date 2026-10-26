/**
 * Reusable UI primitives.
 *
 * Every page composes these instead of repeating markup, which is the concrete
 * expression of the "reusable components / no duplicated UI code" requirement
 * and of the maintainability non-functional requirement (NFR-05).
 */
import { useEffect, useRef } from 'react'
import {
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  Inbox,
  Loader2,
  RefreshCw,
  Search,
  ServerCrash,
  X,
} from 'lucide-react'
import { SEVERITY_BADGE, STATUS_BADGE, titleCase } from '../utils/format'

/* ------------------------------------------------------------------ surfaces */

export function Panel({ title, subtitle, actions, children, className = '', bodyClassName = '' }) {
  return (
    <section className={`panel ${className}`}>
      {(title || actions) && (
        <header className="panel-header">
          <div className="min-w-0">
            {title && <h2 className="panel-title">{title}</h2>}
            {subtitle && <p className="panel-subtitle mt-0.5">{subtitle}</p>}
          </div>
          {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
        </header>
      )}
      <div className={bodyClassName || 'p-5'}>{children}</div>
    </section>
  )
}

export function PageHeader({ title, description, children, icon: Icon }) {
  return (
    <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
      <div className="flex items-start gap-3">
        {Icon && (
          <span className="mt-0.5 rounded-lg border border-accent/25 bg-accent/10 p-2 text-accent">
            <Icon size={20} />
          </span>
        )}
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-slate-100 sm:text-2xl">{title}</h1>
          {description && <p className="mt-1 max-w-3xl text-sm text-slate-400">{description}</p>}
        </div>
      </div>
      {children && <div className="flex flex-wrap items-center gap-2">{children}</div>}
    </div>
  )
}

/* -------------------------------------------------------------------- badges */

export function SeverityBadge({ severity, className = '' }) {
  const key = String(severity || 'LOW').toUpperCase()
  return (
    <span className={`badge ${SEVERITY_BADGE[key] || SEVERITY_BADGE.LOW} ${className}`}>
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {key}
    </span>
  )
}

export function StatusBadge({ status, className = '' }) {
  const key = String(status || 'NEW').toUpperCase()
  return (
    <span className={`badge ${STATUS_BADGE[key] || STATUS_BADGE.NEW} ${className}`}>
      {titleCase(key)}
    </span>
  )
}

export function RiskBar({ score = 0, showValue = true, className = '' }) {
  const value = Math.max(0, Math.min(100, Number(score) || 0))
  const color =
    value >= 76 ? 'bg-critical' : value >= 51 ? 'bg-rose-400' : value >= 26 ? 'bg-warn' : 'bg-safe'
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div className="h-1.5 w-full min-w-[3rem] overflow-hidden rounded-full bg-navy-700">
        <div
          className={`h-full rounded-full ${color} transition-all duration-500`}
          style={{ width: `${value}%` }}
        />
      </div>
      {showValue && <span className="mono w-8 shrink-0 text-right text-slate-300">{value}</span>}
    </div>
  )
}

/* ------------------------------------------------------------------- states */

export function Spinner({ size = 18, className = '' }) {
  return <Loader2 size={size} className={`animate-spin ${className}`} />
}

export function LoadingState({ label = 'Loading...', className = '' }) {
  return (
    <div className={`flex flex-col items-center justify-center gap-3 py-14 text-slate-400 ${className}`}>
      <Spinner size={26} className="text-accent" />
      <p className="text-sm">{label}</p>
    </div>
  )
}

export function SkeletonBlock({ className = 'h-4 w-full' }) {
  return <div className={`skeleton ${className}`} />
}

export function SkeletonCard() {
  return (
    <div className="panel p-5">
      <SkeletonBlock className="h-3 w-24" />
      <SkeletonBlock className="mt-4 h-8 w-20" />
      <SkeletonBlock className="mt-4 h-3 w-32" />
    </div>
  )
}

export function SkeletonTable({ rows = 6, columns = 5 }) {
  return (
    <div className="space-y-2 p-5">
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className="flex gap-3">
          {Array.from({ length: columns }).map((__, columnIndex) => (
            <SkeletonBlock
              key={columnIndex}
              className={`h-8 ${columnIndex === 0 ? 'w-28' : 'flex-1'}`}
            />
          ))}
        </div>
      ))}
    </div>
  )
}

export function EmptyState({ title = 'Nothing to show', message, icon: Icon = Inbox, action }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 px-6 py-16 text-center">
      <span className="rounded-full border border-white/10 bg-navy-800/70 p-3.5 text-slate-500">
        <Icon size={24} />
      </span>
      <h3 className="text-sm font-semibold text-slate-200">{title}</h3>
      {message && <p className="max-w-md text-sm text-slate-400">{message}</p>}
      {action}
    </div>
  )
}

export function ErrorState({ error, onRetry, title }) {
  const offline = error?.isOffline
  const Icon = offline ? ServerCrash : AlertCircle
  return (
    <div className="flex flex-col items-center justify-center gap-3 px-6 py-14 text-center">
      <span className="rounded-full border border-danger/30 bg-danger/10 p-3.5 text-danger">
        <Icon size={24} />
      </span>
      <h3 className="text-sm font-semibold text-slate-100">
        {title || (offline ? 'Backend unavailable' : 'Something went wrong')}
      </h3>
      <p className="max-w-lg text-sm text-slate-400">
        {error?.message || 'An unexpected error occurred.'}
      </p>
      {offline && (
        <pre className="mono rounded-lg border border-white/10 bg-navy-950/80 px-3 py-2 text-left text-xs text-slate-400">
          cd backend{'\n'}venv\Scripts\activate{'\n'}python run.py
        </pre>
      )}
      {onRetry && (
        <button type="button" onClick={onRetry} className="btn-secondary mt-1">
          <RefreshCw size={15} />
          Try again
        </button>
      )}
    </div>
  )
}

/* -------------------------------------------------------------------- inputs */

export function SearchInput({ value, onChange, placeholder = 'Search...', className = '' }) {
  return (
    <div className={`relative ${className}`}>
      <Search
        size={15}
        className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500"
      />
      <input
        type="search"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className="field-input pl-9"
        aria-label={placeholder}
      />
    </div>
  )
}

export function Select({ label, value, onChange, options, className = '', id }) {
  const selectId = id || `select-${label?.replace(/\s+/g, '-').toLowerCase()}`
  return (
    <div className={className}>
      {label && (
        <label className="field-label" htmlFor={selectId}>
          {label}
        </label>
      )}
      <select
        id={selectId}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="field-input cursor-pointer"
      >
        {options.map((option) => {
          const optionValue = typeof option === 'string' ? option : option.value
          const optionLabel = typeof option === 'string' ? titleCase(option) : option.label
          return (
            <option key={optionValue} value={optionValue} className="bg-navy-900">
              {optionLabel}
            </option>
          )
        })}
      </select>
    </div>
  )
}

export function Field({ label, error, hint, children, required }) {
  return (
    <div>
      {label && (
        <span className="field-label">
          {label}
          {required && <span className="ml-0.5 text-danger">*</span>}
        </span>
      )}
      {children}
      {error ? (
        <p className="field-error">
          <AlertCircle size={12} />
          {error}
        </p>
      ) : (
        hint && <p className="field-hint">{hint}</p>
      )}
    </div>
  )
}

/* ------------------------------------------------------------------- dialogs */

export function Modal({ open, onClose, title, description, children, footer, size = 'md' }) {
  const overlayRef = useRef(null)

  useEffect(() => {
    if (!open) return undefined
    const onKeyDown = (event) => event.key === 'Escape' && onClose?.()
    document.addEventListener('keydown', onKeyDown)
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      document.body.style.overflow = previousOverflow
    }
  }, [open, onClose])

  if (!open) return null

  const widths = { sm: 'max-w-md', md: 'max-w-2xl', lg: 'max-w-4xl', xl: 'max-w-6xl' }

  return (
    <div
      ref={overlayRef}
      onMouseDown={(event) => event.target === overlayRef.current && onClose?.()}
      className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-navy-950/80 p-4 backdrop-blur-sm sm:p-6"
      role="dialog"
      aria-modal="true"
      aria-label={title}
    >
      <div
        className={`my-auto w-full ${widths[size]} animate-fade-in rounded-xl border border-white/10 bg-navy-900 shadow-panel`}
      >
        <header className="flex items-start justify-between gap-4 border-b border-white/10 px-5 py-4">
          <div className="min-w-0">
            <h2 className="text-base font-semibold text-slate-100">{title}</h2>
            {description && <p className="mt-0.5 text-sm text-slate-400">{description}</p>}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="shrink-0 rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-white/5 hover:text-slate-100"
            aria-label="Close dialog"
          >
            <X size={18} />
          </button>
        </header>
        <div className="max-h-[70vh] overflow-y-auto px-5 py-4">{children}</div>
        {footer && (
          <footer className="flex flex-wrap items-center justify-end gap-2 border-t border-white/10 px-5 py-4">
            {footer}
          </footer>
        )}
      </div>
    </div>
  )
}

export function ConfirmDialog({
  open,
  onClose,
  onConfirm,
  title = 'Are you sure?',
  message,
  confirmLabel = 'Confirm',
  tone = 'danger',
  busy = false,
}) {
  return (
    <Modal
      open={open}
      onClose={onClose}
      title={title}
      size="sm"
      footer={
        <>
          <button type="button" className="btn-secondary" onClick={onClose} disabled={busy}>
            Cancel
          </button>
          <button
            type="button"
            className={tone === 'danger' ? 'btn-danger' : 'btn-primary'}
            onClick={onConfirm}
            disabled={busy}
          >
            {busy && <Spinner size={15} />}
            {confirmLabel}
          </button>
        </>
      }
    >
      <p className="text-sm leading-relaxed text-slate-300">{message}</p>
    </Modal>
  )
}

/* ---------------------------------------------------------------- pagination */

export function Pagination({ pagination, onPageChange, className = '' }) {
  if (!pagination || pagination.pages <= 1) return null
  const { page, pages, total, per_page: perPage } = pagination
  const from = (page - 1) * perPage + 1
  const to = Math.min(page * perPage, total)

  const numbers = []
  const start = Math.max(1, Math.min(page - 2, pages - 4))
  for (let index = start; index <= Math.min(start + 4, pages); index += 1) numbers.push(index)

  return (
    <div
      className={`flex flex-wrap items-center justify-between gap-3 border-t border-white/10 px-5 py-3.5 ${className}`}
    >
      <p className="text-xs text-slate-400">
        Showing <span className="text-slate-200">{from}</span>-
        <span className="text-slate-200">{to}</span> of{' '}
        <span className="text-slate-200">{total.toLocaleString()}</span>
      </p>
      <div className="flex items-center gap-1">
        <button
          type="button"
          className="btn-ghost btn-sm"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
          aria-label="Previous page"
        >
          <ChevronLeft size={15} />
        </button>
        {numbers.map((number) => (
          <button
            key={number}
            type="button"
            onClick={() => onPageChange(number)}
            aria-current={number === page ? 'page' : undefined}
            className={`min-w-[2rem] rounded-md px-2 py-1.5 text-xs font-medium transition-colors ${
              number === page
                ? 'bg-accent/15 text-accent'
                : 'text-slate-400 hover:bg-white/5 hover:text-slate-100'
            }`}
          >
            {number}
          </button>
        ))}
        <button
          type="button"
          className="btn-ghost btn-sm"
          disabled={page >= pages}
          onClick={() => onPageChange(page + 1)}
          aria-label="Next page"
        >
          <ChevronRight size={15} />
        </button>
      </div>
    </div>
  )
}

/* --------------------------------------------------------------------- misc */

export function DetailRow({ label, value, mono = false, className = '' }) {
  return (
    <div className={`flex items-start justify-between gap-4 py-2 ${className}`}>
      <dt className="shrink-0 text-xs uppercase tracking-wider text-slate-500">{label}</dt>
      <dd className={`text-right text-sm text-slate-200 ${mono ? 'mono' : ''}`}>{value ?? '-'}</dd>
    </div>
  )
}

export function InfoNote({ children, tone = 'info', className = '' }) {
  const tones = {
    info: 'border-info/30 bg-info/[0.07] text-info',
    warning: 'border-warn/30 bg-warn/[0.07] text-warn',
    danger: 'border-danger/30 bg-danger/[0.07] text-danger',
    success: 'border-safe/30 bg-safe/[0.07] text-safe',
  }
  return (
    <div className={`rounded-lg border ${tones[tone]} px-3.5 py-2.5 ${className}`}>
      <p className="text-xs leading-relaxed text-slate-300">{children}</p>
    </div>
  )
}
