/** Assets page (FR-08) - the monitored inventory with full CRUD. */
import { useEffect, useMemo, useState } from 'react'
import { Edit3, Plus, RefreshCw, Server, Trash2 } from 'lucide-react'
import { useApi, useDebounced } from '../hooks/useApi'
import api from '../services/api'
import { useToast } from '../context/ToastContext'
import {
  ConfirmDialog,
  EmptyState,
  ErrorState,
  Field,
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
import { formatNumber, timeAgo } from '../utils/format'

const ASSET_TYPES = [
  'Web Server',
  'Database Server',
  'Application Server',
  'Network Gateway',
  'Workstation',
  'Laptop',
  'Firewall',
  'Domain Controller',
  'Mail Server',
  'IoT Device',
]

const STATUSES = ['ONLINE', 'OFFLINE', 'MAINTENANCE', 'QUARANTINED']
const CRITICALITIES = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']

const EMPTY_ASSET = {
  name: '',
  ip_address: '',
  asset_type: 'Workstation',
  operating_system: '',
  location: '',
  owner: '',
  criticality: 'MEDIUM',
  status: 'ONLINE',
}

function AssetFormModal({ open, onClose, asset, onSaved }) {
  const toast = useToast()
  const [form, setForm] = useState(EMPTY_ASSET)
  const [errors, setErrors] = useState({})
  const [busy, setBusy] = useState(false)
  const editing = Boolean(asset)

  useEffect(() => {
    if (open) {
      setForm(asset ? { ...EMPTY_ASSET, ...asset } : EMPTY_ASSET)
      setErrors({})
    }
  }, [open, asset])

  const setField = (name, value) => {
    setForm((current) => ({ ...current, [name]: value }))
    setErrors((current) => {
      if (!current[name]) return current
      const next = { ...current }
      delete next[name]
      return next
    })
  }

  const submit = async (event) => {
    event?.preventDefault()
    const found = {}
    if (!form.name.trim()) found.name = 'Asset name is required.'
    if (!form.ip_address.trim()) found.ip_address = 'IP address is required.'
    else if (!/^(\d{1,3}\.){3}\d{1,3}$|^[0-9a-fA-F:]+$/.test(form.ip_address.trim()))
      found.ip_address = 'Enter a valid IPv4 or IPv6 address.'
    setErrors(found)
    if (Object.keys(found).length) return

    setBusy(true)
    try {
      const payload = {
        name: form.name,
        ip_address: form.ip_address,
        asset_type: form.asset_type,
        operating_system: form.operating_system,
        location: form.location,
        owner: form.owner,
        criticality: form.criticality,
        status: form.status,
      }
      if (editing) await api.updateAsset(asset.id, payload)
      else await api.createAsset(payload)
      toast.success(`Asset '${form.name}' ${editing ? 'updated' : 'created'}.`)
      onSaved()
      onClose()
    } catch (caught) {
      toast.error(caught.message)
      if (caught.details?.field) setErrors({ [caught.details.field]: caught.message })
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={editing ? `Edit ${asset?.name}` : 'Register a monitored asset'}
      description="Events whose source or destination matches this IP address are automatically linked to the asset."
      footer={
        <>
          <button type="button" className="btn-secondary" onClick={onClose} disabled={busy}>
            Cancel
          </button>
          <button type="button" className="btn-primary" onClick={submit} disabled={busy}>
            {busy && <Spinner size={15} />}
            {editing ? 'Save changes' : 'Create asset'}
          </button>
        </>
      }
    >
      <form onSubmit={submit} className="grid gap-3 sm:grid-cols-2" noValidate>
        <Field label="Asset name" error={errors.name} required>
          <input
            type="text"
            value={form.name}
            onChange={(event) => setField('name', event.target.value)}
            placeholder="Primary Web Server"
            className={`field-input ${errors.name ? 'field-input-error' : ''}`}
          />
        </Field>
        <Field label="IP address" error={errors.ip_address} required>
          <input
            type="text"
            value={form.ip_address}
            onChange={(event) => setField('ip_address', event.target.value)}
            placeholder="10.0.3.10"
            className={`field-input mono ${errors.ip_address ? 'field-input-error' : ''}`}
          />
        </Field>
        <Select
          label="Asset type"
          value={form.asset_type}
          onChange={(value) => setField('asset_type', value)}
          options={ASSET_TYPES.map((type) => ({ value: type, label: type }))}
        />
        <Field label="Operating system">
          <input
            type="text"
            value={form.operating_system || ''}
            onChange={(event) => setField('operating_system', event.target.value)}
            placeholder="Ubuntu Server 22.04 LTS"
            className="field-input"
          />
        </Field>
        <Field label="Location">
          <input
            type="text"
            value={form.location || ''}
            onChange={(event) => setField('location', event.target.value)}
            placeholder="Data Centre A"
            className="field-input"
          />
        </Field>
        <Field label="Owner / team">
          <input
            type="text"
            value={form.owner || ''}
            onChange={(event) => setField('owner', event.target.value)}
            placeholder="Platform Team"
            className="field-input"
          />
        </Field>
        <Select
          label="Business criticality"
          value={form.criticality}
          onChange={(value) => setField('criticality', value)}
          options={CRITICALITIES}
        />
        <Select
          label="Operational status"
          value={form.status}
          onChange={(value) => setField('status', value)}
          options={STATUSES}
        />
      </form>
    </Modal>
  )
}

export default function Assets() {
  const toast = useToast()
  const [page, setPage] = useState(1)
  const [status, setStatus] = useState('ALL')
  const [riskLevel, setRiskLevel] = useState('ALL')
  const [assetType, setAssetType] = useState('all')
  const [search, setSearch] = useState('')
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState(null)
  const [deleting, setDeleting] = useState(null)
  const [busy, setBusy] = useState(false)

  const debouncedSearch = useDebounced(search, 400)

  const params = useMemo(
    () => ({
      page,
      per_page: 25,
      status,
      risk_level: riskLevel,
      asset_type: assetType,
      search: debouncedSearch || undefined,
    }),
    [page, status, riskLevel, assetType, debouncedSearch],
  )

  const { data, error, loading, refresh } = useApi(() => api.listAssets(params), [params])

  useEffect(() => {
    setPage(1)
  }, [status, riskLevel, assetType, debouncedSearch])

  const assets = data?.data || []

  const summary = useMemo(() => {
    const total = data?.pagination?.total || 0
    const online = assets.filter((asset) => asset.status === 'ONLINE').length
    const atRisk = assets.filter((asset) => ['HIGH', 'CRITICAL'].includes(asset.risk_level)).length
    const quarantined = assets.filter((asset) => asset.status === 'QUARANTINED').length
    return { total, online, atRisk, quarantined }
  }, [assets, data])

  const confirmDelete = async () => {
    setBusy(true)
    try {
      await api.deleteAsset(deleting.id)
      toast.success(`Asset '${deleting.name}' removed from monitoring.`)
      setDeleting(null)
      refresh({ quiet: true })
    } catch (caught) {
      toast.error(caught.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <PageHeader
        title="Monitored Assets"
        description="The inventory the detection engine protects. An asset's risk level rises with the highest-risk event observed on it."
        icon={Server}
      >
        <button
          type="button"
          onClick={() => {
            setEditing(null)
            setFormOpen(true)
          }}
          className="btn-primary btn-sm"
        >
          <Plus size={14} />
          Add asset
        </button>
        <button type="button" onClick={() => refresh()} className="btn-secondary btn-sm" disabled={loading}>
          {loading ? <Spinner size={14} /> : <RefreshCw size={14} />}
          Refresh
        </button>
      </PageHeader>

      <div className="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { label: 'Total assets', value: summary.total, tone: 'text-accent' },
          { label: 'Online (this page)', value: summary.online, tone: 'text-safe' },
          { label: 'High / critical risk', value: summary.atRisk, tone: 'text-rose-300' },
          { label: 'Quarantined', value: summary.quarantined, tone: 'text-warn' },
        ].map((tile) => (
          <div key={tile.label} className="panel p-4">
            <p className="text-[0.62rem] uppercase tracking-wider text-slate-500">{tile.label}</p>
            <p className={`mt-1 text-2xl font-semibold tracking-tight ${tile.tone}`}>
              {formatNumber(tile.value)}
            </p>
          </div>
        ))}
      </div>

      <Panel bodyClassName="p-0">
        <div className="grid gap-3 border-b border-white/10 p-4 sm:grid-cols-2 lg:grid-cols-4">
          <SearchInput
            value={search}
            onChange={setSearch}
            placeholder="Search by name, IP or OS..."
          />
          <Select
            value={assetType}
            onChange={setAssetType}
            options={[
              { value: 'all', label: 'All asset types' },
              ...ASSET_TYPES.map((type) => ({ value: type, label: type })),
            ]}
          />
          <Select
            value={status}
            onChange={setStatus}
            options={[{ value: 'ALL', label: 'All statuses' }, ...STATUSES]}
          />
          <Select
            value={riskLevel}
            onChange={setRiskLevel}
            options={[{ value: 'ALL', label: 'All risk levels' }, ...CRITICALITIES]}
          />
        </div>

        {loading && !data ? (
          <SkeletonTable rows={8} columns={8} />
        ) : error ? (
          <ErrorState error={error} onRetry={refresh} />
        ) : assets.length === 0 ? (
          <EmptyState
            icon={Server}
            title="No assets match these filters"
            message="Register the servers, workstations and network devices you want CyberGuard AI to monitor."
            action={
              <button
                type="button"
                onClick={() => {
                  setEditing(null)
                  setFormOpen(true)
                }}
                className="btn-primary btn-sm"
              >
                <Plus size={14} />
                Add asset
              </button>
            }
          />
        ) : (
          <>
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Asset name</th>
                    <th>IP address</th>
                    <th>Type</th>
                    <th>Operating system</th>
                    <th>Status</th>
                    <th>Risk level</th>
                    <th>Events</th>
                    <th>Last seen</th>
                    <th className="text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {assets.map((asset) => (
                    <tr key={asset.id}>
                      <td>
                        <p className="text-slate-200">{asset.name}</p>
                        <p className="text-[0.66rem] text-slate-500">
                          {asset.location || 'No location'} - {asset.owner || 'Unassigned'}
                        </p>
                      </td>
                      <td className="mono text-xs">{asset.ip_address}</td>
                      <td className="whitespace-nowrap text-xs text-slate-400">{asset.asset_type}</td>
                      <td className="max-w-[12rem] truncate text-xs text-slate-400">
                        {asset.operating_system || '-'}
                      </td>
                      <td>
                        <StatusBadge status={asset.status} />
                      </td>
                      <td>
                        <div className="flex items-center gap-2">
                          <SeverityBadge severity={asset.risk_level} />
                          <RiskBar score={asset.risk_score} showValue={false} className="w-16" />
                        </div>
                      </td>
                      <td className="mono text-xs">{formatNumber(asset.event_count || 0)}</td>
                      <td className="whitespace-nowrap text-xs text-slate-500">
                        {timeAgo(asset.last_seen)}
                      </td>
                      <td>
                        <div className="flex items-center justify-end gap-1">
                          <button
                            type="button"
                            onClick={() => {
                              setEditing(asset)
                              setFormOpen(true)
                            }}
                            className="btn-ghost btn-sm"
                            title="Edit asset"
                          >
                            <Edit3 size={14} />
                          </button>
                          <button
                            type="button"
                            onClick={() => setDeleting(asset)}
                            className="btn-ghost btn-sm text-danger"
                            title="Remove asset"
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
            <Pagination pagination={data?.pagination} onPageChange={setPage} />
          </>
        )}
      </Panel>

      <AssetFormModal
        open={formOpen}
        onClose={() => setFormOpen(false)}
        asset={editing}
        onSaved={() => refresh({ quiet: true })}
      />

      <ConfirmDialog
        open={Boolean(deleting)}
        onClose={() => setDeleting(null)}
        onConfirm={confirmDelete}
        title={`Remove '${deleting?.name}'?`}
        message="The asset is removed from the monitored inventory. Its historical security events are kept but will no longer be linked to an asset."
        confirmLabel="Remove asset"
        busy={busy}
      />
    </>
  )
}
