/**
 * Threat Intelligence page (FR-09).
 *
 * Every indicator shown here is simulated. Addresses come from the RFC 5737
 * documentation ranges and domains use the reserved .invalid / .example
 * namespaces, so nothing in this feed points at real infrastructure.
 */
import { useEffect, useMemo, useState } from 'react'
import { Activity, Globe, Network, RefreshCw, ShieldAlert, User as UserIcon } from 'lucide-react'
import { useApi, useDebounced } from '../hooks/useApi'
import api from '../services/api'
import { useToast } from '../context/ToastContext'
import {
  EmptyState,
  ErrorState,
  InfoNote,
  PageHeader,
  Pagination,
  Panel,
  SearchInput,
  Select,
  SeverityBadge,
  SkeletonTable,
  Spinner,
  StatusBadge,
} from '../components/ui'
import { formatDate, timeAgo } from '../utils/format'

const TYPE_ICONS = {
  'Suspicious IP': Network,
  'Suspicious Domain': Globe,
  'Suspicious User Activity': UserIcon,
  'Anomalous Network Activity': Activity,
}

const TYPE_OPTIONS = [
  { value: 'all', label: 'All indicator types' },
  { value: 'Suspicious IP', label: 'Suspicious IP' },
  { value: 'Suspicious Domain', label: 'Suspicious Domain' },
  { value: 'Suspicious User Activity', label: 'Suspicious User Activity' },
  { value: 'Anomalous Network Activity', label: 'Anomalous Network Activity' },
]

const RISK_OPTIONS = [
  { value: 'ALL', label: 'All risk levels' },
  { value: 'CRITICAL', label: 'Critical' },
  { value: 'HIGH', label: 'High' },
  { value: 'MEDIUM', label: 'Medium' },
  { value: 'LOW', label: 'Low' },
]

const STATUS_OPTIONS = [
  { value: 'ALL', label: 'All statuses' },
  { value: 'ACTIVE', label: 'Active' },
  { value: 'MONITORING', label: 'Monitoring' },
  { value: 'RETIRED', label: 'Retired' },
]

export default function ThreatIntelligence() {
  const toast = useToast()
  const [page, setPage] = useState(1)
  const [type, setType] = useState('all')
  const [risk, setRisk] = useState('ALL')
  const [status, setStatus] = useState('ALL')
  const [search, setSearch] = useState('')
  const [busyId, setBusyId] = useState(null)

  const debouncedSearch = useDebounced(search, 400)

  const params = useMemo(
    () => ({
      page,
      per_page: 25,
      indicator_type: type,
      risk_level: risk,
      status,
      search: debouncedSearch || undefined,
    }),
    [page, type, risk, status, debouncedSearch],
  )

  const { data, error, loading, refresh } = useApi(() => api.listIndicators(params), [params])

  useEffect(() => {
    setPage(1)
  }, [type, risk, status, debouncedSearch])

  const indicators = data?.data || []

  const counts = useMemo(() => {
    const tally = {}
    indicators.forEach((indicator) => {
      tally[indicator.indicator_type] = (tally[indicator.indicator_type] || 0) + 1
    })
    return tally
  }, [indicators])

  const changeStatus = async (indicator, nextStatus) => {
    setBusyId(indicator.id)
    try {
      await api.updateIndicator(indicator.id, { status: nextStatus })
      toast.success(`'${indicator.indicator}' set to ${nextStatus.toLowerCase()}.`)
      refresh({ quiet: true })
    } catch (caught) {
      toast.error(caught.message)
    } finally {
      setBusyId(null)
    }
  }

  return (
    <>
      <PageHeader
        title="Threat Intelligence"
        description="Defensive indicator feed used to give context to detections."
        icon={Activity}
      >
        <button type="button" onClick={() => refresh()} className="btn-secondary btn-sm" disabled={loading}>
          {loading ? <Spinner size={14} /> : <RefreshCw size={14} />}
          Refresh
        </button>
      </PageHeader>

      <InfoNote tone="warning" className="mb-4">
        <strong className="text-warn">Simulated feed.</strong> Every indicator below was generated
        for this academic prototype. IP addresses come from the RFC 5737 documentation ranges
        (192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24) and domains use the reserved{' '}
        <span className="mono">.invalid</span> and <span className="mono">.example</span> namespaces.
        None of them refer to real malicious infrastructure.
      </InfoNote>

      <div className="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {TYPE_OPTIONS.slice(1).map((option) => {
          const Icon = TYPE_ICONS[option.value] || ShieldAlert
          const active = type === option.value
          return (
            <button
              key={option.value}
              type="button"
              onClick={() => setType(active ? 'all' : option.value)}
              className={`panel panel-hover flex items-center gap-3 p-4 text-left ${
                active ? 'border-accent/45 bg-accent/[0.06]' : ''
              }`}
            >
              <span
                className={`rounded-lg border p-2 ${
                  active
                    ? 'border-accent/35 bg-accent/15 text-accent'
                    : 'border-white/10 bg-navy-800 text-slate-400'
                }`}
              >
                <Icon size={17} />
              </span>
              <span className="min-w-0">
                <span className="block truncate text-sm text-slate-200">{option.label}</span>
                <span className="block text-xs text-slate-500">
                  {counts[option.value] || 0} on this page
                </span>
              </span>
            </button>
          )
        })}
      </div>

      <Panel bodyClassName="p-0">
        <div className="grid gap-3 border-b border-white/10 p-4 sm:grid-cols-2 lg:grid-cols-4">
          <SearchInput
            value={search}
            onChange={setSearch}
            placeholder="Search indicators..."
            className="lg:col-span-2"
          />
          <Select value={risk} onChange={setRisk} options={RISK_OPTIONS} />
          <Select value={status} onChange={setStatus} options={STATUS_OPTIONS} />
        </div>

        {loading && !data ? (
          <SkeletonTable rows={8} columns={7} />
        ) : error ? (
          <ErrorState error={error} onRetry={refresh} />
        ) : indicators.length === 0 ? (
          <EmptyState
            icon={Activity}
            title="No indicators match these filters"
            message="Adjust the filters, or run the seed script to reload the simulated intelligence feed."
          />
        ) : (
          <>
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Indicator</th>
                    <th>Type</th>
                    <th>Related category</th>
                    <th>Risk</th>
                    <th>Confidence</th>
                    <th>First seen</th>
                    <th>Last seen</th>
                    <th>Status</th>
                    <th className="text-right">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {indicators.map((indicator) => {
                    const Icon = TYPE_ICONS[indicator.indicator_type] || ShieldAlert
                    return (
                      <tr key={indicator.id}>
                        <td>
                          <div className="flex items-center gap-2">
                            <Icon size={14} className="shrink-0 text-accent" />
                            <div className="min-w-0">
                              <p className="mono truncate text-xs text-slate-200">
                                {indicator.indicator}
                              </p>
                              <p className="max-w-xs truncate text-[0.66rem] text-slate-500">
                                {indicator.description}
                              </p>
                            </div>
                          </div>
                        </td>
                        <td className="whitespace-nowrap text-xs text-slate-400">
                          {indicator.indicator_type}
                        </td>
                        <td className="whitespace-nowrap text-xs text-slate-400">
                          {indicator.category}
                        </td>
                        <td>
                          <SeverityBadge severity={indicator.risk_level} />
                        </td>
                        <td className="mono text-xs">{(indicator.confidence * 100).toFixed(0)}%</td>
                        <td className="whitespace-nowrap text-xs text-slate-500">
                          {formatDate(indicator.first_seen)}
                        </td>
                        <td className="whitespace-nowrap text-xs text-slate-500">
                          {timeAgo(indicator.last_seen)}
                        </td>
                        <td>
                          <StatusBadge status={indicator.status} />
                        </td>
                        <td className="text-right">
                          <select
                            value={indicator.status}
                            onChange={(event) => changeStatus(indicator, event.target.value)}
                            disabled={busyId === indicator.id}
                            className="cursor-pointer rounded-md border border-white/10 bg-navy-950 px-2 py-1 text-xs text-slate-300 focus:border-accent/60 focus:outline-none"
                            aria-label={`Change status for ${indicator.indicator}`}
                          >
                            <option value="ACTIVE">Active</option>
                            <option value="MONITORING">Monitoring</option>
                            <option value="RETIRED">Retired</option>
                          </select>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
            <Pagination pagination={data?.pagination} onPageChange={setPage} />
          </>
        )}
      </Panel>
    </>
  )
}
