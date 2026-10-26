/**
 * Dashboard (FR-02).
 *
 * Every figure and every chart on this page is fetched from
 * GET /api/dashboard/stats. Nothing here is hard-coded.
 */
import { useNavigate } from 'react-router-dom'
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Cpu,
  Database,
  FileWarning,
  Gauge,
  LayoutDashboard,
  RefreshCw,
  Server,
  Shield,
  ShieldAlert,
  Siren,
  TrendingUp,
} from 'lucide-react'
import { useApi } from '../hooks/useApi'
import api from '../services/api'
import {
  CategoryBarChart,
  DetectionTrendChart,
  DistributionDonut,
  SeverityDonutChart,
  SourceBarChart,
  ThreatsOverTimeChart,
} from '../components/charts/Charts'
import {
  ErrorState,
  PageHeader,
  Panel,
  RiskBar,
  SeverityBadge,
  SkeletonCard,
  Spinner,
  StatusBadge,
} from '../components/ui'
import { SEVERITY_COLORS, formatNumber, timeAgo } from '../utils/format'

const THREAT_LEVEL_STYLE = {
  LOW: { ring: 'border-safe/40 bg-safe/10', text: 'text-safe', label: 'Normal operations' },
  MEDIUM: { ring: 'border-warn/40 bg-warn/10', text: 'text-warn', label: 'Elevated - review queue' },
  HIGH: { ring: 'border-rose-400/40 bg-rose-400/10', text: 'text-rose-300', label: 'High - act now' },
  CRITICAL: {
    ring: 'border-critical/50 bg-critical/15',
    text: 'text-red-300',
    label: 'Critical - immediate response',
  },
}

function StatCard({ label, value, icon: Icon, tone = 'accent', footer, onClick }) {
  const tones = {
    accent: 'border-accent/25 bg-accent/10 text-accent',
    danger: 'border-danger/25 bg-danger/10 text-danger',
    warn: 'border-warn/25 bg-warn/10 text-warn',
    safe: 'border-safe/25 bg-safe/10 text-safe',
    info: 'border-info/25 bg-info/10 text-info',
    violet: 'border-violet-400/25 bg-violet-400/10 text-violet-300',
  }
  const Element = onClick ? 'button' : 'div'
  return (
    <Element
      type={onClick ? 'button' : undefined}
      onClick={onClick}
      className={`panel panel-hover flex w-full items-start gap-4 p-5 text-left ${
        onClick ? 'cursor-pointer' : ''
      }`}
    >
      <span className={`shrink-0 rounded-lg border p-2.5 ${tones[tone]}`}>
        <Icon size={19} />
      </span>
      <span className="min-w-0 flex-1">
        <span className="block text-xs uppercase tracking-wider text-slate-500">{label}</span>
        <span className="mt-1 block text-2xl font-semibold tracking-tight text-slate-100">
          {value}
        </span>
        {footer && <span className="mt-1 block text-xs text-slate-500">{footer}</span>}
      </span>
    </Element>
  )
}

function ThreatLevelCard({ threatLevel }) {
  const style = THREAT_LEVEL_STYLE[threatLevel?.level] || THREAT_LEVEL_STYLE.LOW
  const counts = threatLevel?.open_by_severity || {}
  return (
    <div className={`panel border ${style.ring} p-5`}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-wider text-slate-400">Current threat level</p>
          <p className={`mt-1 text-3xl font-bold tracking-tight ${style.text}`}>
            {threatLevel?.level || 'LOW'}
          </p>
          <p className="mt-0.5 text-xs text-slate-400">{style.label}</p>
        </div>
        <Shield size={30} className={style.text} />
      </div>

      <div className="mt-4">
        <RiskBar score={threatLevel?.score || 0} />
      </div>

      <div className="mt-4 grid grid-cols-4 gap-2">
        {['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map((severity) => (
          <div key={severity} className="rounded-lg border border-white/10 bg-navy-950/50 px-2 py-2 text-center">
            <p
              className="text-base font-semibold"
              style={{ color: SEVERITY_COLORS[severity] }}
            >
              {counts[severity] ?? 0}
            </p>
            <p className="text-[0.6rem] uppercase tracking-wide text-slate-500">{severity}</p>
          </div>
        ))}
      </div>
      <p className="mt-3 text-[0.68rem] leading-relaxed text-slate-500">{threatLevel?.basis}</p>
    </div>
  )
}

function ActivityFeed({ items = [] }) {
  const icons = { alert: Siren, incident: ShieldAlert, audit: Activity }
  const colors = {
    CRITICAL: 'text-red-300',
    HIGH: 'text-rose-300',
    MEDIUM: 'text-warn',
    LOW: 'text-slate-400',
  }
  if (!items.length) {
    return <p className="py-8 text-center text-sm text-slate-500">No recent activity recorded.</p>
  }
  return (
    <ul className="divide-y divide-white/[0.06]">
      {items.map((item, index) => {
        const Icon = icons[item.type] || Activity
        return (
          <li key={`${item.type}-${item.entity_id}-${index}`} className="flex gap-3 py-3 first:pt-0 last:pb-0">
            <span className={`mt-0.5 shrink-0 ${colors[item.severity] || 'text-slate-400'}`}>
              <Icon size={15} />
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm text-slate-200">{item.title}</p>
              <p className="mt-0.5 line-clamp-2 text-xs text-slate-500">{item.message}</p>
            </div>
            <span className="mono shrink-0 text-[0.68rem] text-slate-600">
              {timeAgo(item.timestamp)}
            </span>
          </li>
        )
      })}
    </ul>
  )
}

function HealthPanel({ health, quality }) {
  const statusTone = {
    OPERATIONAL: 'text-safe',
    FALLBACK: 'text-warn',
    BACKLOG: 'text-warn',
    DEGRADED: 'text-danger',
  }
  const icons = {
    Database: Database,
    'Detection Engine': Cpu,
    'ML Models': Gauge,
    'Event Pipeline': Activity,
  }
  return (
    <div className="space-y-4">
      <div className="flex items-baseline justify-between">
        <div>
          <p className="text-2xl font-semibold tracking-tight text-slate-100">
            {quality?.accuracy ?? 0}%
          </p>
          <p className="text-xs text-slate-400">{quality?.label || 'Detection accuracy'}</p>
        </div>
        <div className="text-right">
          <p className={`text-sm font-semibold ${statusTone[health?.overall] || 'text-slate-300'}`}>
            {health?.overall || 'UNKNOWN'}
          </p>
          <p className="text-xs text-slate-500">Health score {health?.score ?? 0}/100</p>
        </div>
      </div>

      <p className="rounded-lg border border-white/10 bg-navy-950/50 px-3 py-2 text-[0.68rem] leading-relaxed text-slate-500">
        {quality?.note}
      </p>

      <ul className="space-y-2">
        {(health?.checks || []).map((check) => {
          const Icon = icons[check.component] || Activity
          return (
            <li
              key={check.component}
              className="flex items-start gap-2.5 rounded-lg border border-white/10 bg-navy-950/40 px-3 py-2.5"
            >
              <Icon size={14} className={`mt-0.5 shrink-0 ${statusTone[check.status] || 'text-slate-400'}`} />
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-xs font-medium text-slate-200">{check.component}</p>
                  <span className={`text-[0.65rem] font-semibold ${statusTone[check.status] || 'text-slate-400'}`}>
                    {check.status}
                  </span>
                </div>
                <p className="mt-0.5 text-[0.68rem] text-slate-500">{check.detail}</p>
              </div>
            </li>
          )
        })}
      </ul>
    </div>
  )
}

export default function Dashboard() {
  const navigate = useNavigate()
  const { data, error, loading, refresh } = useApi(() => api.dashboardStats(14), [], {
    pollMs: 45000,
  })

  if (loading && !data) {
    return (
      <>
        <PageHeader title="Security Overview" icon={LayoutDashboard} />
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 8 }).map((_, index) => (
            <SkeletonCard key={index} />
          ))}
        </div>
      </>
    )
  }

  if (error && !data) {
    return (
      <>
        <PageHeader title="Security Overview" icon={LayoutDashboard} />
        <div className="panel">
          <ErrorState error={error} onRetry={refresh} />
        </div>
      </>
    )
  }

  const totals = data?.totals || {}
  const charts = data?.charts || {}

  return (
    <>
      <PageHeader
        title="Security Overview"
        description="Live posture of the monitored estate. All figures are computed from the security event database."
        icon={LayoutDashboard}
      >
        <span className="hidden items-center gap-1.5 text-xs text-slate-500 sm:flex">
          <Clock size={13} />
          Updated {timeAgo(data?.generated_at)}
        </span>
        <button type="button" onClick={() => refresh()} className="btn-secondary btn-sm" disabled={loading}>
          {loading ? <Spinner size={14} /> : <RefreshCw size={14} />}
          Refresh
        </button>
      </PageHeader>

      {/* KPI row */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Total Events"
          value={formatNumber(totals.total_events)}
          icon={Activity}
          tone="accent"
          footer={`${formatNumber(totals.events_last_24h)} in the last 24 hours`}
        />
        <StatCard
          label="Threats Detected"
          value={formatNumber(totals.threats_detected)}
          icon={AlertTriangle}
          tone="warn"
          footer={`${formatNumber(totals.threats_last_24h)} in the last 24 hours`}
          onClick={() => navigate('/alerts')}
        />
        <StatCard
          label="Critical Alerts"
          value={formatNumber(totals.critical_alerts)}
          icon={Siren}
          tone="danger"
          footer={`${formatNumber(totals.open_alerts)} alerts still open`}
          onClick={() => navigate('/alerts?severity=CRITICAL')}
        />
        <StatCard
          label="Active Incidents"
          value={formatNumber(totals.active_incidents)}
          icon={ShieldAlert}
          tone="violet"
          footer={`${formatNumber(totals.resolved_incidents)} resolved to date`}
          onClick={() => navigate('/incidents')}
        />
      </div>

      <div className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Monitored Assets"
          value={formatNumber(totals.monitored_assets)}
          icon={Server}
          tone="info"
          footer={`${formatNumber(totals.assets_at_risk)} at high or critical risk`}
          onClick={() => navigate('/assets')}
        />
        <StatCard
          label="Detection Accuracy"
          value={`${data?.detection_quality?.accuracy ?? 0}%`}
          icon={TrendingUp}
          tone="safe"
          footer={data?.detection_quality?.label}
        />
        <StatCard
          label="Active Indicators"
          value={formatNumber(totals.active_indicators)}
          icon={FileWarning}
          tone="warn"
          footer="Simulated threat-intelligence feed"
          onClick={() => navigate('/threat-intelligence')}
        />
        <StatCard
          label="System Health"
          value={`${data?.system_health?.score ?? 0}/100`}
          icon={CheckCircle2}
          tone={data?.system_health?.overall === 'OPERATIONAL' ? 'safe' : 'warn'}
          footer={data?.system_health?.overall}
        />
      </div>

      {/* Threat level + primary trend */}
      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        <ThreatLevelCard threatLevel={data?.threat_level} />
        <Panel
          title="Threats over time"
          subtitle="Detections per day, stacked by severity band (last 14 days)"
          className="lg:col-span-2"
          bodyClassName="px-3 py-4"
        >
          <ThreatsOverTimeChart data={charts.threats_over_time} />
        </Panel>
      </div>

      {/* Distribution charts */}
      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        <Panel
          title="Severity distribution"
          subtitle="Across all analysed events"
          bodyClassName="px-3 py-4"
        >
          <SeverityDonutChart data={charts.severity_distribution} />
        </Panel>
        <Panel
          title="Threat categories"
          subtitle="What the engine is classifying"
          bodyClassName="px-3 py-4"
        >
          <CategoryBarChart data={charts.category_distribution} />
        </Panel>
        <Panel
          title="Protocol mix"
          subtitle="Traffic composition by protocol"
          bodyClassName="px-3 py-4"
        >
          <DistributionDonut data={charts.protocol_distribution} nameKey="protocol" height={260} />
        </Panel>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <Panel
          title="Detection trend"
          subtitle="Events analysed versus threats detected"
          bodyClassName="px-3 py-4"
        >
          <DetectionTrendChart data={charts.detection_trend} />
        </Panel>
        <Panel
          title="Most active sources"
          subtitle="Source addresses generating the most events"
          bodyClassName="px-3 py-4"
        >
          <SourceBarChart data={charts.events_by_source} />
        </Panel>
      </div>

      {/* Recent alerts, activity, health */}
      <div className="mt-4 grid gap-4 xl:grid-cols-3">
        <Panel
          title="Recent alerts"
          subtitle="Newest detections needing triage"
          className="xl:col-span-2"
          bodyClassName="p-0"
          actions={
            <button type="button" onClick={() => navigate('/alerts')} className="btn-ghost btn-sm">
              View all
            </button>
          }
        >
          {(data?.recent_alerts || []).length === 0 ? (
            <p className="py-10 text-center text-sm text-slate-500">
              No alerts have been raised yet. Analyse an event or upload a log file to generate one.
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
                    <th>Risk</th>
                    <th>Status</th>
                    <th>Raised</th>
                  </tr>
                </thead>
                <tbody>
                  {data.recent_alerts.map((alert) => (
                    <tr
                      key={alert.id}
                      className="cursor-pointer"
                      onClick={() => navigate(`/alerts?focus=${alert.id}`)}
                    >
                      <td className="mono text-accent">{alert.alert_code}</td>
                      <td className="text-slate-200">{alert.threat_type}</td>
                      <td className="mono">{alert.source_ip}</td>
                      <td>
                        <SeverityBadge severity={alert.severity} />
                      </td>
                      <td className="w-28">
                        <RiskBar score={alert.risk_score} />
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

        <Panel title="System health" subtitle="Self-check of each subsystem">
          <HealthPanel health={data?.system_health} quality={data?.detection_quality} />
        </Panel>
      </div>

      <div className="mt-4">
        <Panel
          title="Activity feed"
          subtitle="Merged stream of alerts, incident transitions and audited actions"
        >
          <ActivityFeed items={data?.activity_feed} />
        </Panel>
      </div>
    </>
  )
}
