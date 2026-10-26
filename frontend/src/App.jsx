/** Route table and route protection. */
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { ToastProvider } from './context/ToastContext'
import DashboardLayout from './layouts/DashboardLayout'
import { LoadingState } from './components/ui'

import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import ThreatDetection from './pages/ThreatDetection'
import Alerts from './pages/Alerts'
import Incidents from './pages/Incidents'
import IncidentDetails from './pages/IncidentDetails'
import ThreatIntelligence from './pages/ThreatIntelligence'
import LogAnalyzer from './pages/LogAnalyzer'
import Assets from './pages/Assets'
import Reports from './pages/Reports'
import Settings from './pages/Settings'
import NotFound from './pages/NotFound'

/** Blocks unauthenticated access and remembers where the user was heading. */
function ProtectedRoute({ children }) {
  const { isAuthenticated, checking } = useAuth()
  const location = useLocation()

  if (checking) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingState label="Restoring your session..." />
      </div>
    )
  }
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />
  }
  return children
}

function PublicOnlyRoute({ children }) {
  const { isAuthenticated, checking } = useAuth()
  if (checking) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingState label="Checking session..." />
      </div>
    )
  }
  return isAuthenticated ? <Navigate to="/dashboard" replace /> : children
}

function AppRoutes() {
  return (
    <Routes>
      <Route
        path="/login"
        element={
          <PublicOnlyRoute>
            <Login />
          </PublicOnlyRoute>
        }
      />
      <Route
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/detection" element={<ThreatDetection />} />
        <Route path="/alerts" element={<Alerts />} />
        <Route path="/incidents" element={<Incidents />} />
        <Route path="/incidents/:id" element={<IncidentDetails />} />
        <Route path="/threat-intelligence" element={<ThreatIntelligence />} />
        <Route path="/log-analyzer" element={<LogAnalyzer />} />
        <Route path="/assets" element={<Assets />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/settings" element={<Settings />} />
      </Route>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}

export default function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </ToastProvider>
  )
}
