import { useEffect, useState } from 'react';
import { api } from '../api';
import StatusBadge from '../components/StatusBadge';

export default function DataSources() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<string>('capture');

  useEffect(() => {
    api.getDataSources().then(setData).catch(() => setData(null)).finally(() => setLoading(false));
  }, []);

  const sources = data?.sources || [];
  const selectedSource = sources.find((s: any) => s.source === selected);

  const sourceColors: Record<string, string> = {
    capture:      'var(--color-primary)',
    insurance:    'var(--color-success)',
    registration: 'var(--color-warning)',
    theft:        'var(--color-danger)',
    ministry:     'var(--color-purple)',
  };

  const commonKeyMapping: Record<string, { localKey: string; globalKey: string; color: string }> = {
    capture:      { localKey: 'plate_number',       globalKey: 'registration_number', color: 'var(--color-primary)' },
    insurance:    { localKey: 'registration_id',    globalKey: 'registration_number', color: 'var(--color-success)' },
    registration: { localKey: 'vehicle_reg_no',     globalKey: 'registration_number', color: 'var(--color-warning)' },
    theft:        { localKey: 'vehicle_identifier', globalKey: 'registration_number', color: 'var(--color-danger)' },
    ministry:     { localKey: 'vehicle_ref',        globalKey: 'registration_number', color: 'var(--color-purple)' },
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Data <span>Sources</span></h1>
        <p className="page-subtitle">5 independently designed databases — each with its own schema and local attribute names</p>
      </div>

      {/* Key Insight Banner */}
      <div style={{ background: 'var(--color-primary-glow)', border: '1px solid rgba(99,102,241,0.35)', borderRadius: 'var(--radius-lg)', padding: '18px 22px', marginBottom: 24 }}>
        <div style={{ fontWeight: 700, color: 'var(--color-primary)', marginBottom: 10 }}>
          ⎈ Schema Heterogeneity — Core Information Integration Problem
        </div>
        <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 14 }}>
          All 5 databases share the same underlying vehicle value (the registration number), but each uses a <strong>different attribute name</strong> because they were designed independently by different organizations.
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {Object.entries(commonKeyMapping).map(([src, info]) => (
            <div key={src} style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '6px 12px', background: 'var(--color-surface)', borderRadius: 100, border: `1px solid ${info.color}33` }}>
              <code style={{ color: info.color, fontSize: 12, fontFamily: 'JetBrains Mono, monospace' }}>{info.localKey}</code>
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>({src})</span>
            </div>
          ))}
        </div>
        <div style={{ marginTop: 10, fontSize: 12, color: 'var(--text-muted)' }}>
          All map to global attribute: <code style={{ color: 'var(--color-success)', fontSize: 13 }}>registration_number</code> via GAV schema mapping (IIA-3)
        </div>
      </div>

      {loading ? (
        <div className="loading-center"><div className="spinner" /></div>
      ) : (
        <div style={{ display: 'flex', gap: 20 }}>
          {/* Source tabs */}
          <div style={{ width: 200, flexShrink: 0 }}>
            {sources.map((s: any) => (
              <div key={s.source}
                onClick={() => setSelected(s.source)}
                style={{
                  padding: '12px 16px', borderRadius: 'var(--radius-md)', marginBottom: 6,
                  cursor: 'pointer', border: '1px solid var(--color-border)',
                  background: selected === s.source ? `${(sourceColors[s.source] || '#6366f1')}22` : 'var(--color-surface)',
                  borderColor: selected === s.source ? sourceColors[s.source] || 'var(--color-primary)' : 'var(--color-border)',
                  transition: 'all 0.2s',
                }}>
                <div style={{ fontWeight: 700, fontSize: 13, color: selected === s.source ? sourceColors[s.source] : 'var(--text-primary)' }}>
                  {s.source}.db
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{s.organization?.split(' ')[0] || ''}</div>
              </div>
            ))}
          </div>

          {/* Source detail */}
          {selectedSource && (
            <div style={{ flex: 1, minWidth: 0 }}>
              <div className="card" style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                  <div>
                    <div style={{ fontSize: 18, fontWeight: 800, color: sourceColors[selectedSource.source] }}>
                      {selectedSource.source}.db
                    </div>
                    <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>{selectedSource.purpose}</div>
                  </div>
                  <div style={{ textAlign: 'right', fontSize: 11, color: 'var(--text-muted)' }}>
                    <div>Organization</div>
                    <div style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>{selectedSource.organization}</div>
                  </div>
                </div>

                {/* Common key mapping highlight */}
                <div style={{ background: 'var(--color-surface-2)', borderRadius: 8, padding: '10px 14px', marginBottom: 12, border: `1px solid ${sourceColors[selectedSource.source]}33` }}>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>VEHICLE IDENTIFIER (local → global)</div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <code style={{ color: sourceColors[selectedSource.source], fontSize: 14, fontFamily: 'JetBrains Mono, monospace', fontWeight: 700 }}>
                      {commonKeyMapping[selectedSource.source]?.localKey}
                    </code>
                    <span style={{ color: 'var(--text-muted)' }}>↔</span>
                    <code style={{ color: 'var(--color-success)', fontSize: 14, fontFamily: 'JetBrains Mono, monospace', fontWeight: 700 }}>
                      {commonKeyMapping[selectedSource.source]?.globalKey}
                    </code>
                    <span style={{ fontSize: 11, color: 'var(--text-muted)', background: 'var(--color-primary-glow)', padding: '2px 8px', borderRadius: 100 }}>GAV mapping</span>
                  </div>
                </div>
              </div>

              {/* Schema tables */}
              {Object.entries(selectedSource.tables || {}).map(([tableName, tableInfo]: [string, any]) => (
                <div key={tableName} style={{ marginBottom: 16 }}>
                  <div style={{ fontWeight: 700, marginBottom: 8, display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{ fontFamily: 'JetBrains Mono, monospace', color: sourceColors[selectedSource.source] }}>{tableName}</span>
                    <span style={{ fontSize: 11, color: 'var(--text-muted)', background: 'var(--color-surface-2)', padding: '2px 8px', borderRadius: 100, border: '1px solid var(--color-border)' }}>
                      {tableInfo.record_count} records
                    </span>
                  </div>
                  <div className="table-wrapper">
                    <table className="table">
                      <thead>
                        <tr>
                          <th>Column Name</th>
                          <th>Data Type</th>
                          <th>Key</th>
                          <th>Global Mapping</th>
                        </tr>
                      </thead>
                      <tbody>
                        {tableInfo.columns?.map((col: any) => {
                          const isLocalKey = col.name === commonKeyMapping[selectedSource.source]?.localKey;
                          return (
                            <tr key={col.name}>
                              <td>
                                <code style={{
                                  color: isLocalKey ? sourceColors[selectedSource.source] : 'var(--text-primary)',
                                  fontWeight: isLocalKey ? 700 : 400,
                                  fontFamily: 'JetBrains Mono, monospace', fontSize: 12
                                }}>
                                  {col.name}
                                </code>
                                {isLocalKey && <span style={{ marginLeft: 6, fontSize: 10, color: sourceColors[selectedSource.source], background: `${sourceColors[selectedSource.source]}22`, padding: '1px 6px', borderRadius: 100 }}>identity key</span>}
                              </td>
                              <td style={{ color: 'var(--text-muted)', fontSize: 12 }}>{col.type || 'TEXT'}</td>
                              <td>{col.pk && <StatusBadge status="ACTIVE" />}</td>
                              <td>
                                {isLocalKey ? (
                                  <code style={{ color: 'var(--color-success)', fontSize: 11, fontFamily: 'JetBrains Mono, monospace' }}>registration_number</code>
                                ) : (
                                  <span style={{ color: 'var(--text-muted)', fontSize: 11 }}>—</span>
                                )}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
