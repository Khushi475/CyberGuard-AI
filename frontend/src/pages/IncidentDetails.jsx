/**
 * Incident details page (FR-07).
 *
 * Renders the incident summary, its status history, linked alerts and related
 * events, and exposes exactly the lifecycle transitions the backend currently
 * permits (`allowed_transitions`), so the UI can never offer an illegal move.
 */
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import {
  ArrowLeft,
  CheckCircle2,
  ClipboardList,
  History,
  Lock,
  RefreshCw,
  Search,
  ShieldAlert,
  ShieldOff,
  Siren,
  User as UserIcon,
} from 'lucide-react'
import { useApi } from '../hooks/useApi'
import api from '../services/api'
import { useToast } from '../context/ToastContext'
import {
  DetailRow,
  ErrorState,
  LoadingState,
  Modal,
  PageHeader,
  Panel,
  RiskBar,
  SeverityBadge,
  Spinner,
  StatusBadge,
} from '../components/ui'
import { formatDateTime, timeAgo, titleCase } from '../utils/format'

const LIFECYCLE = ['NEW', 'OPEN', 'INVESTIGATING', 'CONTAINED', 'RESOLVED']

const ACTIONS = [
  { status: 'INVESTIGATING', label: 'Investigate', icon: Search, className: 'btn-secondary' },
  { status: 'CONTAINED', label: 'Contain', icon: Lock, className: 'btn-secondary' },
  { status: 'RESOLVED', label: 'Resolve', icon: CheckCircle2, className: 'btn-success' },
  { status: 'FALSE_POSITIVE', label: 'False positive', icon: ShieldOff, className: 'btn-secondary' },
  { status: 'OPEN', label: 'Reopen as open', icon: RefreshCw, className: 'btn-secondary' },
]

function LifecycleTracker({ current }) {
  const closed = ['RESOLVED', 'FALSE_POSITIVE'].includes(current)
  const activeIndex = LIFECYCLE.indexOf(current)
  return (
    <div>
      <div className="flex items-center">
        {LIFECYCLE.map((state, index) => {
          const reached = current === 'FALSE_POSITIVE' ? index === 0 : index <= activeIndex
          const isCurrent = state === current
          return (
            <div key={state} className="flex flex-1 items-center last:flex-none">
              <div className="flex flex-col items-center gap-1.5">
                <span
                  className={`flex h-7 w-7 items-center justify-center rounded-full border text-[0.65rem] font-semibold transition-colors ${
                    isCurrent
                      ? 'border-accent bg-accent text-navy-950'
                      : reached
                        ? 'border-accent/50 bg-accent/15 text-accent'
                        : 'border-white/15 bg-navy-800 text-slate-600'
                  }`}
                >
                  {index + 1}
                </span>
                <span
                  className={`whitespace-nowrap text-[0.6rem] uppercase tracking-wide ${
                    isCurrent ? 'text-accent' : reached ? 'text-slate-400' : 'text-slate-600'
                  }`}
                >
                  {titleCase(state)}
                </span>
              </div>
              {index < LIFECYCLE.length - 1 && (
                <span
                  className={`mx-1 mb-5 h-px flex-1 ${
                    index < activeIndex ? 'bg-accent/50' : 'bg-white/10'
                  }`}
                />
              )}
            </div>
          )
        })}
      </div>
      {current === 'FALSE_POSITIVE' && (
        <p className="mt-3 rounded-lg border border-slate-500/30 bg-slate-500/[0.07] px-3 py-2 text-xs text-slate-400">
          This incident was closed as a <strong className="text-slate-300">false positive</strong> -
          it left the normal lifecycle without being contained.
        </p>
      )}
      {closed && current === 'RESOLVED' && (
        <p className="mt-3 rounded-lg border border-safe/30 bg-safe/[0.07] px-3 py-2 text-xs text-slate-400">
          Lifecycle complete. The incident can be reopened for investigation if the activity recurs.
        </p>
      )}
    </div>
  )
}

function TransitionModal({ open, onClose, action, onConfirm, busy }) {
  const [note, setNote] = useState('')
  const [summary, setSummary] = useState('')
  const closing = ['RESOLVED', 'FALSE_POSITIVE'].includes(action?.status)

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={`${action?.label || 'Update'} incident`}
      description={`The incident will move to ${titleCase(action?.status || '')}. This change is written to the audit trail.`}
      size="sm"
      footer={
        <>
          <button type="button" className="btn-secondary" onClick={onClose} disabled={busy}>
            Cancel
          </button>
          <button
            type="button"
            className="btn-primary"
            onClick={() => onConfirm(note, summary)}
            disabled={busy}
          >
            {busy && <Spinner size={15} />}
            Confirm
          </button>
        </>
      }
    >
      <div className="space-y-4">
        <div>
          <label className="field-label" htmlFor="transition-note">
            Note for the status history
          </label>
          <textarea
            id="transition-note"
            rows={3}
            value={note}
            onChange={(event) => setNote(event.target.value)}
            placeholder="e.g. Source address blocked at the perimeter gateway."
            className="field-input resize-none"
          />
        </div>
        {closing && (
          <div>
            <label className="field-label" htmlFor="transition-summary">
              Resolution summary
            </label>
            <textarea
              id="transition-summary"
              rows={3}
              value={summary}
              onChange={(event) => setSummary(event.target.value)}
              placeholder="What was done and how it was verified."
              className="field-input resize-none"
            />
            <p className="field-hint">
              Closing the incident also closes every alert linked to it.
            </p>
          </div>
        )}
      </div>
    </Modal>
  )
}

export default function IncidentDetails() {
  const { id } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const [pending, setPending] = useState(null)
  const [busy, setBusy] = useState(false)
  const [assigning, setAssigning] = useState(false)

  const { data: incident, error, loading, refresh } = useApi(() => api.getIncident(id), [id])
  const { data: analystData } = useApi(() => api.listIncidents({ per_page: 1 }), [])
  const analysts = analystData?.filters?.analysts || []

  const applyTransition = async (note, summary) => {
    setBusy(true)
    try {
      await api.updateIncident(id, {
        status: pending.status,
        note: note || undefined,
        resolution_summary: summary || undefined,
      })
      toast.success(`Incident moved to ${titleCase(pending.status)}.`)
      setPending(null)
      refresh({ quiet: true })
    } catch (caught) {
      toast.error(caught.message)
    } finally {
      setBusy(false)
    }
  }

  const reassign = async (userId) => {
    setAssigning(true)
    try {
      await api.updateIncident(id, { assigned_to: userId ? Number(userId) : null })
      toast.success('Incident reassigned.')
      refresh({ quiet: true })
    } catch (caught) {
      toast.error(caught.message)
    } finally {
      setAssigning(false)
    }
  }

  if (loading && !incident) return <LoadingState label="Loading incident..." />
  if (error && !incident) {
    return (
      <div className="panel">
        <ErrorState error={error} onRetry={refresh} />
      </div>
    )
  }
  if (!incident) return null

  const allowed = incident.state_machine?.allowed || incident.allowed_transitions || []
  const availableActions = ACTIONS.filter((action) => allowed.includes(action.status))

  return (
    <>
      <Link
        to="/incidents"
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-slate-400 transition-colors hover:text-accent"
      >
        <ArrowLeft size={15} />
        Back to incidents
      </Link>

      <PageHeader
        title={incident.title}
        description={`${incident.incident_code} - detected ${formatDateTime(incident.detected_at)}`}
        icon={ShieldAlert}
      >
        <button type="button" onClick={() => refresh()} className="btn-secondary btn-sm">
          <RefreshCw size={14} />
          Refresh
        </button>
      </PageHeader>

      <div className="mb-4 flex flex-wrap items-center gap-2">
        <SeverityBadge severity={incident.severity} />
        <StatusBadge status={incident.status} />
        <span className="badge border-white/15 bg-navy-800 text-slate-300">
          Priority {incident.priority}
        </span>
        <span className="badge border-white/15 bg-navy-800 text-slate-300">
          {incident.threat_type}
        </span>
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <div className="space-y-4 xl:col-span-2">
          <Panel title="Incident lifecycle" subtitle="Current position in the state machine">
            <LifecycleTracker current={incident.status} />

            <div className="mt-6 border-t border-white/10 pt-4">
              <p className="field-label">Available transitions</p>
              {availableActions.length === 0 ? (
                <p className="text-sm text-slate-500">
                  No further transitions are permitted from this state.
                </p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {availableActions.map((action) => {
                    const Icon = action.icon
                    return (
                      <button
                        key={action.status}
                        type="button"
                        onClick={() => setPending(action)}
                        className={`${action.className} btn-sm`}
                      >
                        <Icon size={14} />
                        {action.label}
                      </button>
                    )
                  })}
                </div>
              )}
              <p className="mt-3 text-xs text-slate-500">
                Only transitions allowed by the backend state machine are offered. Attempting any
                other move returns HTTP 409.
              </p>
            </div>
          </Panel>

          <Panel title="Incident summary" subtitle="Classification and detection context">
            <p className="text-sm leading-relaxed text-slate-300">
              {incident.description || 'No description recorded.'}
            </p>
            <div className="mt-4">
              <p className="field-label">Risk score</p>
              <RiskBar score={incident.risk_score} />
            </div>
            {incident.resolution_summary && (
              <div className="mt-4">
                <p className="field-label">Resolution summary</p>
                <p className="rounded-lg border border-safe/25 bg-safe/[0.06] px-3.5 py-2.5 text-sm text-slate-300">
                  {incident.resolution_summary}
                </p>
              </div>
            )}
          </Panel>

          <Panel
            title="Linked alerts"
            subtitle={`${incident.alerts?.length || 0} alert(s) belong to this incident`}
            bodyClassName="p-0"
          >
            {(incident.alerts || []).length === 0 ? (
              <p className="px-5 py-8 text-center text-sm text-slate-500">
                No alerts are linked to this incident.
              </p>
            ) : (
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Alert</th>
                      <th>Threat type</th>
                      <th>Source</th>
                      <th>Severity</th>
                      <th>Status</th>
                      <th>Raised</th>
                    </tr>
                  </thead>
                  <tbody>
                    {incident.alerts.map((alert) => (
                      <tr
                        key={alert.id}
                        className="cursor-pointer"
                        onClick={() => navigate(`/alerts?focus=${alert.id}`)}
                      >
                        <td className="mono text-accent">{alert.alert_code}</td>
                        <td className="text-slate-200">{alert.threat_type}</td>
                        <td className="mono text-xs">{alert.source_ip}</td>
                        <td>
                          <SeverityBadge severity={alert.severity} />
                        </td>
                        <td>
                          <StatusBadge status={alert.status} />
                        </td>
                        <td className="whitespace-nowrap text-xs text-slate-500">
                          {timeAgo(alert.created_at)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Panel>

          <Panel
            title="Related events"
            subtitle="Telemetry from the same source or linked to the incident's alerts"
            bodyClassName="p-0"
          >
            {(incident.related_events || []).length === 0 ? (
              <p className="px-5 py-8 text-center text-sm text-slate-500">
                No related events found.
              </p>
            ) : (
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Timestamp</th>
                      <th>Source</th>
                      <th>Destination</th>
                      <th>Protocol</th>
                      <th>Classification</th>
                      <th>Risk</th>
                    </tr>
                  </thead>
                  <tbody>
                    {incident.related_events.map((event) => (
                      <tr key={event.id}>
                        <td className="whitespace-nowrap text-xs text-slate-400">
                          {formatDateTime(event.timestamp)}
                        </td>
                        <td className="mono text-xs">{event.source_ip}</td>
                        <td className="mono text-xs">
                          {event.destination_ip}
                          {event.destination_port ? `:${event.destination_port}` : ''}
                        </td>
                        <td className="text-xs">{event.protocol}</td>
                        <td className="text-xs text-slate-300">
                          {event.detection?.classification || 'Not analysed'}
                        </td>
                        <td className="w-24">
                          <RiskBar score={event.detection?.risk_score || 0} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Panel>
        </div>

        <div className="space-y-4">
          <Panel title="Details">
            <dl className="divide-y divide-white/[0.06]">
              <DetailRow label="Incident ID" value={incident.incident_code} mono />
              <DetailRow label="Threat type" value={incident.threat_type} />
              <DetailRow label="Severity" value={incident.severity} />
              <DetailRow label="Priority" value={incident.priority} />
              <DetailRow label="Source IP" value={incident.source_ip} mono />
              <DetailRow label="Detected" value={formatDateTime(incident.detected_at)} />
              <DetailRow label="Last updated" value={formatDateTime(incident.updated_at)} />
              <DetailRow label="Contained" value={formatDateTime(incident.contained_at)} />
              <DetailRow label="Resolved" value={formatDateTime(incident.resolved_at)} />
            </dl>
          </Panel>

          <Panel title="Assignment" subtitle="Who owns this investigation">
            <div className="mb-3 flex items-center gap-2.5 rounded-lg border border-white/10 bg-navy-950/40 px-3.5 py-2.5">
              <UserIcon size={15} className="text-accent" />
              <span className="text-sm text-slate-200">{incident.assigned_analyst}</span>
              {assigning && <Spinner size={14} className="ml-auto text-accent" />}
            </div>
            <label className="field-label" htmlFor="assignee">
              Reassign to
            </label>
            <select
              id="assignee"
              value={incident.assigned_to || ''}
              onChange={(event) => reassign(event.target.value)}
              className="field-input cursor-pointer"
              disabled={assigning}
            >
              <option value="" className="bg-navy-900">
                Unassigned
              </option>
              {analysts.map((analyst) => (
                <option key={analyst.id} value={analyst.id} className="bg-navy-900">
                  {analyst.full_name} ({analyst.role})
                </option>
              ))}
            </select>
          </Panel>

          <Panel
            title="Status history"
            subtitle="Every transition, with who made it"
            actions={<History size={15} className="text-slate-500" />}
          >
            {(incident.history || []).length === 0 ? (
              <p className="py-6 text-center text-sm text-slate-500">No transitions recorded yet.</p>
            ) : (
              <ol className="relative space-y-4 border-l border-white/10 pl-4">
                {incident.history
                  .slice()
                  .reverse()
                  .map((entry, index) => (
                    <li key={index} className="relative">
                      <span className="absolute -left-[1.3rem] top-1 h-2.5 w-2.5 rounded-full border-2 border-navy-900 bg-accent" />
                      <div className="flex flex-wrap items-center gap-1.5 text-xs">
                        {entry.from && (
                          <>
                            <StatusBadge status={entry.from} />
                            <span className="text-slate-600">to</span>
                          </>
                        )}
                        <StatusBadge status={entry.to} />
                      </div>
                      <p className="mt-1 text-xs text-slate-400">{entry.actor}</p>
                      {entry.note && <p className="mt-0.5 text-xs text-slate-500">{entry.note}</p>}
                      <p className="mt-0.5 text-[0.65rem] text-slate-600">
                        {formatDateTime(entry.at)}
                      </p>
                    </li>
                  ))}
              </ol>
            )}
          </Panel>

          <Panel title="Response checklist" subtitle="Standard containment steps">
            <ul className="space-y-2.5 text-sm text-slate-300">
              {[
                'Confirm the activity against the asset owner and change calendar.',
                'Preserve the related events and detection reasons for the case record.',
                'Apply containment (block, rate-limit, isolate or force re-authentication).',
                'Verify the activity has stopped before resolving.',
                'Record a resolution summary so the audit trail is complete.',
              ].map((step, index) => (
                <li key={index} className="flex items-start gap-2.5">
                  <ClipboardList size={14} className="mt-0.5 shrink-0 text-accent" />
                  {step}
                </li>
              ))}
            </ul>
          </Panel>
        </div>
      </div>

      <TransitionModal
        open={Boolean(pending)}
        onClose={() => setPending(null)}
        action={pending}
        onConfirm={applyTransition}
        busy={busy}
      />
    </>
  )
}
