/** Incidents list page (FR-07). */
import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Eye, Plus, RefreshCw, ShieldAlert } from 'lucide-react'
import { useApi, useDebounced } from '../hooks/useApi'
import api from '../services/api'
import { useToast } from '../context/ToastContext'
import {
  EmptyState,
  ErrorState,
  Field,
  Modal,
  PageHeader,
  Pagination,
  Panel,
  RiskBar,
  SearchInput,
  Select,
  SeverityBadge,
  SkeletonTable,
  Spinner,
  StatusBadge,
} from '../components/ui'
import { formatDateTime, timeAgo } from '../utils/format'

const STATUS_OPTIONS = [
  { value: 'ALL', label: 'All statuses' },
  { value: 'NEW', label: 'New' },
  { value: 'OPEN', label: 'Open' },
  { value: 'INVESTIGATING', label: 'Investigating' },
  { value: 'CONTAINED', label: 'Contained' },
  { value: 'RESOLVED', label: 'Resolved' },
  { value: 'FALSE_POSITIVE', label: 'False positive' },
]

const SEVERITY_OPTIONS = [
  { value: 'ALL', label: 'All severities' },
  { value: 'CRITICAL', label: 'Critical' },
  { value: 'HIGH', label: 'High' },
  { value: 'MEDIUM', label: 'Medium' },
  { value: 'LOW', label: 'Low' },
]

const THREAT_TYPES = [
  'Brute Force Attempt',
  'Port Scanning Pattern',
  'Suspicious Login Activity',
  'Network Anomaly',
  'Data Transfer Anomaly',
  'Denial-of-Service Pattern',
  'Credential Abuse Pattern',
]

const PRIORITY_TONE = {
  P1: 'text-red-300',
  P2: 'text-rose-300',
  P3: 'text-warn',
  P4: 'text-slate-400',
}

function CreateIncidentModal({ open, onClose, analysts, onCreated }) {
  const toast = useToast()
  const [form, setForm] = useState({
    title: '',
    description: '',
    threat_type: 'Network Anomaly',
    severity: 'MEDIUM',
    source_ip: '',
    assigned_to: '',
  })
  const [errors, setErrors] = useState({})
  const [busy, setBusy] = useState(false)

  const setField = (name, value) => setForm((current) => ({ ...current, [name]: value }))

  const submit = async (event) => {
    event.preventDefault()
    const found = {}
    if (!form.title.trim()) found.title = 'A title is required.'
    else if (form.title.trim().length < 5) found.title = 'Use at least 5 characters.'
    if (form.source_ip && !/^(\d{1,3}\.){3}\d{1,3}$|^[0-9a-fA-F:]+$/.test(form.source_ip.trim()))
      found.source_ip = 'Enter a valid IP address.'
    setErrors(found)
    if (Object.keys(found).length) return

    setBusy(true)
    try {
      const payload = { ...form }
      if (!payload.assigned_to) delete payload.assigned_to
      if (!payload.source_ip) delete payload.source_ip
      const incident = await api.createIncident(payload)
      toast.success(`Incident ${incident.incident_code} created.`)
      setForm({
        title: '',
        description: '',
        threat_type: 'Network Anomaly',
        severity: 'MEDIUM',
        source_ip: '',
        assigned_to: '',
      })
      onCreated?.(incident)
      onClose()
    } catch (caught) {
      toast.error(caught.message)
      if (caught.details?.field) setErrors({ [caught.details.field]: caught.message })
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Raise an incident"
      description="Open a case manually when activity needs investigation but did not trigger an automatic incident."
      footer={
        <>
          <button type="button" className="btn-secondary" onClick={onClose} disabled={busy}>
            Cancel
          </button>
          <button type="button" className="btn-primary" onClick={submit} disabled={busy}>
            {busy && <Spinner size={15} />}
            Create incident
          </button>
        </>
      }
    >
      <form onSubmit={submit} className="space-y-4" noValidate>
        <Field label="Title" error={errors.title} required>
          <input
            type="text"
            value={form.title}
            onChange={(event) => setField('title', event.target.value)}
            placeholder="Repeated failed logins against the domain controller"
            className={`field-input ${errors.title ? 'field-input-error' : ''}`}
          />
        </Field>

        <Field label="Description" hint="What was observed and why it needs investigation">
          <textarea
            rows={3}
            value={form.description}
            onChange={(event) => setField('description', event.target.value)}
            className="field-input resize-none"
          />
        </Field>

        <div className="grid gap-3 sm:grid-cols-2">
          <Select
            label="Threat type"
            value={form.threat_type}
            onChange={(value) => setField('threat_type', value)}
            options={THREAT_TYPES.map((type) => ({ value: type, label: type }))}
          />
          <Select
            label="Severity"
            value={form.severity}
            onChange={(value) => setField('severity', value)}
            options={['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']}
          />
          <Field label="Source IP" error={errors.source_ip}>
            <input
              type="text"
              value={form.source_ip}
              onChange={(event) => setField('source_ip', event.target.value)}
              placeholder="203.0.113.66"
              className={`field-input mono ${errors.source_ip ? 'field-input-error' : ''}`}
            />
          </Field>
          <Select
            label="Assign to"
            value={form.assigned_to}
            onChange={(value) => setField('assigned_to', value)}
            options={[
              { value: '', label: 'Assign to me' },
              ...analysts.map((analyst) => ({
                value: String(analyst.id),
                label: `${analyst.full_name} (${analyst.role})`,
              })),
            ]}
          />
        </div>
      </form>
    </Modal>
  )
}

export default function Incidents() {
  const navigate = useNavigate()
  const [page, setPage] = useState(1)
  const [status, setStatus] = useState('ALL')
  const [severity, setSeverity] = useState('ALL')
  const [assignee, setAssignee] = useState('all')
  const [sort, setSort] = useState('newest')
  const [search, setSearch] = useState('')
  const [createOpen, setCreateOpen] = useState(false)

  const debouncedSearch = useDebounced(search, 400)

  const params = useMemo(
    () => ({
      page,
      per_page: 15,
      status,
      severity,
      assigned_to: assignee,
      sort,
      search: debouncedSearch || undefined,
    }),
    [page, status, severity, assignee, sort, debouncedSearch],
  )

  const { data, error, loading, refresh } = useApi(() => api.listIncidents(params), [params])

  useEffect(() => {
    setPage(1)
  }, [status, severity, assignee, sort, debouncedSearch])

  const incidents = data?.data || []
  const analysts = data?.filters?.analysts || []

  return (
    <>
      <PageHeader
        title="Incidents"
        description="Cases raised from critical detections or opened manually. Each one follows the incident lifecycle state machine."
        icon={ShieldAlert}
      >
        <button type="button" onClick={() => setCreateOpen(true)} className="btn-primary btn-sm">
          <Plus size={14} />
          New incident
        </button>
        <button type="button" onClick={() => refresh()} className="btn-secondary btn-sm" disabled={loading}>
          {loading ? <Spinner size={14} /> : <RefreshCw size={14} />}
          Refresh
        </button>
      </PageHeader>

      <Panel bodyClassName="p-0">
        <div className="grid gap-3 border-b border-white/10 p-4 sm:grid-cols-2 lg:grid-cols-5">
          <SearchInput
            value={search}
            onChange={setSearch}
            placeholder="Search incidents..."
            className="lg:col-span-2"
          />
          <Select value={status} onChange={setStatus} options={STATUS_OPTIONS} />
          <Select value={severity} onChange={setSeverity} options={SEVERITY_OPTIONS} />
          <Select
            value={assignee}
            onChange={setAssignee}
            options={[
              { value: 'all', label: 'All analysts' },
              { value: 'unassigned', label: 'Unassigned' },
              ...analysts.map((analyst) => ({
                value: String(analyst.id),
                label: analyst.full_name,
              })),
            ]}
          />
        </div>

        {loading && !data ? (
          <SkeletonTable rows={8} columns={7} />
        ) : error ? (
          <ErrorState error={error} onRetry={refresh} />
        ) : incidents.length === 0 ? (
          <EmptyState
            icon={ShieldAlert}
            title="No incidents found"
            message="Incidents open automatically when a detection reaches the CRITICAL band, or you can raise one manually."
            action={
              <button type="button" onClick={() => setCreateOpen(true)} className="btn-primary btn-sm">
                <Plus size={14} />
                New incident
              </button>
            }
          />
        ) : (
          <>
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Incident ID</th>
                    <th>Title</th>
                    <th>Threat type</th>
                    <th>Severity</th>
                    <th>Risk</th>
                    <th>Detected at</th>
                    <th>Assigned analyst</th>
                    <th>Status</th>
                    <th className="text-right">Open</th>
                  </tr>
                </thead>
                <tbody>
                  {incidents.map((incident) => (
                    <tr
                      key={incident.id}
                      className="cursor-pointer"
                      onClick={() => navigate(`/incidents/${incident.id}`)}
                    >
                      <td>
                        <span className="mono text-accent">{incident.incident_code}</span>
                        <span className={`mono ml-2 text-[0.65rem] ${PRIORITY_TONE[incident.priority]}`}>
                          {incident.priority}
                        </span>
                      </td>
                      <td className="max-w-xs truncate text-slate-200">{incident.title}</td>
                      <td className="text-xs text-slate-400">{incident.threat_type}</td>
                      <td>
                        <SeverityBadge severity={incident.severity} />
                      </td>
                      <td className="w-24">
                        <RiskBar score={incident.risk_score} />
                      </td>
                      <td className="whitespace-nowrap text-xs text-slate-400">
                        {formatDateTime(incident.detected_at)}
                        <span className="block text-[0.65rem] text-slate-600">
                          {timeAgo(incident.detected_at)}
                        </span>
                      </td>
                      <td className="text-xs text-slate-300">{incident.assigned_analyst}</td>
                      <td>
                        <StatusBadge status={incident.status} />
                      </td>
                      <td className="text-right">
                        <span className="btn-ghost btn-sm inline-flex">
                          <Eye size={14} />
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination pagination={data?.pagination} onPageChange={setPage} />
          </>
        )}
      </Panel>

      <CreateIncidentModal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        analysts={analysts}
        onCreated={(incident) => {
          refresh({ quiet: true })
          navigate(`/incidents/${incident.id}`)
        }}
      />
    </>
  )
}
