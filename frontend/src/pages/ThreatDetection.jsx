/**
 * Threat Detection page (FR-04, FR-05).
 *
 * Submitting the form calls POST /api/events/analyze. The backend validates the
 * payload, runs the hybrid engine, stores the event, the detection result and -
 * when warranted - an alert and an incident. The verdict rendered below is the
 * backend's own explanation, not a client-side calculation.
 */
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  AlertCircle,
  ArrowRight,
  Beaker,
  Info,
  Radar,
  RotateCcw,
  ShieldCheck,
  Siren,
  Target,
  Zap,
} from 'lucide-react'
import { useApi } from '../hooks/useApi'
import api from '../services/api'
import { useToast } from '../context/ToastContext'
import {
  ErrorState,
  Field,
  InfoNote,
  PageHeader,
  Panel,
  RiskBar,
  SeverityBadge,
  Spinner,
} from '../components/ui'
import { SEVERITY_COLORS, formatBytes, formatDuration, percent } from '../utils/format'

const PROTOCOLS = ['TCP', 'UDP', 'ICMP', 'HTTP', 'HTTPS', 'SSH', 'FTP', 'DNS', 'SMTP', 'RDP']
const EVENT_TYPES = [
  'network_traffic',
  'authentication',
  'web_request',
  'file_access',
  'process_execution',
  'dns_query',
  'firewall',
  'vpn_session',
  'database_query',
  'email_gateway',
]

const EMPTY_FORM = {
  source_ip: '',
  destination_ip: '',
  source_port: '',
  destination_port: '',
  protocol: 'TCP',
  event_type: 'network_traffic',
  request_count: '0',
  failed_login_attempts: '0',
  packet_count: '0',
  bytes_transferred: '0',
  connection_duration: '0',
  timestamp: '',
}

const NUMERIC_FIELDS = [
  { name: 'request_count', label: 'Request Count', hint: 'Connections or requests in the window' },
  { name: 'failed_login_attempts', label: 'Failed Login Attempts', hint: 'Rejected authentications' },
  { name: 'packet_count', label: 'Packet Count', hint: 'Total packets observed' },
  { name: 'bytes_transferred', label: 'Bytes Transferred', hint: 'Total payload in bytes' },
  { name: 'connection_duration', label: 'Connection Duration (s)', hint: 'Seconds the session lasted' },
]

function ScoreRing({ score, severity }) {
  const value = Math.max(0, Math.min(100, Number(score) || 0))
  const radius = 58
  const circumference = 2 * Math.PI * radius
  const color = SEVERITY_COLORS[severity] || '#22d3ee'
  return (
    <div className="relative h-40 w-40 shrink-0">
      <svg viewBox="0 0 140 140" className="h-full w-full -rotate-90">
        <circle cx="70" cy="70" r={radius} fill="none" stroke="rgba(148,163,184,0.16)" strokeWidth="10" />
        <circle
          cx="70"
          cy="70"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference - (value / 100) * circumference}
          style={{ transition: 'stroke-dashoffset 900ms ease-out' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-bold tracking-tight" style={{ color }}>
          {value}
        </span>
        <span className="text-[0.65rem] uppercase tracking-wider text-slate-500">risk / 100</span>
      </div>
    </div>
  )
}

function ResultPanel({ result, onOpenAlert, onOpenIncident }) {
  const benign = !result.is_threat
  return (
    <div className="space-y-4">
      <div
        className={`panel border p-5 ${
          benign ? 'border-safe/35 bg-safe/[0.04]' : 'border-danger/35 bg-danger/[0.04]'
        }`}
      >
        <div className="flex flex-col items-center gap-6 sm:flex-row sm:items-start">
          <ScoreRing score={result.risk_score} severity={result.severity} />

          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              {benign ? (
                <ShieldCheck size={20} className="text-safe" />
              ) : (
                <Siren size={20} className="text-danger" />
              )}
              <h3 className="text-xl font-semibold tracking-tight text-slate-100">
                {result.classification}
              </h3>
              <SeverityBadge severity={result.severity} />
            </div>

            <dl className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
              {[
                { label: 'Risk score', value: `${result.risk_score}/100` },
                { label: 'Severity', value: result.severity },
                { label: 'Confidence', value: percent(result.confidence, 1) },
                { label: 'Verdict', value: benign ? 'Benign' : 'Threat' },
              ].map((item) => (
                <div key={item.label} className="rounded-lg border border-white/10 bg-navy-950/50 px-3 py-2">
                  <dt className="text-[0.62rem] uppercase tracking-wider text-slate-500">
                    {item.label}
                  </dt>
                  <dd className="mt-0.5 text-sm font-semibold text-slate-100">{item.value}</dd>
                </div>
              ))}
            </dl>

            {result.mitre_tactic && (
              <p className="mt-3 flex items-center gap-1.5 text-xs text-slate-400">
                <Target size={13} className="text-accent" />
                Mapped tactic: <span className="text-slate-300">{result.mitre_tactic}</span>
              </p>
            )}
          </div>
        </div>
      </div>

      <Panel title="Why the engine reached this verdict" subtitle="Every detection is explainable">
        <ul className="space-y-2.5">
          {result.reasons.map((reason, index) => (
            <li key={index} className="flex items-start gap-2.5 text-sm text-slate-300">
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
              {reason}
            </li>
          ))}
        </ul>

        <div className="mt-5 grid gap-3 sm:grid-cols-3">
          {[
            { key: 'rule', label: 'Rule bank', hint: 'Deterministic behavioural rules' },
            { key: 'anomaly', label: 'Statistical', hint: 'Z-score against the baseline' },
            { key: 'ml', label: 'Machine learning', hint: 'Trained classifier + isolation forest' },
          ].map((detector) => (
            <div key={detector.key} className="rounded-lg border border-white/10 bg-navy-950/50 p-3">
              <div className="flex items-center justify-between">
                <p className="text-xs font-medium text-slate-300">{detector.label}</p>
                <span className="mono text-xs text-slate-200">
                  {result.scores[detector.key]?.toFixed(1) ?? '0.0'}
                </span>
              </div>
              <RiskBar score={result.scores[detector.key]} showValue={false} className="mt-2" />
              <p className="mt-1.5 text-[0.65rem] text-slate-500">{detector.hint}</p>
            </div>
          ))}
        </div>

        {result.triggered_rules?.length > 0 && (
          <div className="mt-4">
            <p className="field-label">Rules that fired</p>
            <div className="flex flex-wrap gap-2">
              {result.triggered_rules.map((rule) => (
                <span
                  key={rule.category}
                  className="badge border-white/15 bg-navy-800 text-slate-300"
                >
                  {rule.category}
                  <span className="mono ml-1 text-slate-500">{rule.score}</span>
                </span>
              ))}
            </div>
          </div>
        )}
      </Panel>

      <Panel title="Recommended defensive action" subtitle="Containment guidance for the analyst">
        <p className="text-sm leading-relaxed text-slate-300">{result.recommended_action}</p>

        {(result.alert || result.incident) && (
          <div className="mt-4 flex flex-wrap gap-2">
            {result.alert && (
              <button type="button" onClick={onOpenAlert} className="btn-secondary btn-sm">
                <Siren size={14} />
                Alert {result.alert.alert_code} raised
                <ArrowRight size={13} />
              </button>
            )}
            {result.incident && (
              <button type="button" onClick={onOpenIncident} className="btn-secondary btn-sm">
                Incident {result.incident.incident_code} opened
                <ArrowRight size={13} />
              </button>
            )}
          </div>
        )}
      </Panel>

      <Panel title="Feature summary" subtitle="What the engine measured from your input">
        <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3">
          {Object.entries(result.feature_summary || {}).map(([label, value]) => (
            <div key={label} className="rounded-lg border border-white/10 bg-navy-950/50 px-3 py-2">
              <p className="text-[0.62rem] uppercase tracking-wider text-slate-500">{label}</p>
              <p className="mono mt-0.5 text-sm text-slate-200">
                {typeof value === 'boolean' ? (value ? 'Yes' : 'No') : value}
              </p>
            </div>
          ))}
        </div>
        <p className="mt-4 text-xs text-slate-500">
          Engine: {result.model_used} v{result.engine_version} - analysed in{' '}
          {result.analysis_time_ms?.toFixed(2)} ms
          {result.persisted === false && ' - dry run, nothing was stored'}
        </p>
      </Panel>
    </div>
  )
}

export default function ThreatDetection() {
  const toast = useToast()
  const navigate = useNavigate()
  const [form, setForm] = useState(EMPTY_FORM)
  const [errors, setErrors] = useState({})
  const [result, setResult] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [persist, setPersist] = useState(true)
  const [failure, setFailure] = useState(null)

  const { data: samples } = useApi(() => api.sampleEvents(), [])

  const setField = (name, value) => {
    setForm((current) => ({ ...current, [name]: value }))
    setErrors((current) => {
      if (!current[name]) return current
      const next = { ...current }
      delete next[name]
      return next
    })
  }

  const validate = () => {
    const found = {}
    const ipPattern = /^(\d{1,3}\.){3}\d{1,3}$|^[0-9a-fA-F:]+$/

    if (!form.source_ip.trim()) found.source_ip = 'Source IP is required.'
    else if (!ipPattern.test(form.source_ip.trim())) found.source_ip = 'Enter a valid IP address.'

    if (form.destination_ip.trim() && !ipPattern.test(form.destination_ip.trim()))
      found.destination_ip = 'Enter a valid IP address.'

    ;['source_port', 'destination_port'].forEach((field) => {
      const value = form[field]
      if (value !== '' && (Number.isNaN(Number(value)) || Number(value) < 0 || Number(value) > 65535))
        found[field] = 'Port must be between 0 and 65535.'
    })

    NUMERIC_FIELDS.forEach(({ name, label }) => {
      const value = form[name]
      if (value !== '' && (Number.isNaN(Number(value)) || Number(value) < 0))
        found[name] = `${label} must be a non-negative number.`
    })

    setErrors(found)
    return Object.keys(found).length === 0
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setFailure(null)
    if (!validate()) {
      toast.warning('Please correct the highlighted fields.')
      return
    }

    setSubmitting(true)
    try {
      const payload = Object.fromEntries(
        Object.entries(form).filter(([, value]) => value !== '' && value !== null),
      )
      const analysis = await api.analyzeEvent(payload, persist)
      setResult(analysis)
      if (analysis.is_threat) {
        toast.error(`${analysis.classification} detected - risk ${analysis.risk_score}/100.`)
      } else {
        toast.success('Analysis complete: no threat indicators found.')
      }
    } catch (error) {
      setFailure(error)
      if (error.details?.field) setErrors({ [error.details.field]: error.message })
      toast.error(error.message)
    } finally {
      setSubmitting(false)
    }
  }

  const loadSample = (sample) => {
    setResult(null)
    setFailure(null)
    setErrors({})
    setForm({
      ...EMPTY_FORM,
      ...Object.fromEntries(
        Object.entries(sample.payload).map(([key, value]) => [key, String(value)]),
      ),
    })
    toast.info(`Loaded sample: ${sample.label}`)
  }

  const reset = () => {
    setForm(EMPTY_FORM)
    setErrors({})
    setResult(null)
    setFailure(null)
  }

  return (
    <>
      <PageHeader
        title="Threat Detection"
        description="Submit a security event for analysis. The hybrid engine returns a classification, a 0-100 risk score, a confidence value and the reasons behind its verdict."
        icon={Radar}
      >
        <button type="button" onClick={reset} className="btn-secondary btn-sm">
          <RotateCcw size={14} />
          Reset form
        </button>
      </PageHeader>

      <div className="grid gap-4 xl:grid-cols-5">
        {/* Input form */}
        <div className="space-y-4 xl:col-span-2">
          <Panel title="Security event" subtitle="Describe the observed activity">
            <form onSubmit={handleSubmit} className="space-y-4" noValidate>
              <div className="grid gap-3 sm:grid-cols-2">
                <Field label="Source IP" error={errors.source_ip} required>
                  <input
                    type="text"
                    value={form.source_ip}
                    onChange={(event) => setField('source_ip', event.target.value)}
                    placeholder="203.0.113.66"
                    className={`field-input mono ${errors.source_ip ? 'field-input-error' : ''}`}
                  />
                </Field>
                <Field label="Destination IP" error={errors.destination_ip}>
                  <input
                    type="text"
                    value={form.destination_ip}
                    onChange={(event) => setField('destination_ip', event.target.value)}
                    placeholder="10.0.1.20"
                    className={`field-input mono ${errors.destination_ip ? 'field-input-error' : ''}`}
                  />
                </Field>
                <Field label="Source Port" error={errors.source_port}>
                  <input
                    type="number"
                    value={form.source_port}
                    onChange={(event) => setField('source_port', event.target.value)}
                    placeholder="44122"
                    className={`field-input mono ${errors.source_port ? 'field-input-error' : ''}`}
                  />
                </Field>
                <Field label="Destination Port" error={errors.destination_port}>
                  <input
                    type="number"
                    value={form.destination_port}
                    onChange={(event) => setField('destination_port', event.target.value)}
                    placeholder="22"
                    className={`field-input mono ${errors.destination_port ? 'field-input-error' : ''}`}
                  />
                </Field>
                <Field label="Protocol">
                  <select
                    value={form.protocol}
                    onChange={(event) => setField('protocol', event.target.value)}
                    className="field-input cursor-pointer"
                  >
                    {PROTOCOLS.map((protocol) => (
                      <option key={protocol} value={protocol} className="bg-navy-900">
                        {protocol}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="Event Type">
                  <select
                    value={form.event_type}
                    onChange={(event) => setField('event_type', event.target.value)}
                    className="field-input cursor-pointer"
                  >
                    {EVENT_TYPES.map((type) => (
                      <option key={type} value={type} className="bg-navy-900">
                        {type.replace(/_/g, ' ')}
                      </option>
                    ))}
                  </select>
                </Field>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                {NUMERIC_FIELDS.map((field) => (
                  <Field key={field.name} label={field.label} error={errors[field.name]} hint={field.hint}>
                    <input
                      type="number"
                      min="0"
                      step="any"
                      value={form[field.name]}
                      onChange={(event) => setField(field.name, event.target.value)}
                      className={`field-input mono ${errors[field.name] ? 'field-input-error' : ''}`}
                    />
                  </Field>
                ))}
                <Field label="Timestamp" hint="Leave blank to use the current time">
                  <input
                    type="datetime-local"
                    value={form.timestamp}
                    onChange={(event) => setField('timestamp', event.target.value)}
                    className="field-input"
                  />
                </Field>
              </div>

              {/* Live preview of the derived values the engine will use */}
              <div className="rounded-lg border border-white/10 bg-navy-950/50 px-3.5 py-3">
                <p className="mb-2 text-[0.62rem] uppercase tracking-wider text-slate-500">
                  Derived from your input
                </p>
                <div className="grid grid-cols-3 gap-3 text-xs">
                  <div>
                    <p className="text-slate-500">Volume</p>
                    <p className="mono text-slate-200">
                      {formatBytes(Number(form.bytes_transferred) || 0)}
                    </p>
                  </div>
                  <div>
                    <p className="text-slate-500">Duration</p>
                    <p className="mono text-slate-200">
                      {formatDuration(Number(form.connection_duration) || 0)}
                    </p>
                  </div>
                  <div>
                    <p className="text-slate-500">Requests/sec</p>
                    <p className="mono text-slate-200">
                      {(
                        (Number(form.request_count) || 0) /
                        Math.max(Number(form.connection_duration) || 1, 1)
                      ).toFixed(2)}
                    </p>
                  </div>
                </div>
              </div>

              <label className="flex cursor-pointer select-none items-start gap-2.5 text-sm text-slate-400">
                <input
                  type="checkbox"
                  checked={persist}
                  onChange={(event) => setPersist(event.target.checked)}
                  className="mt-0.5 h-4 w-4 cursor-pointer rounded border-white/20 bg-navy-950 text-accent focus:ring-accent/50"
                />
                <span>
                  Store this event in the database
                  <span className="block text-xs text-slate-500">
                    When off, the engine runs a dry run and no alert or incident is created.
                  </span>
                </span>
              </label>

              <button type="submit" className="btn-primary w-full" disabled={submitting}>
                {submitting ? (
                  <>
                    <Spinner size={16} />
                    Analysing...
                  </>
                ) : (
                  <>
                    <Zap size={16} />
                    Analyze Threat
                  </>
                )}
              </button>
            </form>
          </Panel>

          <Panel
            title="Sample scenarios"
            subtitle="Load a prepared payload to demonstrate each detection category"
          >
            <div className="space-y-2">
              {(samples || []).map((sample) => (
                <button
                  key={sample.label}
                  type="button"
                  onClick={() => loadSample(sample)}
                  className="flex w-full items-center justify-between gap-3 rounded-lg border border-white/10 bg-navy-950/40 px-3.5 py-2.5 text-left transition-all hover:border-accent/40 hover:bg-navy-850"
                >
                  <span className="min-w-0">
                    <span className="block truncate text-sm text-slate-200">{sample.label}</span>
                    <span className="block truncate text-xs text-slate-500">
                      Expected: {sample.expected}
                    </span>
                  </span>
                  <Beaker size={15} className="shrink-0 text-accent" />
                </button>
              ))}
            </div>
          </Panel>
        </div>

        {/* Verdict */}
        <div className="xl:col-span-3">
          {failure ? (
            <div className="panel">
              <ErrorState error={failure} onRetry={() => setFailure(null)} />
            </div>
          ) : result ? (
            <ResultPanel
              result={result}
              onOpenAlert={() => navigate(`/alerts?focus=${result.alert.id}`)}
              onOpenIncident={() => navigate(`/incidents/${result.incident.id}`)}
            />
          ) : (
            <Panel title="Analysis result" subtitle="Awaiting an event to analyse">
              <div className="flex flex-col items-center justify-center gap-4 py-14 text-center">
                <span className="rounded-full border border-white/10 bg-navy-800/70 p-4 text-slate-500">
                  <Radar size={30} />
                </span>
                <div>
                  <h3 className="text-sm font-semibold text-slate-200">No analysis yet</h3>
                  <p className="mx-auto mt-1 max-w-md text-sm text-slate-400">
                    Fill in the event form or load a sample scenario, then press{' '}
                    <span className="text-accent">Analyze Threat</span>. The verdict, the risk score
                    and the reasons behind it will appear here.
                  </p>
                </div>
                <InfoNote className="mx-auto max-w-lg text-left">
                  <span className="flex items-start gap-2">
                    <Info size={13} className="mt-0.5 shrink-0" />
                    Severity bands: LOW 0-25, MEDIUM 26-50, HIGH 51-75, CRITICAL 76-100. An alert is
                    raised from MEDIUM upwards; an incident opens automatically at CRITICAL.
                  </span>
                </InfoNote>
              </div>
            </Panel>
          )}
        </div>
      </div>

      {Object.keys(errors).length > 0 && (
        <div className="mt-4 flex items-start gap-2.5 rounded-lg border border-danger/40 bg-danger/10 p-3.5">
          <AlertCircle size={16} className="mt-0.5 shrink-0 text-danger" />
          <div className="text-sm text-slate-300">
            <p className="font-medium text-slate-100">Please fix the following before analysing:</p>
            <ul className="mt-1 list-inside list-disc space-y-0.5 text-xs">
              {Object.entries(errors).map(([field, message]) => (
                <li key={field}>{message}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </>
  )
}
