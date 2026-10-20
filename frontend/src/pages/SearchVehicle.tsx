import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../api';
import UnifiedVehicleView from '../components/UnifiedVehicleView';

const DEMO_VEHICLES = [
  { plate: 'UP32AB1234', label: 'Insured', color: 'var(--color-success)' },
  { plate: 'UP32CD5678', label: 'Expired', color: 'var(--color-warning)' },
  { plate: 'MH02EF9012', label: 'Uninsured', color: 'var(--color-danger)' },
  { plate: 'DL01GH3456', label: 'Stolen', color: 'var(--color-danger)' },
  { plate: 'KA03IJ7890', label: 'Scrapped', color: '#9ca3af' },
  { plate: 'TN05KL1122', label: 'Conflict', color: 'var(--color-purple)' },
  { plate: 'GJ06MN3344', label: 'Partial', color: 'var(--color-info)' },
  { plate: 'HR26PQ7788', label: 'Suspicious', color: 'var(--color-warning)' },
];

export default function SearchVehicle() {
  const [searchParams] = useSearchParams();
  const [input, setInput] = useState(searchParams.get('plate') || '');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');

  const handleSearch = async (plateOverride?: string) => {
    const plate = plateOverride || input;
    if (!plate.trim()) return;
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const data = await api.getVehicle(plate.trim());
      setResult(data);
    } catch (e: any) {
      setError('Failed to query data sources. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const plate = searchParams.get('plate');
    if (plate) { setInput(plate); handleSearch(plate); }
  }, []);

  const createReport = async () => {
    if (!result) return;
    const statusToReportType: Record<string, string> = {
      UNINSURED: 'UNINSURED_VEHICLE',
      INSURANCE_EXPIRED: 'EXPIRED_INSURANCE',
      STOLEN: 'STOLEN_VEHICLE',
      SUSPICIOUS: 'SUSPICIOUS_VEHICLE',
      DATA_CONFLICT: 'REGISTRATION_MISMATCH',
    };
    const reportType = statusToReportType[result.overall_status];
    if (!reportType) return;
    await api.createReport({
      vehicle_ref: result.registration_number,
      report_type: reportType,
      reason: `Vehicle ${result.registration_number} detected with status: ${result.overall_status}`,
      severity: ['STOLEN', 'UNINSURED'].includes(result.overall_status) ? 'HIGH' : 'MEDIUM',
      submitted_by: 'OFFICER_UI',
    });
    alert('Ministry report created successfully!');
    // Refresh
    handleSearch(result.registration_number);
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Search <span>Vehicle</span></h1>
        <p className="page-subtitle">Enter a registration number to query all 5 data sources via the Information Integration Mediator</p>
      </div>

      {/* Search Bar */}
      <div style={{ marginBottom: 24 }}>
        <div className="search-bar" style={{ maxWidth: 600 }}>
          <input
            className="search-input"
            placeholder="Enter plate number (e.g. UP32AB1234)"
            value={input}
            onChange={e => setInput(e.target.value.toUpperCase())}
            onKeyDown={e => e.key === 'Enter' && handleSearch()}
          />
          <button className="search-btn" onClick={() => handleSearch()} disabled={loading}>
            {loading ? '⏳' : '⌕'} {loading ? 'Searching…' : 'Search'}
          </button>
        </div>

        {/* Demo chips */}
        <div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 12, marginBottom: 8 }}>Demo vehicles:</div>
          <div className="demo-chips">
            {DEMO_VEHICLES.map(v => (
              <button key={v.plate} className="demo-chip"
                style={{ borderColor: v.color, color: v.color }}
                onClick={() => { setInput(v.plate); handleSearch(v.plate); }}>
                {v.plate} <span style={{ opacity: 0.7, fontSize: 10 }}>· {v.label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div style={{ background: 'var(--color-danger-dim)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 12, padding: '14px 18px', marginBottom: 20, color: 'var(--color-danger)' }}>
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="loading-center">
          <div className="spinner" />
          <div>
            <div style={{ fontWeight: 600, marginBottom: 4 }}>Querying 5 independent data sources…</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>capture.db → insurance.db → registration.db → theft.db → ministry.db</div>
          </div>
        </div>
      )}

      {/* Results */}
      {result && !loading && (
        <>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16, gap: 10 }}>
            {result.requires_ministry_report && (
              <button className="btn btn-danger" onClick={createReport}>
                ⚑ File Ministry Report
              </button>
            )}
            <button className="btn btn-secondary" onClick={() => handleSearch()}>
              ↻ Refresh
            </button>
          </div>
          <UnifiedVehicleView data={result} />
        </>
      )}
    </div>
  );
}
