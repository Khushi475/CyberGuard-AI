/** 404 page for unknown routes. */
import { Link } from 'react-router-dom'
import { Compass, Shield } from 'lucide-react'

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-4 text-center">
      <span className="rounded-2xl border border-accent/25 bg-accent/10 p-4 text-accent">
        <Shield size={32} />
      </span>
      <p className="mono mt-6 text-5xl font-bold tracking-tight text-slate-100">404</p>
      <h1 className="mt-2 text-lg font-semibold text-slate-200">This route does not exist</h1>
      <p className="mt-2 max-w-md text-sm text-slate-400">
        The page you requested is not part of the CyberGuard AI console. Use the link below to get
        back to the security overview.
      </p>
      <Link to="/dashboard" className="btn-primary mt-6">
        <Compass size={16} />
        Return to dashboard
      </Link>
    </div>
  )
}
