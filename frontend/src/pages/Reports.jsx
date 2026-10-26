/** Reports page (FR-11) - generate, preview and export security reports. */
import { useState } from 'react'
import {
  Download,
  FileBarChart,
  FileJson,
  FileSpreadsheet,
  FileText,
  Plus,
  RefreshCw,
  Trash2,
} from 'lucide-react'
import { useApi } from '../hooks/useApi'
import api, { saveBlob } from '../services/api'
import { useToast } from '../context/ToastContext'
import { CategoryBarChart, SeverityDonutChart } from '../components/charts/Charts'
import {
  ConfirmDialog,
  DetailRow,
  EmptyState,
  ErrorState,
  Field,
  Modal,
  PageHeader,
  Panel,
  SeverityBadge,
  SkeletonTable,
  Spinner,
} from '../components/ui'
import { formatDateTime, formatNumber, titleCase } from '../utils/format'

const PERIODS = [
  { value: 7, label: 'Last 7 days' },
  { value: 14, label: 'Last 14 days' },
  { value: 30, label: 'Last 30 days' },
  { value: 90, label: 'Last 90 days' },
]

const TYPES = [
  { value: 'SUMMARY', label: 'Summary report', description: 'Overall posture, severity mix and recommendations' },
  { value: 'THREAT', label: 'Threat report', description: 'Focused on detection categories and sources' },
  { value: 'INCIDENT', label: 'Incident report', description: 'Incident lifecycle and resolution statistics' },
  { value: 'COMPLIANCE', label: 'Compliance report', description: 'Audit-oriented view of activity and controls' },
]

function ReportContent({ content }) {
  if (!content) return null
  return (
    <div className="space-y-5">
      <div>
        <h3 className="text-base font-semibold text-slate-100">{content.title}</h3>
        <p className="mt-0.5 text-xs text-slate-500">
          Generated {formatDateTime(content.generated_at)} - covering the last{' '}
          {content.period?.days} day(s)
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        {Object.entries(content.summary || {}).map(([key, value]) => (
          <div key={key} className="rounded-lg border border-white/10 bg-navy-950/50 px-3.5 py-2.5">
            <p className="text-[0.62rem] uppercase tracking-wider text-slate-500">
              {titleCase(key)}
            </p>
            <p className="mt-0.5 text-lg font-semibold text-slate-100">{formatNumber(value)}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-lg border border-white/10 bg-navy-950/40 p-3">
          <p className="field-label">Severity breakdown</p>
          <SeverityDonutChart data={content.severity_breakdown} height={220} />
        </div>
        <div className="rounded-lg border border-white/10 bg-navy-950/40 p-3">
          <p className="field-label">Threat categories</p>
          <CategoryBarChart data={content.threat_categories} height={220} />
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-lg border border-white/10 bg-navy-950/40 px-4 py-2">
          <p className="field-label mt-2">Detection statistics</p>
          <dl className="divide-y divide-white/[0.06]">
            {Object.entries(content.detection_statistics || {})
              .filter(([key]) => !key.endsWith('_note'))
              .map(([key, value]) => (
                <DetailRow key={key} label={titleCase(key)} value={String(value ?? '-')} />
              ))}
          </dl>
          {content.detection_statistics?.accuracy_note && (
            <p className="pb-3 text-[0.66rem] leading-relaxed text-slate-500">
              {content.detection_statistics.accuracy_note}
            </p>
          )}
        </div>
        <div className="rounded-lg border border-white/10 bg-navy-950/40 px-4 py-2">
          <p className="field-label mt-2">Incident statistics</p>
          <dl className="divide-y divide-white/[0.06]">
            {Object.entries(content.incident_statistics || {}).map(([key, value]) => (
              <DetailRow key={key} label={titleCase(key)} value={String(value ?? '-')} />
            ))}
          </dl>
        </div>
      </div>

      {content.at_risk_assets?.length > 0 && (
        <div>
          <p className="field-label">Assets at elevated risk</p>
          <div className="table-wrap rounded-lg border border-white/10">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Asset</th>
                  <th>IP address</th>
                  <th>Risk level</th>
                  <th>Score</th>
                </tr>
              </thead>
              <tbody>
                {content.at_risk_assets.map((asset) => (
                  <tr key={asset.ip_address}>
                    <td className="text-slate-200">{asset.name}</td>
                    <td className="mono text-xs">{asset.ip_address}</td>
                    <td>
                      <SeverityBadge severity={asset.risk_level} />
                    </td>
                    <td className="mono text-xs">{asset.risk_score}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div>
        <p className="field-label">Recommendations</p>
        <ol className="space-y-2">
          {(content.recommendations || []).map((recommendation, index) => (
            <li key={index} className="flex items-start gap-2.5 text-sm text-slate-300">
              <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded bg-accent/15 text-[0.65rem] font-semibold text-accent">
                {index + 1}
              </span>
              {recommendation}
            </li>
          ))}
        </ol>
      </div>
    </div>
  )
}

export default function Reports() {
  const toast = useToast()
  const [days, setDays] = useState(30)
  const [reportType, setReportType] = useState('SUMMARY')
  const [title, setTitle] = useState('')
  const [generating, setGenerating] = useState(false)
  const [viewing, setViewing] = useState(null)
  const [deleting, setDeleting] = useState(null)
  const [busy, setBusy] = useState(false)
  const [downloading, setDownloading] = useState(null)

  const { data: reports, error, loading, refresh } = useApi(() => api.listReports({ per_page: 25 }), [])
  const { data: preview, loading: previewLoading, refresh: refreshPreview } = useApi(
    () => api.previewReport(days),
    [days],
  )

  const generate = async () => {
    setGenerating(true)
    try {
      const report = await api.generateReport({
        days,
        report_type: reportType,
        title: title.trim() || undefined,
      })
      toast.success(`Report ${report.report_code} generated.`)
      setTitle('')
      refresh({ quiet: true })
      setViewing(report)
    } catch (caught) {
      toast.error(caught.message)
    } finally {
      setGenerating(false)
    }
  }

  const download = async (report, format) => {
    setDownloading(`${report.id}-${format}`)
    try {
      const response = await api.downloadReport(report.id, format)
      const contentType = response.headers?.['content-type'] || ''
      if (contentType.includes('application/json') && format === 'pdf') {
        // The backend returns JSON when ReportLab is unavailable.
        const text = await response.data.text()
        const payload = JSON.parse(text)
        toast.warning(payload.message)
        return
      }
      const filename = saveBlob(response, `${report.report_code}.${format}`)
      toast.success(`Downloaded ${filename}.`)
    } catch (caught) {
      toast.error(caught.message)
    } finally {
      setDownloading(null)
    }
  }

  const confirmDelete = async () => {
    setBusy(true)
    try {
      await api.deleteReport(deleting.id)
      toast.success(`Report ${deleting.report_code} deleted.`)
      setDeleting(null)
      refresh({ quiet: true })
    } catch (caught) {
      toast.error(caught.message)
    } finally {
      setBusy(false)
    }
  }

  const openReport = async (report) => {
    try {
      const full = await api.getReport(report.id)
      setViewing(full)
    } catch (caught) {
      toast.error(caught.message)
    }
  }

  const rows = reports?.data || []

  return (
    <>
      <PageHeader
        title="Security Reports"
        description="Generate a point-in-time report from the live database and export it as PDF, CSV or JSON."
        icon={FileBarChart}
      >
        <button type="button" onClick={() => refresh()} className="btn-secondary btn-sm" disabled={loading}>
          {loading ? <Spinner size={14} /> : <RefreshCw size={14} />}
          Refresh
        </button>
      </PageHeader>

      <div className="grid gap-4 xl:grid-cols-3">
        <div className="space-y-4">
          <Panel title="Generate a report" subtitle="Choose the period and report type">
            <div className="space-y-4">
              <Field label="Reporting period">
                <select
                  value={days}
                  onChange={(event) => setDays(Number(event.target.value))}
                  className="field-input cursor-pointer"
                >
                  {PERIODS.map((period) => (
                    <option key={period.value} value={period.value} className="bg-navy-900">
                      {period.label}
                    </option>
                  ))}
                </select>
              </Field>

              <div>
                <span className="field-label">Report type</span>
                <div className="space-y-2">
                  {TYPES.map((type) => (
                    <button
                      key={type.value}
                      type="button"
                      onClick={() => setReportType(type.value)}
                      className={`flex w-full items-start gap-2.5 rounded-lg border px-3.5 py-2.5 text-left transition-all ${
                        reportType === type.value
                          ? 'border-accent/50 bg-accent/[0.07]'
                          : 'border-white/10 bg-navy-950/40 hover:border-accent/30'
                      }`}
                    >
                      <span
                        className={`mt-1 h-2 w-2 shrink-0 rounded-full ${
                          reportType === type.value ? 'bg-accent' : 'bg-slate-600'
                        }`}
                      />
                      <span className="min-w-0">
                        <span className="block text-sm text-slate-200">{type.label}</span>
                        <span className="block text-[0.68rem] text-slate-500">
                          {type.description}
                        </span>
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              <Field label="Custom title" hint="Leave blank to use the default title">
                <input
                  type="text"
                  value={title}
                  onChange={(event) => setTitle(event.target.value)}
                  placeholder="Monthly SOC review - March"
                  className="field-input"
                />
              </Field>

              <button
                type="button"
                onClick={generate}
                className="btn-primary w-full"
                disabled={generating}
              >
                {generating ? (
                  <>
                    <Spinner size={16} />
                    Generating...
                  </>
                ) : (
                  <>
                    <Plus size={16} />
                    Generate Report
                  </>
                )}
              </button>
            </div>
          </Panel>

          <Panel
            title="Live preview"
            subtitle={`Figures for the last ${days} days, computed now`}
            actions={
              <button
                type="button"
                onClick={() => refreshPreview()}
                className="btn-ghost btn-sm"
                disabled={previewLoading}
              >
                {previewLoading ? <Spinner size={13} /> : <RefreshCw size={13} />}
              </button>
            }
          >
            {previewLoading && !preview ? (
              <SkeletonTable rows={4} columns={2} />
            ) : (
              <dl className="divide-y divide-white/[0.06]">
                {Object.entries(preview?.summary || {}).map(([key, value]) => (
                  <DetailRow key={key} label={titleCase(key)} value={formatNumber(value)} mono />
                ))}
              </dl>
            )}
          </Panel>
        </div>

        <Panel
          title="Generated reports"
          subtitle="Stored in the reports table and re-downloadable at any time"
          className="xl:col-span-2"
          bodyClassName="p-0"
        >
          {loading && !reports ? (
            <SkeletonTable rows={6} columns={6} />
          ) : error ? (
            <ErrorState error={error} onRetry={refresh} />
          ) : rows.length === 0 ? (
            <EmptyState
              icon={FileBarChart}
              title="No reports generated yet"
              message="Choose a period on the left and press Generate Report. The report is built from the live database and stored for re-download."
            />
          ) : (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Report</th>
                    <th>Type</th>
                    <th>Period</th>
                    <th>Events</th>
                    <th>Threats</th>
                    <th>Generated</th>
                    <th className="text-right">Export</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((report) => (
                    <tr key={report.id}>
                      <td>
                        <button
                          type="button"
                          onClick={() => openReport(report)}
                          className="text-left"
                        >
                          <span className="mono block text-xs text-accent hover:underline">
                            {report.report_code}
                          </span>
                          <span className="block max-w-xs truncate text-xs text-slate-400">
                            {report.title}
                          </span>
                        </button>
                      </td>
                      <td className="text-xs text-slate-400">{titleCase(report.report_type)}</td>
                      <td className="text-xs text-slate-400">{report.period_days} days</td>
                      <td className="mono text-xs">{formatNumber(report.total_events)}</td>
                      <td className="mono text-xs">{formatNumber(report.total_threats)}</td>
                      <td className="whitespace-nowrap text-xs text-slate-500">
                        {formatDateTime(report.generated_at)}
                        <span className="block text-[0.65rem] text-slate-600">
                          by {report.generated_by}
                        </span>
                      </td>
                      <td>
                        <div className="flex items-center justify-end gap-1">
                          {[
                            { format: 'pdf', icon: FileText, title: 'Download PDF' },
                            { format: 'csv', icon: FileSpreadsheet, title: 'Download CSV' },
                            { format: 'json', icon: FileJson, title: 'Download JSON' },
                          ].map((option) => {
                            const Icon = option.icon
                            const key = `${report.id}-${option.format}`
                            return (
                              <button
                                key={option.format}
                                type="button"
                                onClick={() => download(report, option.format)}
                                className="btn-ghost btn-sm"
                                title={option.title}
                                disabled={downloading === key}
                              >
                                {downloading === key ? <Spinner size={14} /> : <Icon size={14} />}
                              </button>
                            )
                          })}
                          <button
                            type="button"
                            onClick={() => setDeleting(report)}
                            className="btn-ghost btn-sm text-danger"
                            title="Delete report"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Panel>
      </div>

      <Modal
        open={Boolean(viewing)}
        onClose={() => setViewing(null)}
        title={viewing?.report_code || 'Report'}
        description={viewing?.title}
        size="lg"
        footer={
          viewing && (
            <>
              <button
                type="button"
                className="btn-secondary btn-sm"
                onClick={() => download(viewing, 'csv')}
              >
                <Download size={14} />
                CSV
              </button>
              <button
                type="button"
                className="btn-primary btn-sm"
                onClick={() => download(viewing, 'pdf')}
              >
                <Download size={14} />
                PDF
              </button>
            </>
          )
        }
      >
        <ReportContent content={viewing?.content} />
      </Modal>

      <ConfirmDialog
        open={Boolean(deleting)}
        onClose={() => setDeleting(null)}
        onConfirm={confirmDelete}
        title={`Delete ${deleting?.report_code}?`}
        message="The stored report is permanently removed. Any file you have already downloaded is unaffected."
        confirmLabel="Delete report"
        busy={busy}
      />
    </>
  )
}
