import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

export default function Dashboard() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getStatistics().then(setStats).catch(() => setStats(null)).finally(() => setLoading(false));
  }, []);

  const insurancePieData = stats ? [
    { name: 'Insured (Active)', value: stats.insured_active || 0 },
    { name: 'Expired', value: stats.insurance_expired || 0 },
    { name: 'No Insurance', value: Math.max(0, (stats.total_registered || 0) - (stats.total_insurance_records || 0)) },
  ] : [];

  const pieColors = ['#22c55e', '#f59e0b', '#ef4444'];

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Information <span>Integration</span> Dashboard</h1>
        <p className="page-subtitle">Federated query results from 5 independently designed data sources · Mediation Architecture (IIA-1)</p>
      </div>

      {loading ? (
        <div className="loading-center"><div className="spinner" /><span>Loading statistics from all sources…</span></div>
      ) : (
        <>
          {/* Stat Cards */}
          <div className="stat-cards">
            <div className="stat-card indigo">
              <div className="stat-icon indigo">⌖</div>
              <div className="stat-label">Total Captured</div>
              <div className="stat-value">{stats?.unique_plates_captured ?? '—'}</div>
              <div className="stat-sub">{stats?.total_vehicles_captured ?? 0} total events</div>
            </div>
            <div className="stat-card green">
              <div className="stat-icon green">✓</div>
              <div className="stat-label">Insured (Active)</div>
              <div className="stat-value">{stats?.insured_active ?? '—'}</div>
              <div className="stat-sub">Valid policies</div>
            </div>
            <div className="stat-card yellow">
              <div className="stat-icon yellow">⚠</div>
              <div className="stat-label">Expired Insurance</div>
              <div className="stat-value">{stats?.insurance_expired ?? '—'}</div>
              <div className="stat-sub">Expired policies</div>
            </div>
            <div className="stat-card red">
              <div className="stat-icon red">🚨</div>
              <div className="stat-label">Stolen</div>
              <div className="stat-value">{stats?.stolen_vehicles ?? '—'}</div>
              <div className="stat-sub">Active cases</div>
            </div>
            <div className="stat-card purple">
              <div className="stat-icon purple">⬛</div>
              <div className="stat-label">Scrapped</div>
              <div className="stat-value">{stats?.scrapped_vehicles ?? '—'}</div>
              <div className="stat-sub">Decommissioned</div>
            </div>
            <div className="stat-card blue">
              <div className="stat-icon blue">⚑</div>
              <div className="stat-label">Ministry Reports</div>
              <div className="stat-value">{stats?.total_reports ?? '—'}</div>
              <div className="stat-sub">{stats?.pending_reports ?? 0} pending</div>
            </div>
          </div>

          {/* Charts row */}
          <div className="grid-2" style={{ marginBottom: 24 }}>
            <div className="card">
              <div className="card-title">Insurance Status Distribution</div>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie data={insurancePieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={75} label={({ name, value }) => value > 0 ? `${name}: ${value}` : ''} labelLine={false}>
                    {insurancePieData.map((_, i) => <Cell key={i} fill={pieColors[i]} />)}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="card">
              <div className="card-title">Records per Data Source</div>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={[
                  { source: 'Capture', count: stats?.sources?.capture?.total ?? 0 },
                  { source: 'Insurance', count: stats?.sources?.insurance?.total ?? 0 },
                  { source: 'Registration', count: stats?.sources?.registration?.total ?? 0 },
                  { source: 'Theft', count: stats?.sources?.theft?.total ?? 0 },
                  { source: 'Ministry', count: stats?.sources?.ministry?.total ?? 0 },
                ]} margin={{ top: 5, right: 10, bottom: 5, left: -10 }}>
                  <XAxis dataKey="source" tick={{ fontSize: 11, fill: '#94a3b8' }} />
                  <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} />
                  <Tooltip contentStyle={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border)', borderRadius: 8 }} />
                  <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Quick links */}
          <div className="card-title" style={{ marginBottom: 12 }}>Quick Actions</div>
          <div className="grid-3">
            {[
              { to: '/scan', icon: '⌖', title: 'Scan Vehicle', desc: 'Upload image → ANPR → Integration', color: 'var(--color-primary)' },
              { to: '/search', icon: '⌕', title: 'Search by Plate', desc: 'Enter plate → Federated query → Unified view', color: 'var(--color-success)' },
              { to: '/sources', icon: '⬢', title: 'View Data Sources', desc: 'See all 5 independent schemas + mappings', color: 'var(--color-warning)' },
              { to: '/integration', icon: '⎈', title: 'Integration View', desc: 'GAV schema mapping + mediator diagram', color: 'var(--color-purple)' },
              { to: '/reports', icon: '⚑', title: 'Ministry Reports', desc: 'Transport dept violations log', color: 'var(--color-danger)' },
              { to: '/search?plate=TN05KL1122', icon: '⚡', title: 'Demo: Data Conflict', desc: 'Color conflict between capture & registration', color: 'var(--color-purple)' },
            ].map(item => (
              <Link key={item.to} to={item.to}>
                <div className="source-card" style={{ height: '100%', cursor: 'pointer' }}>
                  <div style={{ fontSize: 24, marginBottom: 10 }}>{item.icon}</div>
                  <div style={{ fontWeight: 700, marginBottom: 6, color: item.color }}>{item.title}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{item.desc}</div>
                </div>
              </Link>
            ))}
          </div>

          {/* IIA Architecture note */}
          <div style={{ marginTop: 24, padding: '16px 20px', background: 'var(--color-primary-glow)', border: '1px solid rgba(99,102,241,0.3)', borderRadius: 'var(--radius-md)', fontSize: 13, color: 'var(--text-secondary)' }}>
            <strong style={{ color: 'var(--color-primary)' }}>⎈ Architecture:</strong> Mediation / Federated Virtual Integration (IIA-1). Each query is decomposed into 5 sub-queries targeting independent SQLite databases. Sources use different attribute names for the same vehicle identifier: <code style={{ color: 'var(--color-primary)', fontSize: 11 }}>plate_number / registration_id / vehicle_reg_no / vehicle_identifier / vehicle_ref</code>. The Mediator applies GAV schema mapping (IIA-3) to unify results.
          </div>
        </>
      )}
    </div>
  );
}
