/** Settings page - profile, notifications, detection sensitivity and system status. */
import { useEffect, useState } from 'react'
import {
  Activity,
  Bell,
  Cpu,
  Database,
  Gauge,
  KeyRound,
  Palette,
  RefreshCw,
  Save,
  Server,
  Settings as SettingsIcon,
  ShieldCheck,
  User as UserIcon,
} from 'lucide-react'
import { useApi } from '../hooks/useApi'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import {
  DetailRow,
  ErrorState,
  Field,
  InfoNote,
  PageHeader,
  Panel,
  SkeletonTable,
  Spinner,
  StatusBadge,
} from '../components/ui'
import { formatDateTime, formatNumber, timeAgo, titleCase } from '../utils/format'

const TABS = [
  { id: 'profile', label: 'Profile', icon: UserIcon },
  { id: 'notifications', label: 'Notifications', icon: Bell },
  { id: 'detection', label: 'Detection', icon: Gauge },
  { id: 'system', label: 'System status', icon: Server },
  { id: 'audit', label: 'Audit log', icon: Activity },
]

const SENSITIVITY_MARKS = [
  { value: 0.5, label: 'Relaxed', hint: 'Fewer alerts; only strong signals are escalated.' },
  { value: 1.0, label: 'Balanced', hint: 'The default calibration used by the seeded data.' },
  { value: 1.5, label: 'Aggressive', hint: 'More alerts, and more false positives to triage.' },
]

function Toggle({ checked, onChange, label, description, disabled }) {
  return (
    <label className="flex cursor-pointer items-start justify-between gap-4 rounded-lg border border-white/10 bg-navy-950/40 px-4 py-3">
      <span className="min-w-0">
        <span className="block text-sm text-slate-200">{label}</span>
        {description && <span className="mt-0.5 block text-xs text-slate-500">{description}</span>}
      </span>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        aria-label={label}
        disabled={disabled}
        onClick={() => onChange(!checked)}
        className={`relative mt-0.5 h-6 w-11 shrink-0 rounded-full transition-colors ${
          checked ? 'bg-accent' : 'bg-navy-600'
        } ${disabled ? 'cursor-not-allowed opacity-60' : ''}`}
      >
        <span
          className={`absolute top-0.5 h-5 w-5 rounded-full bg-white transition-transform ${
            checked ? 'translate-x-[1.375rem]' : 'translate-x-0.5'
          }`}
        />
      </button>
    </label>
  )
}

export default function Settings() {
  const { user, updateUser } = useAuth()
  const toast = useToast()
  const [tab, setTab] = useState('profile')

  const [profile, setProfile] = useState({ full_name: '', email: '', department: '' })
  const [preferences, setPreferences] = useState({
    notify_email: true,
    notify_critical_only: false,
    detection_sensitivity: 1.0,
    theme: 'dark',
  })
  const [passwords, setPasswords] = useState({ current_password: '', new_password: '', confirm: '' })
  const [errors, setErrors] = useState({})
  const [saving, setSaving] = useState(null)

  const { data: status, error: statusError, loading: statusLoading, refresh: refreshStatus } =
    useApi(() => api.systemStatus(), [])
  const { data: auditLog, loading: auditLoading, refresh: refreshAudit } = useApi(
    () => api.auditLogs(60),
    [],
  )

  useEffect(() => {
    if (user) {
      setProfile({
        full_name: user.full_name || '',
        email: user.email || '',
        department: user.department || '',
      })
      if (user.preferences) setPreferences(user.preferences)
    }
  }, [user])

  const saveProfile = async () => {
    const found = {}
    if (!profile.full_name.trim()) found.full_name = 'Name is required.'
    if (!/^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$/.test(profile.email.trim()))
      found.email = 'Enter a valid email address.'
    setErrors(found)
    if (Object.keys(found).length) return

    setSaving('profile')
    try {
      const updated = await api.updateProfile(profile)
      updateUser(updated)
      toast.success('Profile updated.')
    } catch (caught) {
      toast.error(caught.message)
      if (caught.details?.field) setErrors({ [caught.details.field]: caught.message })
    } finally {
      setSaving(null)
    }
  }

  const savePreferences = async (overrides = {}) => {
    const payload = { ...preferences, ...overrides }
    setPreferences(payload)
    setSaving('preferences')
    try {
      const updated = await api.updatePreferences(payload)
      updateUser(updated)
      toast.success('Preferences saved.')
    } catch (caught) {
      toast.error(caught.message)
    } finally {
      setSaving(null)
    }
  }

  const changePassword = async () => {
    const found = {}
    if (!passwords.current_password) found.current_password = 'Enter your current password.'
    if (passwords.new_password.length < 6)
      found.new_password = 'The new password must be at least 6 characters.'
    if (passwords.new_password !== passwords.confirm)
      found.confirm = 'The two passwords do not match.'
    setErrors(found)
    if (Object.keys(found).length) return

    setSaving('password')
    try {
      await api.changePassword({
        current_password: passwords.current_password,
        new_password: passwords.new_password,
      })
      toast.success('Password changed successfully.')
      setPasswords({ current_password: '', new_password: '', confirm: '' })
    } catch (caught) {
      toast.error(caught.message)
    } finally {
      setSaving(null)
    }
  }

  const reloadModel = async () => {
    setSaving('model')
    try {
      const info = await api.reloadModel()
      toast.success(`Detection engine reloaded in ${info.mode} mode.`)
      refreshStatus({ quiet: true })
    } catch (caught) {
      toast.error(caught.message)
    } finally {
      setSaving(null)
    }
  }

  return (
    <>
      <PageHeader
        title="Settings"
        description="Manage your profile, alerting preferences, detection sensitivity and inspect system status."
        icon={SettingsIcon}
      />

      <div className="mb-4 flex flex-wrap gap-1.5 border-b border-white/10 pb-px">
        {TABS.map((item) => {
          const Icon = item.icon
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => setTab(item.id)}
              className={`flex items-center gap-2 rounded-t-lg px-3.5 py-2.5 text-sm font-medium transition-colors ${
                tab === item.id
                  ? 'border-b-2 border-accent text-accent'
                  : 'border-b-2 border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Icon size={15} />
              {item.label}
            </button>
          )
        })}
      </div>

      {tab === 'profile' && (
        <div className="grid gap-4 lg:grid-cols-2">
          <Panel title="User profile" subtitle="Your identity within the console">
            <div className="space-y-4">
              <Field label="Full name" error={errors.full_name} required>
                <input
                  type="text"
                  value={profile.full_name}
                  onChange={(event) =>
                    setProfile((current) => ({ ...current, full_name: event.target.value }))
                  }
                  className={`field-input ${errors.full_name ? 'field-input-error' : ''}`}
                />
              </Field>
              <Field label="Email address" error={errors.email} required>
                <input
                  type="email"
                  value={profile.email}
                  onChange={(event) =>
                    setProfile((current) => ({ ...current, email: event.target.value }))
                  }
                  className={`field-input ${errors.email ? 'field-input-error' : ''}`}
                />
              </Field>
              <Field label="Department">
                <input
                  type="text"
                  value={profile.department}
                  onChange={(event) =>
                    setProfile((current) => ({ ...current, department: event.target.value }))
                  }
                  placeholder="Security Operations Centre"
                  className="field-input"
                />
              </Field>

              <dl className="divide-y divide-white/[0.06] rounded-lg border border-white/10 bg-navy-950/40 px-4">
                <DetailRow label="Role" value={titleCase(user?.role || '')} />
                <DetailRow label="Account created" value={formatDateTime(user?.created_at)} />
                <DetailRow label="Last sign-in" value={formatDateTime(user?.last_login)} />
              </dl>

              <button
                type="button"
                onClick={saveProfile}
                className="btn-primary"
                disabled={saving === 'profile'}
              >
                {saving === 'profile' ? <Spinner size={15} /> : <Save size={15} />}
                Save profile
              </button>
            </div>
          </Panel>

          <Panel title="Change password" subtitle="Passwords are stored as salted PBKDF2 hashes">
            <div className="space-y-4">
              <Field label="Current password" error={errors.current_password} required>
                <input
                  type="password"
                  autoComplete="current-password"
                  value={passwords.current_password}
                  onChange={(event) =>
                    setPasswords((current) => ({ ...current, current_password: event.target.value }))
                  }
                  className={`field-input ${errors.current_password ? 'field-input-error' : ''}`}
                />
              </Field>
              <Field
                label="New password"
                error={errors.new_password}
                hint="At least 6 characters"
                required
              >
                <input
                  type="password"
                  autoComplete="new-password"
                  value={passwords.new_password}
                  onChange={(event) =>
                    setPasswords((current) => ({ ...current, new_password: event.target.value }))
                  }
                  className={`field-input ${errors.new_password ? 'field-input-error' : ''}`}
                />
              </Field>
              <Field label="Confirm new password" error={errors.confirm} required>
                <input
                  type="password"
                  autoComplete="new-password"
                  value={passwords.confirm}
                  onChange={(event) =>
                    setPasswords((current) => ({ ...current, confirm: event.target.value }))
                  }
                  className={`field-input ${errors.confirm ? 'field-input-error' : ''}`}
                />
              </Field>

              <button
                type="button"
                onClick={changePassword}
                className="btn-secondary"
                disabled={saving === 'password'}
              >
                {saving === 'password' ? <Spinner size={15} /> : <KeyRound size={15} />}
                Change password
              </button>

              <InfoNote tone="warning">
                Changing the seeded demo password means the credentials shown on the login screen
                will no longer work until the database is re-seeded.
              </InfoNote>
            </div>
          </Panel>
        </div>
      )}

      {tab === 'notifications' && (
        <div className="grid gap-4 lg:grid-cols-2">
          <Panel title="Notification settings" subtitle="How you are told about new detections">
            <div className="space-y-3">
              <Toggle
                label="In-app alert notifications"
                description="Show new alerts in the bell menu in the top bar."
                checked={preferences.notify_email}
                onChange={(value) => savePreferences({ notify_email: value })}
                disabled={saving === 'preferences'}
              />
              <Toggle
                label="Critical severity only"
                description="Suppress notifications for anything below CRITICAL."
                checked={preferences.notify_critical_only}
                onChange={(value) => savePreferences({ notify_critical_only: value })}
                disabled={saving === 'preferences'}
              />
            </div>
            <InfoNote className="mt-4">
              This prototype delivers notifications inside the console only. No email is sent -
              outbound mail is deliberately out of scope for an academic build.
            </InfoNote>
          </Panel>

          <Panel title="Appearance" subtitle="Theme preference">
            <div className="grid grid-cols-2 gap-3">
              {['dark', 'light'].map((theme) => (
                <button
                  key={theme}
                  type="button"
                  onClick={() => savePreferences({ theme })}
                  className={`flex flex-col items-center gap-2 rounded-lg border px-4 py-5 transition-all ${
                    preferences.theme === theme
                      ? 'border-accent/50 bg-accent/[0.07]'
                      : 'border-white/10 bg-navy-950/40 hover:border-accent/30'
                  }`}
                >
                  <Palette
                    size={20}
                    className={preferences.theme === theme ? 'text-accent' : 'text-slate-400'}
                  />
                  <span className="text-sm text-slate-200">{titleCase(theme)}</span>
                </button>
              ))}
            </div>
            <InfoNote tone="warning" className="mt-4">
              The preference is stored against your account, but this build ships the dark
              Security Operations Centre theme only. A light theme is listed under future
              enhancements in the README.
            </InfoNote>
          </Panel>
        </div>
      )}

      {tab === 'detection' && (
        <div className="grid gap-4 lg:grid-cols-2">
          <Panel
            title="Detection sensitivity"
            subtitle="Scales the fused risk score before the severity bands are applied"
          >
            <div className="space-y-5">
              <div>
                <input
                  type="range"
                  min="0.5"
                  max="1.5"
                  step="0.1"
                  value={preferences.detection_sensitivity}
                  onChange={(event) =>
                    setPreferences((current) => ({
                      ...current,
                      detection_sensitivity: Number(event.target.value),
                    }))
                  }
                  onMouseUp={() => savePreferences()}
                  onTouchEnd={() => savePreferences()}
                  className="w-full cursor-pointer accent-cyan-400"
                  aria-label="Detection sensitivity"
                />
                <div className="mt-2 flex justify-between text-xs text-slate-500">
                  <span>0.5 relaxed</span>
                  <span className="mono text-base font-semibold text-accent">
                    {Number(preferences.detection_sensitivity).toFixed(1)}
                  </span>
                  <span>1.5 aggressive</span>
                </div>
              </div>

              <div className="space-y-2">
                {SENSITIVITY_MARKS.map((mark) => (
                  <button
                    key={mark.value}
                    type="button"
                    onClick={() => savePreferences({ detection_sensitivity: mark.value })}
                    className={`flex w-full items-start gap-2.5 rounded-lg border px-3.5 py-2.5 text-left transition-all ${
                      Number(preferences.detection_sensitivity) === mark.value
                        ? 'border-accent/50 bg-accent/[0.07]'
                        : 'border-white/10 bg-navy-950/40 hover:border-accent/30'
                    }`}
                  >
                    <span className="mono mt-0.5 shrink-0 text-xs text-accent">{mark.value}</span>
                    <span className="min-w-0">
                      <span className="block text-sm text-slate-200">{mark.label}</span>
                      <span className="block text-xs text-slate-500">{mark.hint}</span>
                    </span>
                  </button>
                ))}
              </div>

              <InfoNote>
                The setting applies to events <em>you</em> analyse from now on. Previously stored
                detections keep the score they were given, so historical charts stay consistent.
              </InfoNote>
            </div>
          </Panel>

          <Panel title="Engine configuration" subtitle="Current thresholds and model state">
            {statusLoading && !status ? (
              <SkeletonTable rows={5} columns={2} />
            ) : statusError ? (
              <ErrorState error={statusError} onRetry={refreshStatus} />
            ) : (
              <div className="space-y-4">
                <dl className="divide-y divide-white/[0.06]">
                  <DetailRow label="Engine mode" value={status?.detection_engine?.mode} mono />
                  <DetailRow
                    label="ML models loaded"
                    value={status?.detection_engine?.ml_available ? 'Yes' : 'No (rules + statistics)'}
                  />
                  <DetailRow
                    label="Engine version"
                    value={status?.detection_engine?.engine_version}
                    mono
                  />
                  <DetailRow label="Features" value={status?.detection_engine?.feature_count} mono />
                  <DetailRow
                    label="Baseline source"
                    value={
                      status?.detection_engine?.baseline_source === 'default'
                        ? 'Built-in default'
                        : 'Fitted (baseline.json)'
                    }
                  />
                  <DetailRow
                    label="Alert threshold"
                    value={`risk >= ${status?.thresholds?.alert_risk_threshold}`}
                    mono
                  />
                  <DetailRow
                    label="Incident threshold"
                    value={`risk >= ${status?.thresholds?.incident_risk_threshold}`}
                    mono
                  />
                </dl>

                {status?.model_metadata && (
                  <div className="rounded-lg border border-white/10 bg-navy-950/40 p-3.5">
                    <p className="field-label">Trained model</p>
                    <dl className="divide-y divide-white/[0.06]">
                      <DetailRow
                        label="Trained at"
                        value={formatDateTime(status.model_metadata.trained_at)}
                      />
                      <DetailRow
                        label="Samples"
                        value={formatNumber(status.model_metadata.samples)}
                        mono
                      />
                      <DetailRow
                        label="Hold-out accuracy"
                        value={`${(status.model_metadata.holdout_accuracy * 100).toFixed(2)}%`}
                        mono
                      />
                    </dl>
                    <p className="mt-2 text-[0.66rem] leading-relaxed text-slate-500">
                      {status.model_metadata.note}
                    </p>
                  </div>
                )}

                <button
                  type="button"
                  onClick={reloadModel}
                  className="btn-secondary"
                  disabled={saving === 'model'}
                >
                  {saving === 'model' ? <Spinner size={15} /> : <RefreshCw size={15} />}
                  Reload detection models
                </button>
                <p className="text-xs text-slate-500">
                  Run <span className="mono text-slate-400">python -m app.ml.train_model</span> in
                  the backend folder, then reload here to pick up the new artefacts without
                  restarting Flask.
                </p>
              </div>
            )}
          </Panel>
        </div>
      )}

      {tab === 'system' && (
        <div className="grid gap-4 lg:grid-cols-2">
          {statusLoading && !status ? (
            <SkeletonTable rows={8} columns={2} />
          ) : statusError ? (
            <div className="panel lg:col-span-2">
              <ErrorState error={statusError} onRetry={refreshStatus} />
            </div>
          ) : (
            <>
              <Panel
                title="API status"
                subtitle="Flask REST API"
                actions={<StatusBadge status="ACTIVE" />}
              >
                <dl className="divide-y divide-white/[0.06]">
                  <DetailRow label="Service" value="CyberGuard AI API" />
                  <DetailRow label="Version" value={status?.api?.version} mono />
                  <DetailRow label="Environment" value={status?.api?.environment} mono />
                  <DetailRow label="Registered endpoints" value={status?.api?.endpoints} mono />
                </dl>
                <p className="field-label mt-4">Allowed CORS origins</p>
                <div className="flex flex-wrap gap-1.5">
                  {(status?.api?.cors_origins || []).map((origin) => (
                    <span key={origin} className="badge mono border-white/15 bg-navy-800 text-slate-400">
                      {origin}
                    </span>
                  ))}
                </div>
              </Panel>

              <Panel
                title="Database status"
                subtitle={status?.database?.engine}
                actions={<StatusBadge status="ACTIVE" />}
              >
                <p className="mono mb-3 truncate rounded-lg border border-white/10 bg-navy-950/60 px-3 py-2 text-xs text-slate-400">
                  {status?.database?.uri}
                </p>
                <dl className="divide-y divide-white/[0.06]">
                  {Object.entries(status?.database?.tables || {}).map(([table, count]) => (
                    <DetailRow
                      key={table}
                      label={titleCase(table)}
                      value={formatNumber(count)}
                      mono
                    />
                  ))}
                </dl>
              </Panel>

              <Panel title="Subsystem health" subtitle="Live self-check" className="lg:col-span-2">
                <div className="grid gap-3 sm:grid-cols-2">
                  {(status?.health?.checks || []).map((check) => {
                    const icons = {
                      Database,
                      'Detection Engine': Cpu,
                      'ML Models': Gauge,
                      'Event Pipeline': Activity,
                    }
                    const Icon = icons[check.component] || ShieldCheck
                    const tone =
                      check.status === 'OPERATIONAL'
                        ? 'text-safe'
                        : check.status === 'FALLBACK' || check.status === 'BACKLOG'
                          ? 'text-warn'
                          : 'text-danger'
                    return (
                      <div
                        key={check.component}
                        className="flex items-start gap-3 rounded-lg border border-white/10 bg-navy-950/40 px-4 py-3"
                      >
                        <Icon size={17} className={`mt-0.5 shrink-0 ${tone}`} />
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <p className="text-sm text-slate-200">{check.component}</p>
                            <span className={`text-xs font-semibold ${tone}`}>{check.status}</span>
                          </div>
                          <p className="mt-0.5 text-xs text-slate-500">{check.detail}</p>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </Panel>
            </>
          )}
        </div>
      )}

      {tab === 'audit' && (
        <Panel
          title="Audit log"
          subtitle="Every state-changing action is recorded (FR-12)"
          bodyClassName="p-0"
          actions={
            <button
              type="button"
              onClick={() => refreshAudit()}
              className="btn-secondary btn-sm"
              disabled={auditLoading}
            >
              {auditLoading ? <Spinner size={14} /> : <RefreshCw size={14} />}
              Refresh
            </button>
          }
        >
          {auditLoading && !auditLog ? (
            <SkeletonTable rows={8} columns={5} />
          ) : (
            <div className="table-wrap max-h-[36rem] overflow-y-auto">
              <table className="data-table">
                <thead className="sticky top-0 z-10">
                  <tr>
                    <th>Action</th>
                    <th>Description</th>
                    <th>Entity</th>
                    <th>User</th>
                    <th>Result</th>
                    <th>When</th>
                  </tr>
                </thead>
                <tbody>
                  {(auditLog || []).map((entry) => (
                    <tr key={entry.id}>
                      <td className="mono whitespace-nowrap text-xs text-accent">{entry.action}</td>
                      <td className="max-w-md text-xs text-slate-300">{entry.description}</td>
                      <td className="whitespace-nowrap text-xs text-slate-500">
                        {entry.entity_type}
                        {entry.entity_id ? ` #${entry.entity_id}` : ''}
                      </td>
                      <td className="text-xs text-slate-400">{entry.user_name}</td>
                      <td>
                        <span
                          className={`badge ${
                            entry.status === 'SUCCESS'
                              ? 'border-safe/40 bg-safe/10 text-safe'
                              : 'border-danger/40 bg-danger/10 text-danger'
                          }`}
                        >
                          {entry.status}
                        </span>
                      </td>
                      <td className="whitespace-nowrap text-xs text-slate-500">
                        {timeAgo(entry.created_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Panel>
      )}
    </>
  )
}
