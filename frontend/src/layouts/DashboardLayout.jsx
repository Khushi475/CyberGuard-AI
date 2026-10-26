/** Application shell: sidebar navigation, top bar and routed content area. */
import { useEffect, useRef, useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import {
  Activity,
  Bell,
  ChevronDown,
  FileBarChart,
  FileSearch,
  Gauge,
  LayoutDashboard,
  LogOut,
  Menu,
  Radar,
  Search,
  Server,
  Settings as SettingsIcon,
  Shield,
  ShieldAlert,
  Siren,
  User as UserIcon,
  X,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { useApi } from '../hooks/useApi'
import api from '../services/api'
import { SEVERITY_BADGE, timeAgo, titleCase } from '../utils/format'

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/detection', label: 'Threat Detection', icon: Radar },
  { to: '/alerts', label: 'Alerts', icon: Siren },
  { to: '/incidents', label: 'Incidents', icon: ShieldAlert },
  { to: '/threat-intelligence', label: 'Threat Intelligence', icon: Activity },
  { to: '/log-analyzer', label: 'Log Analyzer', icon: FileSearch },
  { to: '/assets', label: 'Assets', icon: Server },
  { to: '/reports', label: 'Reports', icon: FileBarChart },
  { to: '/settings', label: 'Settings', icon: SettingsIcon },
]

const SEARCH_TARGETS = [
  { keywords: ['alert', 'alerts', 'triage', 'queue'], to: '/alerts', label: 'Alerts' },
  { keywords: ['incident', 'incidents', 'case'], to: '/incidents', label: 'Incidents' },
  { keywords: ['asset', 'assets', 'server', 'host', 'inventory'], to: '/assets', label: 'Assets' },
  { keywords: ['indicator', 'intel', 'intelligence', 'ioc'], to: '/threat-intelligence', label: 'Threat Intelligence' },
  { keywords: ['log', 'csv', 'upload', 'analyzer'], to: '/log-analyzer', label: 'Log Analyzer' },
  { keywords: ['report', 'reports', 'pdf', 'export'], to: '/reports', label: 'Reports' },
  { keywords: ['detect', 'detection', 'analyse', 'analyze', 'scan'], to: '/detection', label: 'Threat Detection' },
  { keywords: ['setting', 'settings', 'profile', 'password', 'theme'], to: '/settings', label: 'Settings' },
  { keywords: ['dashboard', 'overview', 'home', 'stats'], to: '/dashboard', label: 'Dashboard' },
]

function SidebarContent({ onNavigate, engineMode }) {
  return (
    <>
      <div className="flex items-center gap-3 border-b border-white/10 px-5 py-4">
        <span className="relative rounded-lg border border-accent/30 bg-accent/10 p-2 text-accent">
          <Shield size={20} />
          <span className="absolute -right-0.5 -top-0.5 h-2 w-2 animate-pulse-ring rounded-full bg-accent" />
        </span>
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold tracking-tight text-slate-100">CyberGuard AI</p>
          <p className="truncate text-[0.68rem] uppercase tracking-wider text-slate-500">
            Threat Detection Console
          </p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4" aria-label="Main navigation">
        {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            onClick={onNavigate}
            className={({ isActive }) => `nav-link ${isActive ? 'nav-link-active' : ''}`}
          >
            <Icon size={17} className="shrink-0" />
            <span className="truncate">{label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-white/10 px-4 py-3.5">
        <div className="flex items-center gap-2 text-xs">
          <span className="h-2 w-2 shrink-0 rounded-full bg-safe" />
          <span className="text-slate-400">Engine</span>
          <span className="mono ml-auto truncate text-slate-300">{engineMode || 'checking...'}</span>
        </div>
        <p className="mt-2 text-[0.66rem] leading-relaxed text-slate-600">
          Academic prototype - simulated defensive telemetry only.
        </p>
      </div>
    </>
  )
}

export default function DashboardLayout() {
  const { user, logout } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()
  const location = useLocation()

  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const [notificationsOpen, setNotificationsOpen] = useState(false)
  const [search, setSearch] = useState('')
  const menuRef = useRef(null)
  const notificationsRef = useRef(null)

  const { data: health } = useApi(() => api.health(), [], { pollMs: 60000 })
  const { data: alertFeed } = useApi(
    () => api.listAlerts({ status: 'NEW', per_page: 6, sort: 'risk' }),
    [location.pathname],
    { pollMs: 30000 },
  )

  const notifications = alertFeed?.data || []

  useEffect(() => {
    setSidebarOpen(false)
    setMenuOpen(false)
    setNotificationsOpen(false)
  }, [location.pathname])

  useEffect(() => {
    const onClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) setMenuOpen(false)
      if (notificationsRef.current && !notificationsRef.current.contains(event.target)) {
        setNotificationsOpen(false)
      }
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [])

  const handleSearch = (event) => {
    event.preventDefault()
    const query = search.trim().toLowerCase()
    if (!query) return
    const match = SEARCH_TARGETS.find((target) =>
      target.keywords.some((keyword) => keyword.startsWith(query) || query.startsWith(keyword)),
    )
    if (match) {
      navigate(match.to)
      toast.info(`Opened ${match.label}.`)
    } else {
      // Anything else is treated as an indicator search against the alert queue.
      navigate(`/alerts?search=${encodeURIComponent(search.trim())}`)
      toast.info(`Searching alerts for "${search.trim()}".`)
    }
    setSearch('')
  }

  const handleLogout = async () => {
    await logout()
    toast.success('You have been signed out.')
    navigate('/login', { replace: true })
  }

  const engineMode = health?.detection_engine?.mode
  const initials = (user?.full_name || 'A')
    .split(' ')
    .map((part) => part[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()

  return (
    <div className="flex min-h-screen">
      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 flex-col border-r border-white/10 bg-navy-900/85 backdrop-blur lg:flex">
        <SidebarContent engineMode={engineMode} />
      </aside>

      {/* Mobile sidebar */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div
            className="absolute inset-0 bg-navy-950/80 backdrop-blur-sm"
            onClick={() => setSidebarOpen(false)}
            aria-hidden="true"
          />
          <aside className="relative flex h-full w-64 animate-slide-in flex-col border-r border-white/10 bg-navy-900">
            <button
              type="button"
              onClick={() => setSidebarOpen(false)}
              className="absolute right-3 top-4 rounded p-1 text-slate-400 hover:text-slate-100"
              aria-label="Close navigation"
            >
              <X size={18} />
            </button>
            <SidebarContent onNavigate={() => setSidebarOpen(false)} engineMode={engineMode} />
          </aside>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col lg:pl-64">
        {/* Top bar */}
        <header className="sticky top-0 z-20 border-b border-white/10 bg-navy-950/85 backdrop-blur">
          <div className="flex h-16 items-center gap-3 px-4 sm:px-6">
            <button
              type="button"
              onClick={() => setSidebarOpen(true)}
              className="rounded-lg p-2 text-slate-400 hover:bg-white/5 hover:text-slate-100 lg:hidden"
              aria-label="Open navigation"
            >
              <Menu size={20} />
            </button>

            <form onSubmit={handleSearch} className="relative hidden max-w-sm flex-1 sm:block">
              <Search
                size={15}
                className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500"
              />
              <input
                type="search"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search pages, IP addresses, alert codes..."
                className="field-input py-2 pl-9 text-sm"
                aria-label="Search"
              />
            </form>

            <div className="ml-auto flex items-center gap-1.5">
              <span className="hidden items-center gap-2 rounded-lg border border-white/10 bg-navy-900/70 px-3 py-1.5 md:flex">
                <Gauge size={13} className={health ? 'text-safe' : 'text-warn'} />
                <span className="text-xs text-slate-400">
                  API {health ? 'online' : 'checking'}
                </span>
              </span>

              {/* Notifications */}
              <div className="relative" ref={notificationsRef}>
                <button
                  type="button"
                  onClick={() => setNotificationsOpen((open) => !open)}
                  className="relative rounded-lg p-2 text-slate-400 transition-colors hover:bg-white/5 hover:text-slate-100"
                  aria-label={`Notifications (${notifications.length} new alerts)`}
                >
                  <Bell size={18} />
                  {notifications.length > 0 && (
                    <span className="absolute right-1 top-1 flex h-4 min-w-[1rem] items-center justify-center rounded-full bg-danger px-1 text-[0.6rem] font-semibold text-white">
                      {notifications.length}
                    </span>
                  )}
                </button>
                {notificationsOpen && (
                  <div className="absolute right-0 mt-2 w-[min(22rem,calc(100vw-2rem))] animate-fade-in overflow-hidden rounded-xl border border-white/10 bg-navy-900 shadow-panel">
                    <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
                      <p className="text-sm font-semibold text-slate-100">New alerts</p>
                      <span className="text-xs text-slate-500">{notifications.length} unread</span>
                    </div>
                    <div className="max-h-80 overflow-y-auto">
                      {notifications.length === 0 ? (
                        <p className="px-4 py-6 text-center text-sm text-slate-500">
                          No unacknowledged alerts.
                        </p>
                      ) : (
                        notifications.map((alert) => (
                          <button
                            key={alert.id}
                            type="button"
                            onClick={() => navigate(`/alerts?focus=${alert.id}`)}
                            className="flex w-full items-start gap-3 border-b border-white/[0.06] px-4 py-3 text-left transition-colors hover:bg-white/5"
                          >
                            <span
                              className={`badge mt-0.5 shrink-0 ${
                                SEVERITY_BADGE[alert.severity] || SEVERITY_BADGE.LOW
                              }`}
                            >
                              {alert.severity}
                            </span>
                            <span className="min-w-0 flex-1">
                              <span className="block truncate text-sm text-slate-200">
                                {alert.threat_type}
                              </span>
                              <span className="mono block truncate text-xs text-slate-500">
                                {alert.source_ip} - {timeAgo(alert.created_at)}
                              </span>
                            </span>
                          </button>
                        ))
                      )}
                    </div>
                    <button
                      type="button"
                      onClick={() => navigate('/alerts')}
                      className="w-full border-t border-white/10 px-4 py-2.5 text-xs font-medium text-accent transition-colors hover:bg-accent/5"
                    >
                      View all alerts
                    </button>
                  </div>
                )}
              </div>

              {/* User menu */}
              <div className="relative" ref={menuRef}>
                <button
                  type="button"
                  onClick={() => setMenuOpen((open) => !open)}
                  className="flex items-center gap-2 rounded-lg px-1.5 py-1.5 transition-colors hover:bg-white/5"
                  aria-label="Account menu"
                  aria-expanded={menuOpen}
                >
                  <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/15 text-xs font-semibold text-accent">
                    {initials}
                  </span>
                  <span className="hidden text-left sm:block">
                    <span className="block text-xs font-medium leading-tight text-slate-200">
                      {user?.full_name}
                    </span>
                    <span className="block text-[0.65rem] leading-tight text-slate-500">
                      {titleCase(user?.role || '')}
                    </span>
                  </span>
                  <ChevronDown size={14} className="hidden text-slate-500 sm:block" />
                </button>
                {menuOpen && (
                  <div className="absolute right-0 mt-2 w-56 animate-fade-in overflow-hidden rounded-xl border border-white/10 bg-navy-900 shadow-panel">
                    <div className="border-b border-white/10 px-4 py-3">
                      <p className="truncate text-sm font-medium text-slate-100">{user?.full_name}</p>
                      <p className="truncate text-xs text-slate-500">{user?.email}</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => navigate('/settings')}
                      className="flex w-full items-center gap-2.5 px-4 py-2.5 text-sm text-slate-300 transition-colors hover:bg-white/5"
                    >
                      <UserIcon size={15} />
                      Profile &amp; settings
                    </button>
                    <button
                      type="button"
                      onClick={handleLogout}
                      className="flex w-full items-center gap-2.5 border-t border-white/10 px-4 py-2.5 text-sm text-danger transition-colors hover:bg-danger/10"
                    >
                      <LogOut size={15} />
                      Sign out
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </header>

        <main className="flex-1 px-4 py-6 sm:px-6 lg:px-8">
          <div className="mx-auto w-full max-w-[1600px] animate-fade-in">
            <Outlet />
          </div>
        </main>

        <footer className="border-t border-white/10 px-4 py-4 sm:px-6 lg:px-8">
          <p className="text-center text-xs text-slate-600">
            CyberGuard AI v1.0.0 - academic Software Engineering Lab prototype. All telemetry,
            indicators and detections shown here are simulated.
          </p>
        </footer>
      </div>
    </div>
  )
}
