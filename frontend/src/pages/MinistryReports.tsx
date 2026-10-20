import { useEffect, useState } from 'react';
import { api } from '../api';
import StatusBadge from '../components/StatusBadge';

const REPORT_TYPES = ['UNINSURED_VEHICLE', 'EXPIRED_INSURANCE', 'STOLEN_VEHICLE', 'SUSPICIOUS_VEHICLE', 'REGISTRATION_MISMATCH'];

export default function MinistryReports() {
  const [reports, setReports] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ vehicle_ref: '', report_type: REPORT_TYPES[0], reason: '', severity: 'HIGH', submitted_by: 'OFFICER' });
  const [submitting, setSubmitting] = useState(false);
  const [toast, setToast] = useState('');

  const load = () => {
    setLoading(true);
    Promise.all([api.getAllReports(), api.getReportStats()])
      .then(([r, s]) => { setReports(r.reports || []); setStats(s); })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleSubmit = async () => {
    if (!form.vehicle_ref || !form.reason) return;
    setSubmitting(true);
    try {
      await api.createReport(form);
      setToast('Report filed successfully!');
      setShowForm(false);
      setForm({ ...form, vehicle_ref: '', reason: '' });
      setTimeout(() => setToast(''), 3000);
      load();
    } catch (e) {
      setToast('Error filing report.');
    } finally {
      setSubmitting(false);
    }
  };

  const severityColor: Record<string, string> = {
    CRITICAL: 'var(--color-danger)', HIGH: 'var(--color-warning)',
    MEDIUM: 'var(--color-info)', LOW: 'var(--color-success)',
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Ministry of <span>Transportation</span> Reports</h1>
        <p className="page-subtitle">Simulated academic reporting system for vehicle violations · ministry.db → vehicle_ref</p>
      </div>

      {/* Stats */}
      <div className="stat-cards" style={{ marginBottom: 20 }}>
        <div className="stat-card blue">
          <div className="stat-icon blue">⚑</div>
          <div className="stat-label">Total Reports</div>
          <div className="stat-value">{stats?.total ?? '—'}</div>
        </div>
        <div className="stat-card yellow">
          <div className="stat-icon yellow">⏳</div>
          <div className="stat-label">Pending</div>
          <div className="stat-value">{stats?.pending ?? '—'}</div>
        </div>
        <div className="stat-card green">
          <div className="stat-icon green">✓</div>
          <div className="stat-label">Resolved</div>
          <div className="stat-value">{stats?.resolved ?? '—'}</div>
        </div>
        <div className="stat-card red">
          <div className="stat-icon red">✗</div>
          <div className="stat-label">Uninsured</div>
          <div className="stat-value">{stats?.uninsured_reports ?? '—'}</div>
        </div>
        <div className="stat-card yellow">
          <div className="stat-icon yellow">⚠</div>
          <div className="stat-label">Expired</div>
          <div className="stat-value">{stats?.expired_reports ?? '—'}</div>
        </div>
        <div className="stat-card red">
          <div className="stat-icon red">🚨</div>
          <div className="stat-label">Stolen</div>
          <div className="stat-value">{stats?.stolen_reports ?? '—'}</div>
        </div>
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
          {reports.length} total reports
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn btn-secondary btn-sm" onClick={load}>↻ Refresh</button>
          <button className="btn btn-primary btn-sm" onClick={() => setShowForm(!showForm)}>
            {showForm ? '✕ Cancel' : '+ File New Report'}
          </button>
        </div>
      </div>

      {/* New report form */}
      {showForm && (
        <div className="card" style={{ marginBottom: 20, border: '1px solid rgba(99,102,241,0.3)' }}>
          <div className="card-title" style={{ marginBottom: 14 }}>File Ministry Report (Simulated Academic System)</div>
          <div className="grid-2" style={{ marginBottom: 14 }}>
            <div className="input-group">
              <div className="input-label">Vehicle Registration</div>
              <input className="input" placeholder="e.g. UP32AB1234" value={form.vehicle_ref}
                onChange={e => setForm({ ...form, vehicle_ref: e.target.value.toUpperCase() })} />
            </div>
            <div className="input-group">
              <div className="input-label">Report Type</div>
              <select className="input" value={form.report_type} onChange={e => setForm({ ...form, report_type: e.target.value })}>
                {REPORT_TYPES.map(t => <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>)}
              </select>
            </div>
            <div className="input-group">
              <div className="input-label">Severity</div>
              <select className="input" value={form.severity} onChange={e => setForm({ ...form, severity: e.target.value })}>
                {['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div className="input-group">
              <div className="input-label">Submitted By</div>
              <input className="input" value={form.submitted_by} onChange={e => setForm({ ...form, submitted_by: e.target.value })} />
            </div>
          </div>
          <div className="input-group" style={{ marginBottom: 14 }}>
            <div className="input-label">Reason</div>
            <textarea className="input" rows={3} placeholder="Describe the violation…" value={form.reason}
              onChange={e => setForm({ ...form, reason: e.target.value })} />
          </div>
          <button className="btn btn-primary" onClick={handleSubmit} disabled={submitting}>
            {submitting ? '⏳ Submitting…' : '⚑ Submit Report'}
          </button>
        </div>
      )}

      {/* Reports Table */}
      {loading ? (
        <div className="loading-center"><div className="spinner" /></div>
      ) : reports.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">⚑</div>
          <h3>No Reports Yet</h3>
          <p>File a report for an uninsured or suspicious vehicle.</p>
        </div>
      ) : (
        <div className="table-wrapper">
          <table className="table">
            <thead>
              <tr>
                <th>#</th>
                <th>Vehicle Ref</th>
                <th>Report Type</th>
                <th>Date</th>
                <th>Severity</th>
                <th>Status</th>
                <th>Submitted By</th>
                <th>Action Taken</th>
              </tr>
            </thead>
            <tbody>
              {reports.map((r: any) => (
                <tr key={r.report_id}>
                  <td style={{ color: 'var(--text-muted)', fontSize: 12 }}>{r.report_id}</td>
                  <td><span className="mono">{r.vehicle_ref}</span></td>
                  <td><span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)' }}>{r.report_type?.replace(/_/g, ' ')}</span></td>
                  <td style={{ fontSize: 12 }}>{r.report_date?.split('T')[0]}</td>
                  <td>
                    <span style={{ fontSize: 11, fontWeight: 700, color: severityColor[r.severity] || 'var(--text-muted)', background: `${severityColor[r.severity] || '#666'}18`, padding: '2px 8px', borderRadius: 100, border: `1px solid ${severityColor[r.severity] || '#666'}33` }}>
                      {r.severity}
                    </span>
                  </td>
                  <td><StatusBadge status={r.report_status} /></td>
                  <td style={{ fontSize: 12 }}>{r.submitted_by || '—'}</td>
                  <td style={{ fontSize: 12, color: 'var(--text-muted)' }}>{r.action_taken || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Toast */}
      {toast && (
        <div className="toast">
          <span>✓</span>
          <span>{toast}</span>
        </div>
      )}
    </div>
  );
}
