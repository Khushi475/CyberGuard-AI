/**
 * Chart components.
 *
 * All of these are fed exclusively from backend API responses - no chart in this
 * application contains hard-coded statistics.
 */
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { CHART_PALETTE, SEVERITY_COLORS, formatCompact, formatShortDate } from '../../utils/format'
import { EmptyState } from '../ui'

const AXIS = {
  stroke: '#64748b',
  fontSize: 11,
  tickLine: false,
  axisLine: false,
}

const GRID = { stroke: 'rgba(148,163,184,0.12)', strokeDasharray: '3 3' }

function ChartTooltip({ active, payload, label, valueSuffix = '' }) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-lg border border-white/10 bg-navy-900/97 px-3 py-2 shadow-panel backdrop-blur">
      {label !== undefined && <p className="mb-1 text-xs font-medium text-slate-300">{label}</p>}
      {payload.map((entry) => (
        <p key={entry.dataKey || entry.name} className="flex items-center gap-2 text-xs">
          <span
            className="h-2 w-2 shrink-0 rounded-full"
            style={{ backgroundColor: entry.color || entry.payload?.fill }}
          />
          <span className="text-slate-400">{entry.name}:</span>
          <span className="mono font-medium text-slate-100">
            {typeof entry.value === 'number' ? entry.value.toLocaleString() : entry.value}
            {valueSuffix}
          </span>
        </p>
      ))}
    </div>
  )
}

function ChartEmpty({ message = 'No data available yet.' }) {
  return (
    <div className="flex h-full min-h-[200px] items-center justify-center">
      <p className="text-sm text-slate-500">{message}</p>
    </div>
  )
}

/** Stacked area: threats per day, split by severity. */
export function ThreatsOverTimeChart({ data = [], height = 260 }) {
  if (!data.length) return <ChartEmpty />
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 6, right: 8, left: -18, bottom: 0 }}>
        <defs>
          {Object.entries(SEVERITY_COLORS).map(([severity, color]) => (
            <linearGradient key={severity} id={`grad-${severity}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.55} />
              <stop offset="95%" stopColor={color} stopOpacity={0.04} />
            </linearGradient>
          ))}
        </defs>
        <CartesianGrid {...GRID} vertical={false} />
        <XAxis dataKey="date" tickFormatter={formatShortDate} {...AXIS} minTickGap={18} />
        <YAxis allowDecimals={false} tickFormatter={formatCompact} {...AXIS} width={44} />
        <Tooltip content={<ChartTooltip />} />
        <Legend wrapperStyle={{ fontSize: 11, paddingTop: 8 }} iconType="circle" iconSize={8} />
        {['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map((severity) => (
          <Area
            key={severity}
            type="monotone"
            dataKey={severity}
            name={severity}
            stackId="severity"
            stroke={SEVERITY_COLORS[severity]}
            strokeWidth={1.6}
            fill={`url(#grad-${severity})`}
          />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  )
}

/** Donut: how detections split across the four severity bands. */
export function SeverityDonutChart({ data = [], height = 260 }) {
  const rows = data.filter((row) => row.count > 0)
  if (!rows.length) return <ChartEmpty />
  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie
          data={rows}
          dataKey="count"
          nameKey="severity"
          innerRadius="55%"
          outerRadius="80%"
          paddingAngle={3}
          stroke="none"
        >
          {rows.map((row) => (
            <Cell key={row.severity} fill={SEVERITY_COLORS[row.severity] || '#64748b'} />
          ))}
        </Pie>
        <Tooltip content={<ChartTooltip />} />
        <Legend
          verticalAlign="bottom"
          wrapperStyle={{ fontSize: 11 }}
          iconType="circle"
          iconSize={8}
        />
      </PieChart>
    </ResponsiveContainer>
  )
}

/** Horizontal bars: which threat categories dominate. */
export function CategoryBarChart({ data = [], height = 260 }) {
  if (!data.length) return <ChartEmpty message="No threats classified yet." />
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 16, left: 4, bottom: 4 }}>
        <CartesianGrid {...GRID} horizontal={false} />
        <XAxis type="number" allowDecimals={false} {...AXIS} />
        <YAxis
          type="category"
          dataKey="category"
          width={150}
          tick={{ fill: '#94a3b8', fontSize: 11 }}
          tickLine={false}
          axisLine={false}
        />
        <Tooltip content={<ChartTooltip />} cursor={{ fill: 'rgba(148,163,184,0.06)' }} />
        <Bar dataKey="count" name="Detections" radius={[0, 4, 4, 0]} barSize={16}>
          {data.map((row, index) => (
            <Cell key={row.category} fill={CHART_PALETTE[index % CHART_PALETTE.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

/** Vertical bars: busiest source addresses. */
export function SourceBarChart({ data = [], height = 260 }) {
  if (!data.length) return <ChartEmpty />
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 6, right: 8, left: -18, bottom: 34 }}>
        <CartesianGrid {...GRID} vertical={false} />
        <XAxis
          dataKey="source_ip"
          angle={-32}
          textAnchor="end"
          interval={0}
          height={56}
          tick={{ fill: '#94a3b8', fontSize: 10 }}
          tickLine={false}
          axisLine={false}
        />
        <YAxis allowDecimals={false} tickFormatter={formatCompact} {...AXIS} width={44} />
        <Tooltip content={<ChartTooltip />} cursor={{ fill: 'rgba(148,163,184,0.06)' }} />
        <Bar dataKey="count" name="Events" fill="#22d3ee" radius={[4, 4, 0, 0]} barSize={22} />
      </BarChart>
    </ResponsiveContainer>
  )
}

/** Dual line: events ingested vs threats detected per day. */
export function DetectionTrendChart({ data = [], height = 260 }) {
  if (!data.length) return <ChartEmpty />
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 6, right: 8, left: -18, bottom: 0 }}>
        <CartesianGrid {...GRID} vertical={false} />
        <XAxis dataKey="date" tickFormatter={formatShortDate} {...AXIS} minTickGap={18} />
        <YAxis allowDecimals={false} tickFormatter={formatCompact} {...AXIS} width={44} />
        <Tooltip content={<ChartTooltip />} />
        <Legend wrapperStyle={{ fontSize: 11, paddingTop: 8 }} iconType="circle" iconSize={8} />
        <Line
          type="monotone"
          dataKey="events"
          name="Events analysed"
          stroke="#38bdf8"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4 }}
        />
        <Line
          type="monotone"
          dataKey="threats"
          name="Threats detected"
          stroke="#fb7185"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4 }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}

/** Generic donut used for protocol / event-type / channel breakdowns. */
export function DistributionDonut({ data = [], nameKey, height = 240 }) {
  const rows = (data || []).filter((row) => row.count > 0)
  if (!rows.length) return <ChartEmpty />
  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie
          data={rows}
          dataKey="count"
          nameKey={nameKey}
          innerRadius="52%"
          outerRadius="78%"
          paddingAngle={3}
          stroke="none"
        >
          {rows.map((row, index) => (
            <Cell key={row[nameKey]} fill={CHART_PALETTE[index % CHART_PALETTE.length]} />
          ))}
        </Pie>
        <Tooltip content={<ChartTooltip />} />
        <Legend
          verticalAlign="bottom"
          wrapperStyle={{ fontSize: 11 }}
          iconType="circle"
          iconSize={8}
        />
      </PieChart>
    </ResponsiveContainer>
  )
}

/** Bars showing when during the day activity occurs. */
export function HourlyBarChart({ data = [], height = 240 }) {
  if (!data.length) return <ChartEmpty />
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 6, right: 8, left: -18, bottom: 0 }}>
        <CartesianGrid {...GRID} vertical={false} />
        <XAxis dataKey="hour" {...AXIS} interval={2} />
        <YAxis allowDecimals={false} tickFormatter={formatCompact} {...AXIS} width={44} />
        <Tooltip content={<ChartTooltip />} cursor={{ fill: 'rgba(148,163,184,0.06)' }} />
        <Bar dataKey="count" name="Events" radius={[3, 3, 0, 0]}>
          {data.map((row) => (
            <Cell
              key={row.hour}
              fill={Number(row.hour) < 6 || Number(row.hour) >= 22 ? '#f59e0b' : '#22d3ee'}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

export { ChartEmpty, EmptyState }
