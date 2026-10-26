/**
 * Alerts page (FR-06).
 *
 * Filtering, searching and pagination are all performed server-side; the actions
 * (investigate / resolve / false positive / escalate) call PUT /api/alerts/<id>
 * and POST /api/alerts/<id>/escalate, which also write the audit trail.
 */
import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  ArrowUpRight,
  CheckCircle2,
  Eye,
  Filter,
  RefreshCw,
  Search as SearchIcon,
  ShieldOff,
  Siren,
  X,
} from 'lucide-react'
import { useApi, useDebounced } from '../hooks/useApi'
import api from '../services/api'
import { useToast } from '../context/ToastContext'
import {
  ConfirmDialog,
  DetailRow,
  EmptyState,
  ErrorState,
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

const SEVERITY_OPTIONS = [
  { value: 'ALL', label: 'All severities' },
  { value: 'CRITICAL', label: 'Critical' },
  { value: 'HIGH', label: 'High' },
  { value: 'MEDIUM', label: 'Medium' },
  { value: 'LOW', label: 'Low' },
]

const STATUS_OPTIONS = [
  { value: 'ALL', label: 'All statuses' },
  { value: 'NEW', label: 'New' },
  { value: 'ACKNOWLEDGED', label: 'Acknowledged' },
  { value: 'INVESTIGATING', label: 'Investigating' },
  { value: 'RESOLVED', label: 'Resolved' },
  { value: 'FALSE_POSITIVE', label: 'False positive' },
]

const SORT_OPTIONS = [
  { value: 'newest', label: 'Newest first' },
  { value: 'oldest', label: 'Oldest first' },
  { value: 'risk', label: 'Highest risk' },
]

function AlertDetailModal({ alertId, open, onClose, onChanged }) {
  const toast = useToast()
  const navigate = useNavigate()
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(null)
  const { data: alert, loading, error, refresh } = useApi(
    () => (alertId ? api.getAlert(alertId) : Promise.resolve(null)),
    [alertId],
    { immediate: Boolean(alertId) },
  )

  const act = async (action, label) => {
    setBusy(action)
    try {
      await api.updateAlert(alertId, { action, note: note.trim() || undefined })
      toast.success(`Alert marked as ${label}.`)
      setNote('')
      await refresh({ quiet: true })
      onChanged?.()
    } catch (caught) {
      toast.error(caught.message)
    } finally {
      setBusy(null)
    }
  }

  const escalate = async () => {
    setBusy('escalate')
    try {
      const result = await api.escalateAlert(alertId, {})
      toast.success(`Incident ${result.incident.incident_code} opened.`)
      onChanged?.()
      onClose()
      navigate(`/incidents/${result.incident.id}`)
    } catch (caught) {
      toast.error(caught.message)
    } finally {
      setBusy(null)
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={alert ? `${alert.alert_code} - ${alert.threat_type}` : 'Alert details'}
      description={alert ? formatDateTime(alert.created_at) : undefined}
      size="lg"
      footer={
        alert && (
          <>
            <button
              type="button"
              className="btn-secondary btn-sm"
              onClick={() => act('investigate', 'investigating')}
              disabled={Boolean(busy)}
            >
              {busy === 'investigate' ? <Spinner size={14} /> : <SearchIcon size={14} />}
              Investigate
            </button>
            <button
              type="button"
              className="btn-secondary btn-sm"
              onClick={escalate}
              disabled={Boolean(busy)}
            >
              {busy === 'escalate' ? <Spinner size={14} /> : <ArrowUpRight size={14} />}
              Escalate to incident
            </button>
            <button
              type="button"
              className="btn-secondary btn-sm"
              onClick={() => act('false_positive', 'a false positive')}
              disabled={Boolean(busy)}
            >
              {busy === 'false_positive' ? <Spinner size={14} /> : <ShieldOff size={14} />}
              False positive
            </button>
            <button
              type="button"
              className="btn-success btn-sm"
              onClick={() => act('resolve', 'resolved')}
              disabled={Boolean(busy)}
            >
              {busy === 'resolve' ? <Spinner size={14} /> : <CheckCircle2 size={14} />}
              Resolve
            </button>
          </>
        )
      }
    >
      {loading && !alert && <SkeletonTable rows={4} columns={2} />}
      {error && <ErrorState error={error} onRetry={refresh} />}
      {alert && (
        <div className="space-y-5">
          <div className="flex flex-wrap items-center gap-2">
            <SeverityBadge severity={alert.severity} />
            <StatusBadge status={alert.status} />
            <span className="mono text-xs text-slate-500">
              confidence {(alert.confidence * 100).toFixed(0)}%
            </span>
            {alert.incident_id && (
              <button
                type="button"
                onClick={() => {
                  onClose()
                  navigate(`/incidents/${alert.incident_id}`)
                }}
                className="badge border-violet-400/40 bg-violet-400/10 text-violet-300"
              >
                Linked incident #{alert.incident_id}
              </button>
            )}
          </div>

          <div>
            <p className="field-label">Summary</p>
            <p className="text-sm leading-relaxed text-slate-300">{alert.description}</p>
          </div>

          <div>
            <p className="field-label">Risk score</p>
            <RiskBar score={alert.risk_score} />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-lg border border-white/10 bg-navy-950/40 px-4 py-2">
              <p className="field-label mt-2">Source information</p>
              <dl className="divide-y divide-white/[0.06]">
                <DetailRow label="Source IP" value={alert.source_ip} mono />
                <DetailRow label="Destination IP" value={alert.destination_ip} mono />
                <DetailRow label="Event ID" value={alert.event_id} mono />
                <DetailRow label="Raised" value={formatDateTime(alert.created_at)} />
              </dl>
            </div>
            <div className="rounded-lg border border-white/10 bg-navy-950/40 px-4 py-2">
              <p className="field-label mt-2">Event telemetry</p>
              <dl className="divide-y divide-white/[0.06]">
                <DetailRow label="Protocol" value={alert.event?.protocol} mono />
                <DetailRow label="Dest. port" value={alert.event?.destination_port} mono />
                <DetailRow label="Failed logins" value={alert.event?.failed_login_attempts} mono />
                <DetailRow label="Requests" value={alert.event?.request_count} mono />
              </dl>
            </div>
          </div>

          <div>
            <p className="field-label">Detection reasons</p>
            <ul className="space-y-2">
              {(alert.reasons || []).map((reason, index) => (
                <li key={index} className="flex items-start gap-2.5 text-sm text-slate-300">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
                  {reason}
                </li>
              ))}
            </ul>
          </div>

          <div>
            <p className="field-label">Recommended response</p>
            <p className="rounded-lg border border-info/25 bg-info/[0.06] px-3.5 py-2.5 text-sm leading-relaxed text-slate-300">
              {alert.recommended_action}
            </p>
          </div>

          {alert.notes && (
            <div>
              <p className="field-label">Analyst notes</p>
              <pre className="whitespace-pre-wrap rounded-lg border border-white/10 bg-navy-950/60 px-3.5 py-2.5 text-xs leading-relaxed text-slate-400">
                {alert.notes}
              </pre>
            </div>
          )}

          <div>
            <label className="field-label" htmlFor="alert-note">
              Add a note with your next action
            </label>
            <textarea
              id="alert-note"
              rows={2}
              value={note}
              onChange={(event) => setNote(event.target.value)}
              placeholder="e.g. Source blocked at the perimeter gateway, monitoring for recurrence."
              className="field-input resize-none"
            />
          </div>
        </div>
      )}
    </Modal>
  )
}

export default function Alerts() {
  const toast = useToast()
  const [searchParams, setSearchParams] = useSearchParams()

  const [page, setPage] = useState(1)
  const [severity, setSeverity] = useState(searchParams.get('severity') || 'ALL')
  const [status, setStatus] = useState(searchParams.get('status') || 'ALL')
  const [threatType, setThreatType] = useState('all')
  const [sort, setSort] = useState('newest')
  const [search, setSearch] = useState(searchParams.get('search') || '')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [showFilters, setShowFilters] = useState(false)
  const [selectedId, setSelectedId] = useState(searchParams.get('focus') || null)
  const [confirm, setConfirm] = useState(null)
  const [bulkBusy, setBulkBusy] = useState(false)

  const debouncedSearch = useDebounced(search, 400)

  const params = useMemo(
    () => ({
      page,
      per_page: 15,
      severity,
      status,
      threat_type: threatType,
      sort,
      search: debouncedSearch || undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
    }),
    [page, severity, status, threatType, sort, debouncedSearch, dateFrom, dateTo],
  )

  const { data, error, loading, refresh } = useApi(() => api.listAlerts(params), [params])

  useEffect(() => {
    setPage(1)
  }, [severity, status, threatType, sort, debouncedSearch, dateFrom, dateTo])

  useEffect(() => {
    const next = new URLSearchParams()
    if (severity !== 'ALL') next.set('severity', severity)
    if (status !== 'ALL') next.set('status', status)
    if (search) next.set('search', search)
    if (selectedId) next.set('focus', selectedId)
    setSearchParams(next, { replace: true })
  }, [severity, status, search, selectedId, setSearchParams])

  const alerts = data?.data || []
  const filters = data?.filters || {}
  const activeFilters =
    (severity !== 'ALL' ? 1 : 0) +
    (status !== 'ALL' ? 1 : 0) +
    (threatType !== 'all' ? 1 : 0) +
    (dateFrom ? 1 : 0) +
    (dateTo ? 1 : 0)

  const clearFilters = () => {
    setSeverity('ALL')
    setStatus('ALL')
    setThreatType('all')
    setDateFrom('')
    setDateTo('')
    setSearch('')
  }

  const quickAction = async (alert, action, label) => {
    setBulkBusy(true)
    try {
      await api.updateAlert(alert.id, { action })
      toast.success(`${alert.alert_code} marked as ${label}.`)
      refresh({ quiet: true })
    } catch (caught) {
      toast.error(caught.message)
    } finally {
      setBulkBusy(false)
      setConfirm(null)
    }
  }

  return (
    <>
      <PageHeader
        title="Alerts"
        description="Every detection at MEDIUM severity or above raises an alert here for triage."
        icon={Siren}
      >
        <button
          type="button"
          onClick={() => setShowFilters((open) => !open)}
          className="btn-secondary btn-sm"
        >
          <Filter size={14} />
          Filters
          {activeFilters > 0 && (
            <span className="rounded bg-accent/20 px-1.5 text-[0.65rem] text-accent">
              {activeFilters}
            </span>
          )}
        </button>
        <button type="button" onClick={() => refresh()} className="btn-secondary btn-sm" disabled={loading}>
          {loading ? <Spinner size={14} /> : <RefreshCw size={14} />}
          Refresh
        </button>
      </PageHeader>

      <Panel bodyClassName="p-0">
        <div className="border-b border-white/10 p-4">
          <div className="flex flex-wrap items-center gap-3">
            <SearchInput
              value={search}
              onChange={setSearch}
              placeholder="Search by alert code, source IP or threat type..."
              className="min-w-[16rem] flex-1"
            />
            <Select value={sort} onChange={setSort} options={SORT_OPTIONS} className="w-40" />
          </div>

          {showFilters && (
            <div className="mt-4 grid animate-fade-in gap-3 sm:grid-cols-2 lg:grid-cols-5">
              <Select label="Severity" value={severity} onChange={setSeverity} options={SEVERITY_OPTIONS} />
              <Select label="Status" value={status} onChange={setStatus} options={STATUS_OPTIONS} />
              <Select
                label="Threat type"
                value={threatType}
                onChange={setThreatType}
                options={[
                  { value: 'all', label: 'All types' },
                  ...(filters.threat_types || []).map((type) => ({ value: type, label: type })),
                ]}
              />
              <div>
                <label className="field-label" htmlFor="date-from">
                  From date
                </label>
                <input
                  id="date-from"
                  type="date"
                  value={dateFrom}
                  onChange={(event) => setDateFrom(event.target.value)}
                  className="field-input"
                />
              </div>
              <div>
                <label className="field-label" htmlFor="date-to">
                  To date
                </label>
                <input
                  id="date-to"
                  type="date"
                  value={dateTo}
                  onChange={(event) => setDateTo(event.target.value)}
                  className="field-input"
                />
              </div>
            </div>
          )}

          {activeFilters > 0 && (
            <button type="button" onClick={clearFilters} className="btn-ghost btn-sm mt-3">
              <X size={13} />
              Clear all filters
            </button>
          )}
        </div>

        {loading && !data ? (
          <SkeletonTable rows={8} columns={8} />
        ) : error ? (
          <ErrorState error={error} onRetry={refresh} />
        ) : alerts.length === 0 ? (
          <EmptyState
            icon={Siren}
            title="No alerts match these filters"
            message={
              activeFilters > 0 || search
                ? 'Try widening the filters, or clear them to see the full queue.'
                : 'No alerts have been raised yet. Analyse an event or upload a log file to generate one.'
            }
            action={
              activeFilters > 0 ? (
                <button type="button" onClick={clearFilters} className="btn-secondary btn-sm">
                  Clear filters
                </button>
              ) : null
            }
          />
        ) : (
          <>
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Alert ID</th>
                    <th>Timestamp</th>
                    <th>Threat type</th>
                    <th>Source</th>
                    <th>Severity</th>
                    <th>Risk</th>
                    <th>Confidence</th>
                    <th>Status</th>
                    <th className="text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {alerts.map((alert) => (
                    <tr key={alert.id}>
                      <td>
                        <button
                          type="button"
                          onClick={() => setSelectedId(String(alert.id))}
                          className="mono text-accent hover:underline"
                        >
                          {alert.alert_code}
                        </button>
                      </td>
                      <td className="whitespace-nowrap text-xs text-slate-400">
                        {formatDateTime(alert.created_at)}
                        <span className="block text-[0.65rem] text-slate-600">
                          {timeAgo(alert.created_at)}
                        </span>
                      </td>
                      <td className="text-slate-200">{alert.threat_type}</td>
                      <td className="mono text-xs">{alert.source_ip}</td>
                      <td>
                        <SeverityBadge severity={alert.severity} />
                      </td>
                      <td className="w-28">
                        <RiskBar score={alert.risk_score} />
                      </td>
                      <td className="mono text-xs">{(alert.confidence * 100).toFixed(0)}%</td>
                      <td>
                        <StatusBadge status={alert.status} />
                      </td>
                      <td>
                        <div className="flex items-center justify-end gap-1">
                          <button
                            type="button"
                            onClick={() => setSelectedId(String(alert.id))}
                            className="btn-ghost btn-sm"
                            title="View details"
                          >
                            <Eye size={14} />
                          </button>
                          {!['RESOLVED', 'FALSE_POSITIVE'].includes(alert.status) && (
                            <>
                              <button
                                type="button"
                                onClick={() => quickAction(alert, 'investigate', 'investigating')}
                                className="btn-ghost btn-sm"
                                title="Investigate"
                                disabled={bulkBusy}
                              >
                                <SearchIcon size={14} />
                              </button>
                              <button
                                type="button"
                                onClick={() =>
                                  setConfirm({
                                    alert,
                                    action: 'resolve',
                                    label: 'resolved',
                                    title: `Resolve ${alert.alert_code}?`,
                                    message:
                                      'This marks the alert as a confirmed and handled finding. It will count towards the detection precision figure on the dashboard.',
                                    confirmLabel: 'Resolve alert',
                                    tone: 'primary',
                                  })
                                }
                                className="btn-ghost btn-sm text-safe"
                                title="Resolve"
                                disabled={bulkBusy}
                              >
                                <CheckCircle2 size={14} />
                              </button>
                              <button
                                type="button"
                                onClick={() =>
                                  setConfirm({
                                    alert,
                                    action: 'false_positive',
                                    label: 'a false positive',
                                    title: `Mark ${alert.alert_code} as a false positive?`,
                                    message:
                                      'Use this when the activity was legitimate. False positives lower the reported detection precision, which is the intended feedback signal.',
                                    confirmLabel: 'Mark false positive',
                                    tone: 'danger',
                                  })
                                }
                                className="btn-ghost btn-sm text-slate-500"
                                title="Mark false positive"
                                disabled={bulkBusy}
                              >
                                <ShieldOff size={14} />
                              </button>
                            </>
                          )}
                        </div>
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

      <AlertDetailModal
        alertId={selectedId}
        open={Boolean(selectedId)}
        onClose={() => setSelectedId(null)}
        onChanged={() => refresh({ quiet: true })}
      />

      <ConfirmDialog
        open={Boolean(confirm)}
        onClose={() => setConfirm(null)}
        onConfirm={() => quickAction(confirm.alert, confirm.action, confirm.label)}
        title={confirm?.title}
        message={confirm?.message}
        confirmLabel={confirm?.confirmLabel}
        tone={confirm?.tone}
        busy={bulkBusy}
      />
    </>
  )
}
