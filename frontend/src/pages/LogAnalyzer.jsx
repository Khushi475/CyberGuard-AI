/**
 * Log Analyzer page (FR-10).
 *
 * Upload -> POST /api/events/upload -> Flask parses and validates every row ->
 * the detection engine scores each record -> results are stored -> the summary
 * returned by the backend is rendered below.
 */
import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  AlertTriangle,
  CheckCircle2,
  Download,
  FileSearch,
  FileSpreadsheet,
  FileWarning,
  Trash2,
  Upload,
} from 'lucide-react'
import api from '../services/api'
import { useToast } from '../context/ToastContext'
import { CategoryBarChart, SourceBarChart } from '../components/charts/Charts'
import {
  EmptyState,
  ErrorState,
  InfoNote,
  PageHeader,
  Panel,
  RiskBar,
  SearchInput,
  Select,
  SeverityBadge,
  Spinner,
} from '../components/ui'
import { formatBytes, formatDateTime, formatNumber } from '../utils/format'

const EXPECTED_COLUMNS = [
  'timestamp',
  'source_ip',
  'destination_ip',
  'source_port',
  'destination_port',
  'protocol',
  'bytes',
  'packets',
  'failed_logins',
  'request_count',
  'duration',
  'event_type',
]

const SAMPLE_FILES = [
  { name: 'sample_logs_mixed.csv', description: '120 rows - a realistic mix of normal and suspicious traffic' },
  { name: 'sample_logs_normal.csv', description: '80 rows - benign baseline traffic only' },
  { name: 'sample_logs_suspicious.csv', description: '60 rows - suspicious activity only' },
  { name: 'sample_logs_invalid.csv', description: '5 rows - 4 deliberately malformed, to demonstrate validation' },
]

function SummaryTile({ label, value, tone, icon: Icon }) {
  const tones = {
    accent: 'border-accent/25 bg-accent/10 text-accent',
    safe: 'border-safe/25 bg-safe/10 text-safe',
    warn: 'border-warn/25 bg-warn/10 text-warn',
    danger: 'border-danger/25 bg-danger/10 text-danger',
    critical: 'border-critical/30 bg-critical/10 text-red-300',
  }
  return (
    <div className="panel p-4">
      <div className="flex items-center gap-2.5">
        <span className={`rounded-lg border p-2 ${tones[tone]}`}>
          <Icon size={16} />
        </span>
        <div className="min-w-0">
          <p className="text-[0.62rem] uppercase tracking-wider text-slate-500">{label}</p>
          <p className="text-xl font-semibold tracking-tight text-slate-100">{value}</p>
        </div>
      </div>
    </div>
  )
}

export default function LogAnalyzer() {
  const toast = useToast()
  const navigate = useNavigate()
  const inputRef = useRef(null)

  const [file, setFile] = useState(null)
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [severityFilter, setSeverityFilter] = useState('ALL')
  const [rowSearch, setRowSearch] = useState('')

  const pickFile = (selected) => {
    if (!selected) return
    const name = selected.name.toLowerCase()
    if (!name.endsWith('.csv') && !name.endsWith('.txt') && !name.endsWith('.log')) {
      toast.error('Only .csv, .txt or .log files are accepted.')
      return
    }
    if (selected.size === 0) {
      toast.error('That file is empty. Choose a CSV with a header row and at least one record.')
      return
    }
    if (selected.size > 8 * 1024 * 1024) {
      toast.error('That file exceeds the 8 MB upload limit.')
      return
    }
    setFile(selected)
    setError(null)
    setResult(null)
  }

  const upload = async () => {
    if (!file) {
      toast.warning('Choose a CSV file first.')
      return
    }
    setUploading(true)
    setProgress(0)
    setError(null)
    try {
      const summary = await api.uploadLogs(file, setProgress)
      setResult(summary)
      toast.success(
        `Analysed ${summary.total_records} records - ${summary.suspicious_events} suspicious, ${summary.alerts_created} alerts raised.`,
      )
    } catch (caught) {
      setError(caught)
      toast.error(caught.message)
    } finally {
      setUploading(false)
      setProgress(0)
    }
  }

  const reset = () => {
    setFile(null)
    setResult(null)
    setError(null)
    if (inputRef.current) inputRef.current.value = ''
  }

  const exportResults = () => {
    if (!result?.records?.length) return
    const header = [
      'event_id',
      'timestamp',
      'source_ip',
      'destination_ip',
      'destination_port',
      'protocol',
      'event_type',
      'classification',
      'risk_score',
      'severity',
      'confidence',
      'reason',
    ]
    const escape = (value) => `"${String(value ?? '').replace(/"/g, '""')}"`
    const csv = [
      header.join(','),
      ...result.records.map((row) => header.map((key) => escape(row[key])).join(',')),
    ].join('\n')
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8;' }))
    const link = document.createElement('a')
    link.href = url
    link.download = `cyberguard_analysis_${Date.now()}.csv`
    link.click()
    URL.revokeObjectURL(url)
    toast.success('Analysis results exported as CSV.')
  }

  const visibleRows = (result?.records || []).filter((row) => {
    if (severityFilter !== 'ALL' && row.severity !== severityFilter) return false
    if (rowSearch) {
      const needle = rowSearch.toLowerCase()
      return (
        row.source_ip?.toLowerCase().includes(needle) ||
        row.destination_ip?.toLowerCase().includes(needle) ||
        row.classification?.toLowerCase().includes(needle)
      )
    }
    return true
  })

  return (
    <>
      <PageHeader
        title="Log Analyzer"
        description="Upload a CSV log export. Every row is validated, scored by the detection engine and stored, and alerts are raised automatically."
        icon={FileSearch}
      >
        {result && (
          <>
            <button type="button" onClick={exportResults} className="btn-secondary btn-sm">
              <Download size={14} />
              Export results
            </button>
            <button type="button" onClick={reset} className="btn-secondary btn-sm">
              <Trash2 size={14} />
              Clear
            </button>
          </>
        )}
      </PageHeader>

      <div className="grid gap-4 xl:grid-cols-3">
        <div className="space-y-4">
          <Panel title="Upload log file" subtitle="CSV, TXT or LOG - maximum 8 MB, 5000 rows">
            <div
              onDragOver={(event) => {
                event.preventDefault()
                setDragging(true)
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={(event) => {
                event.preventDefault()
                setDragging(false)
                pickFile(event.dataTransfer.files?.[0])
              }}
              onClick={() => inputRef.current?.click()}
              className={`flex cursor-pointer flex-col items-center justify-center gap-2.5 rounded-xl border-2 border-dashed px-4 py-10 text-center transition-all ${
                dragging
                  ? 'border-accent bg-accent/[0.07]'
                  : 'border-white/15 hover:border-accent/50 hover:bg-white/[0.02]'
              }`}
            >
              <span className="rounded-full border border-white/10 bg-navy-800/70 p-3 text-accent">
                <Upload size={22} />
              </span>
              <p className="text-sm font-medium text-slate-200">
                {file ? file.name : 'Drop a CSV file here, or click to browse'}
              </p>
              <p className="text-xs text-slate-500">
                {file ? formatBytes(file.size) : 'Files are parsed and validated on the server'}
              </p>
              <input
                ref={inputRef}
                type="file"
                accept=".csv,.txt,.log"
                className="hidden"
                onChange={(event) => pickFile(event.target.files?.[0])}
              />
            </div>

            {uploading && (
              <div className="mt-4">
                <div className="mb-1.5 flex items-center justify-between text-xs text-slate-400">
                  <span>Uploading and analysing...</span>
                  <span className="mono">{progress}%</span>
                </div>
                <div className="h-1.5 overflow-hidden rounded-full bg-navy-700">
                  <div
                    className="h-full rounded-full bg-accent transition-all duration-300"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
            )}

            <button
              type="button"
              onClick={upload}
              className="btn-primary mt-4 w-full"
              disabled={!file || uploading}
            >
              {uploading ? (
                <>
                  <Spinner size={16} />
                  Analysing...
                </>
              ) : (
                <>
                  <FileSearch size={16} />
                  Analyze log file
                </>
              )}
            </button>
          </Panel>

          <Panel title="Expected columns" subtitle="Header names are matched case-insensitively">
            <div className="flex flex-wrap gap-1.5">
              {EXPECTED_COLUMNS.map((column) => (
                <span
                  key={column}
                  className={`badge mono ${
                    column === 'source_ip'
                      ? 'border-accent/40 bg-accent/10 text-accent'
                      : 'border-white/15 bg-navy-800 text-slate-400'
                  }`}
                >
                  {column}
                </span>
              ))}
            </div>
            <p className="mt-3 text-xs leading-relaxed text-slate-500">
              Only <span className="mono text-accent">source_ip</span> is mandatory. Missing optional
              columns default to zero. Common aliases are accepted -{' '}
              <span className="mono">bytes</span> maps to{' '}
              <span className="mono">bytes_transferred</span>,{' '}
              <span className="mono">packets</span> to <span className="mono">packet_count</span>, and{' '}
              <span className="mono">failed_logins</span> to{' '}
              <span className="mono">failed_login_attempts</span>.
            </p>
          </Panel>

          <Panel title="Sample files" subtitle="Provided in the sample_data folder">
            <ul className="space-y-2">
              {SAMPLE_FILES.map((sample) => (
                <li
                  key={sample.name}
                  className="flex items-start gap-2.5 rounded-lg border border-white/10 bg-navy-950/40 px-3 py-2.5"
                >
                  <FileSpreadsheet size={15} className="mt-0.5 shrink-0 text-accent" />
                  <div className="min-w-0">
                    <p className="mono truncate text-xs text-slate-200">{sample.name}</p>
                    <p className="text-[0.68rem] text-slate-500">{sample.description}</p>
                  </div>
                </li>
              ))}
            </ul>
            <InfoNote className="mt-3">
              Browse to the project&apos;s <span className="mono">sample_data</span> folder in the
              file picker to load one of these.
            </InfoNote>
          </Panel>
        </div>

        <div className="xl:col-span-2">
          {error ? (
            <div className="panel">
              <ErrorState error={error} onRetry={() => setError(null)} />
              {error.details?.row_errors?.length > 0 && (
                <div className="border-t border-white/10 p-5">
                  <p className="field-label">Rejected rows</p>
                  <ul className="space-y-1.5">
                    {error.details.row_errors.map((row, index) => (
                      <li key={index} className="mono text-xs text-slate-400">
                        Row {row.row}: {row.error}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : !result ? (
            <Panel title="Analysis results" subtitle="Awaiting a log file">
              <EmptyState
                icon={FileSearch}
                title="No file analysed yet"
                message="Upload a CSV log export to see per-record classifications, severity counts and the alerts that were raised."
              />
            </Panel>
          ) : (
            <div className="space-y-4">
              <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-5">
                <SummaryTile
                  label="Total records"
                  value={formatNumber(result.total_records)}
                  tone="accent"
                  icon={FileSpreadsheet}
                />
                <SummaryTile
                  label="Normal events"
                  value={formatNumber(result.normal_events)}
                  tone="safe"
                  icon={CheckCircle2}
                />
                <SummaryTile
                  label="Suspicious"
                  value={formatNumber(result.suspicious_events)}
                  tone="warn"
                  icon={AlertTriangle}
                />
                <SummaryTile
                  label="High risk"
                  value={formatNumber(result.high_risk_events)}
                  tone="danger"
                  icon={FileWarning}
                />
                <SummaryTile
                  label="Critical"
                  value={formatNumber(result.critical)}
                  tone="critical"
                  icon={AlertTriangle}
                />
              </div>

              <Panel
                title="Ingestion summary"
                subtitle={`${result.filename} - ${result.alerts_created} alert(s) and ${result.incidents_created} incident(s) created`}
              >
                <div className="grid gap-3 sm:grid-cols-4">
                  {[
                    { label: 'LOW', value: result.low, color: '#22c55e' },
                    { label: 'MEDIUM', value: result.medium, color: '#f59e0b' },
                    { label: 'HIGH', value: result.high, color: '#fb7185' },
                    { label: 'CRITICAL', value: result.critical, color: '#dc2626' },
                  ].map((band) => (
                    <div
                      key={band.label}
                      className="rounded-lg border border-white/10 bg-navy-950/50 px-3 py-2.5 text-center"
                    >
                      <p className="text-xl font-semibold" style={{ color: band.color }}>
                        {band.value}
                      </p>
                      <p className="text-[0.62rem] uppercase tracking-wider text-slate-500">
                        {band.label}
                      </p>
                    </div>
                  ))}
                </div>

                {result.rejected_rows > 0 && (
                  <div className="mt-4 rounded-lg border border-warn/30 bg-warn/[0.07] px-3.5 py-3">
                    <p className="flex items-center gap-2 text-sm text-warn">
                      <AlertTriangle size={15} />
                      {result.rejected_rows} row(s) failed validation and were skipped
                    </p>
                    <ul className="mt-2 space-y-1">
                      {result.row_errors.map((row, index) => (
                        <li key={index} className="mono text-xs text-slate-400">
                          Row {row.row}: {row.error}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {result.alerts_created > 0 && (
                  <button
                    type="button"
                    onClick={() => navigate('/alerts')}
                    className="btn-secondary btn-sm mt-4"
                  >
                    View the {result.alerts_created} new alert(s)
                  </button>
                )}
              </Panel>

              <div className="grid gap-4 lg:grid-cols-2">
                <Panel title="Classifications found" bodyClassName="px-3 py-4">
                  <CategoryBarChart data={result.categories} height={240} />
                </Panel>
                <Panel title="Most active sources in this file" bodyClassName="px-3 py-4">
                  <SourceBarChart data={result.top_sources} height={240} />
                </Panel>
              </div>

              <Panel
                title="Per-record results"
                subtitle={`${visibleRows.length} of ${result.records.length} records shown`}
                bodyClassName="p-0"
                actions={
                  <div className="flex flex-wrap items-center gap-2">
                    <SearchInput
                      value={rowSearch}
                      onChange={setRowSearch}
                      placeholder="Filter by IP or class..."
                      className="w-52"
                    />
                    <Select
                      value={severityFilter}
                      onChange={setSeverityFilter}
                      options={[
                        { value: 'ALL', label: 'All severities' },
                        { value: 'CRITICAL', label: 'Critical' },
                        { value: 'HIGH', label: 'High' },
                        { value: 'MEDIUM', label: 'Medium' },
                        { value: 'LOW', label: 'Low' },
                      ]}
                      className="w-40"
                    />
                  </div>
                }
              >
                {visibleRows.length === 0 ? (
                  <p className="px-5 py-10 text-center text-sm text-slate-500">
                    No records match this filter.
                  </p>
                ) : (
                  <div className="table-wrap max-h-[30rem] overflow-y-auto">
                    <table className="data-table">
                      <thead className="sticky top-0 z-10">
                        <tr>
                          <th>Timestamp</th>
                          <th>Source</th>
                          <th>Destination</th>
                          <th>Classification</th>
                          <th>Risk</th>
                          <th>Severity</th>
                          <th>Top reason</th>
                        </tr>
                      </thead>
                      <tbody>
                        {visibleRows.slice(0, 300).map((row) => (
                          <tr key={row.event_id}>
                            <td className="whitespace-nowrap text-xs text-slate-400">
                              {formatDateTime(row.timestamp)}
                            </td>
                            <td className="mono text-xs">{row.source_ip}</td>
                            <td className="mono text-xs">
                              {row.destination_ip}
                              {row.destination_port ? `:${row.destination_port}` : ''}
                            </td>
                            <td className="text-xs text-slate-200">{row.classification}</td>
                            <td className="w-24">
                              <RiskBar score={row.risk_score} />
                            </td>
                            <td>
                              <SeverityBadge severity={row.severity} />
                            </td>
                            <td className="max-w-sm truncate text-xs text-slate-500">
                              {row.reason}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
                {visibleRows.length > 300 && (
                  <p className="border-t border-white/10 px-5 py-3 text-xs text-slate-500">
                    Showing the first 300 records. Export the results to review them all.
                  </p>
                )}
              </Panel>
            </div>
          )}
        </div>
      </div>
    </>
  )
}
