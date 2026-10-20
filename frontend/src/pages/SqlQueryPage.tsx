import { useState, useEffect } from 'react';
import { api } from '../api';

const DB_OPTIONS = [
  { value: 'all',          label: '🌐 All Databases',        color: '#a78bfa' },
  { value: 'capture',      label: '📷 Capture DB',            color: '#38bdf8' },
  { value: 'insurance',    label: '🛡️ Insurance DB',          color: '#34d399' },
  { value: 'registration', label: '📋 Registration DB',       color: '#fbbf24' },
  { value: 'theft',        label: '🚨 Theft DB',              color: '#f87171' },
  { value: 'ministry',     label: '🏛️ Ministry DB',           color: '#c084fc' },
];

const EXAMPLE_QUERIES = [
  {
    label: 'All captures (global view)',
    db: 'capture',
    query: 'SELECT plate_number, detected_vehicle_type, detected_color, capture_location, capture_timestamp\nFROM vehicle_capture\nLIMIT 20',
  },
  {
    label: 'Active insurance policies',
    db: 'insurance',
    query: "SELECT registration_id, insurer_name, policy_number, policy_expiry_date, insurance_status\nFROM insurance_records\nWHERE insurance_status = 'ACTIVE'\nLIMIT 20",
  },
  {
    label: 'Registered vehicles',
    db: 'registration',
    query: 'SELECT vehicle_reg_no, owner_name, manufacturer, model_name, registered_color, registration_status\nFROM vehicle_registration\nLIMIT 20',
  },
  {
    label: 'Stolen vehicles',
    db: 'theft',
    query: "SELECT vehicle_identifier, case_type, case_status, reported_date, police_reference\nFROM vehicle_security_records\nWHERE case_type = 'STOLEN'\nLIMIT 20",
  },
  {
    label: 'Ministry reports',
    db: 'ministry',
    query: 'SELECT vehicle_ref, report_type, report_date, reason, severity, report_status\nFROM transport_reports\nORDER BY report_date DESC\nLIMIT 20',
  },
  {
    label: 'Cross-DB: plate lookup (global view)',
    db: 'all',
    query: "SELECT * FROM vehicle_capture WHERE plate_number = 'UP32AB1234'",
  },
];

interface ResultSet {
  database: string;
  columns: string[];
  rows: Record<string, unknown>[];
  row_count: number;
  error: string | null;
}

interface SchemaTable {
  name: string;
  type: string;
  pk: boolean;
}

interface SchemaDB {
  tables: Record<string, SchemaTable[]>;
  error?: string;
}

interface WriteResult {
  success: boolean;
  database: string;
  owner: string;
  affected_rows: number;
  last_insert_id: number | null;
  error?: string;
  forwarded_to?: string;
}

export default function SqlQueryPage() {
  const [query, setQuery] = useState(EXAMPLE_QUERIES[0].query);
  const [database, setDatabase] = useState('capture');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<ResultSet[] | null>(null);
  const [writeResult, setWriteResult] = useState<WriteResult | null>(null);
  const [totalRows, setTotalRows] = useState(0);
  const [error, setError] = useState('');
  const [schema, setSchema] = useState<Record<string, SchemaDB> | null>(null);
  const [schemaOpen, setSchemaOpen] = useState(false);
  const [writeMode, setWriteMode] = useState(false);
  const [ownership, setOwnership] = useState<Record<string, {owner: string, node: string, writable_here: boolean}> | null>(null);

  useEffect(() => {
    api.getSqlTables()
      .then(data => setSchema(data.databases))
      .catch(() => setSchema(null));
    api.getDbOwnership()
      .then(data => setOwnership(data.databases))
      .catch(() => setOwnership(null));
  }, []);

  const runQuery = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError('');
    setResults(null);
    setWriteResult(null);
    try {
      if (writeMode) {
        if (database === 'all') throw new Error("Please select a specific database for write operations.");
        const data = await api.sqlWrite(query, database);
        setWriteResult(data);
      } else {
        const data = await api.sqlQuery(query, database);
        setResults(data.results);
        const successfulRows = (data.results as ResultSet[])
          .filter(r => !r.error?.includes('no such table'))
          .reduce((sum: number, r: ResultSet) => sum + r.row_count, 0);
        setTotalRows(successfulRows);
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Query failed');
    } finally {
      setLoading(false);
    }
  };

  const loadExample = (ex: typeof EXAMPLE_QUERIES[0]) => {
    setQuery(ex.query);
    setDatabase(ex.db);
    setResults(null);
    setWriteResult(null);
    setError('');
    setWriteMode(false);
  };

  const dbColor = DB_OPTIONS.find(d => d.value === database)?.color ?? '#a78bfa';

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">SQL <span>Query</span></h1>
        <p className="page-subtitle">
          Run SELECT queries against any of the 5 independent databases — or all at once for a global view
        </p>
      </div>

      <div className="grid-2" style={{ gap: 24, marginBottom: 24 }}>
        {/* Left: Query Editor */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

          {/* Database selector */}
          <div style={{
            background: 'var(--color-surface)',
            border: '1px solid var(--color-border)',
            borderRadius: 14,
            padding: '16px 20px',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 600, letterSpacing: '0.05em' }}>
                SELECT DATABASE
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 12, color: writeMode ? 'var(--text-muted)' : '#38bdf8', fontWeight: writeMode ? 400 : 700 }}>READ</span>
                <button
                  onClick={() => {
                    const newMode = !writeMode;
                    setWriteMode(newMode);
                    if (newMode && database === 'all') setDatabase('capture');
                    setResults(null);
                    setWriteResult(null);
                  }}
                  style={{
                    width: 40, height: 20, borderRadius: 10, background: writeMode ? '#f87171' : 'var(--color-surface-3)',
                    border: 'none', position: 'relative', cursor: 'pointer', transition: 'background 0.2s'
                  }}
                >
                  <div style={{
                    width: 16, height: 16, borderRadius: '50%', background: 'white',
                    position: 'absolute', top: 2, left: writeMode ? 22 : 2, transition: 'left 0.2s'
                  }} />
                </button>
                <span style={{ fontSize: 12, color: writeMode ? '#f87171' : 'var(--text-muted)', fontWeight: writeMode ? 700 : 400 }}>WRITE</span>
              </div>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {DB_OPTIONS.map(opt => {
                if (writeMode && opt.value === 'all') return null;
                const dbOwner = ownership?.[opt.value];
                const isRemote = writeMode && dbOwner && !dbOwner.writable_here;
                
                return (
                  <button
                    key={opt.value}
                    onClick={() => setDatabase(opt.value)}
                    style={{
                      padding: '6px 14px',
                      borderRadius: 20,
                      border: database === opt.value
                        ? `2px solid ${opt.color}`
                        : '2px solid var(--color-border)',
                      background: database === opt.value
                        ? `${opt.color}22`
                        : 'var(--color-surface-2)',
                      color: database === opt.value ? opt.color : 'var(--text-muted)',
                      fontSize: 13,
                      fontWeight: database === opt.value ? 700 : 400,
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6
                    }}
                  >
                    {opt.label}
                    {isRemote && <span title={`Owned by ${dbOwner.owner}`}>🔒</span>}
                  </button>
                );
              })}
            </div>
            {writeMode && ownership?.[database] && !ownership[database].writable_here && (
              <div style={{ marginTop: 12, fontSize: 12, color: '#f87171', background: '#f8717122', padding: '8px 12px', borderRadius: 8 }}>
                ℹ️ <strong>Remote Database:</strong> This database belongs to <strong>{ownership[database].owner}</strong>. Writes will be federated over HTTP.
              </div>
            )}
            {writeMode && ownership?.[database] && ownership[database].writable_here && (
              <div style={{ marginTop: 12, fontSize: 12, color: '#34d399', background: '#34d39922', padding: '8px 12px', borderRadius: 8 }}>
                ✅ <strong>Local Database:</strong> This database is owned by this laptop.
              </div>
            )}
          </div>

          {/* SQL Editor */}
          <div style={{
            background: 'var(--color-surface)',
            border: `1px solid ${dbColor}44`,
            borderRadius: 14,
            overflow: 'hidden',
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '10px 16px',
              background: 'var(--color-surface-2)',
              borderBottom: `1px solid ${dbColor}33`,
            }}>
              <span style={{ fontSize: 12, fontWeight: 700, color: dbColor, letterSpacing: '0.05em' }}>
                SQL EDITOR — {database.toUpperCase()} DATABASE
              </span>
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{writeMode ? 'INSERT / UPDATE / DELETE' : 'SELECT only'}</span>
            </div>
            <textarea
              id="sql-query-input"
              value={query}
              onChange={e => setQuery(e.target.value)}
              spellCheck={false}
              style={{
                width: '100%',
                minHeight: 200,
                padding: '16px',
                background: '#0d1117',
                color: '#e6edf3',
                fontFamily: '"Fira Code", "Cascadia Code", "Courier New", monospace',
                fontSize: 13,
                lineHeight: 1.7,
                border: 'none',
                outline: 'none',
                resize: 'vertical',
                boxSizing: 'border-box',
              }}
              placeholder={writeMode ? "INSERT INTO vehicle_capture (plate_number) VALUES ('UP32AB1234')" : "SELECT * FROM vehicle_capture LIMIT 10"}
              onKeyDown={e => {
                // Ctrl+Enter / Cmd+Enter to run
                if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                  e.preventDefault();
                  runQuery();
                }
                // Tab inserts spaces
                if (e.key === 'Tab') {
                  e.preventDefault();
                  const start = e.currentTarget.selectionStart;
                  const end = e.currentTarget.selectionEnd;
                  const newVal = query.substring(0, start) + '    ' + query.substring(end);
                  setQuery(newVal);
                  setTimeout(() => {
                    e.currentTarget.selectionStart = start + 4;
                    e.currentTarget.selectionEnd = start + 4;
                  }, 0);
                }
              }}
            />
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '10px 16px',
              background: 'var(--color-surface-2)',
              borderTop: `1px solid ${dbColor}33`,
            }}>
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Ctrl+Enter to run</span>
              <button
                id="sql-run-btn"
                className="btn btn-primary"
                onClick={runQuery}
                disabled={loading}
                style={{ background: dbColor, border: 'none', minWidth: 120 }}
              >
                {loading ? 'Running…' : '▶ Run Query'}
              </button>
            </div>
          </div>
        </div>

        {/* Right: Examples + Schema helper */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Example queries */}
          <div style={{
            background: 'var(--color-surface)',
            border: '1px solid var(--color-border)',
            borderRadius: 14,
            padding: '16px 20px',
          }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '0.05em', marginBottom: 12 }}>
              EXAMPLE QUERIES
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {EXAMPLE_QUERIES.map((ex, i) => (
                <button
                  key={i}
                  onClick={() => loadExample(ex)}
                  style={{
                    textAlign: 'left',
                    padding: '8px 12px',
                    borderRadius: 8,
                    border: '1px solid var(--color-border)',
                    background: 'var(--color-surface-2)',
                    color: 'var(--text-secondary)',
                    fontSize: 12,
                    cursor: 'pointer',
                    transition: 'all 0.15s',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                  }}
                  onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.background = 'var(--color-surface-3)'; (e.currentTarget as HTMLButtonElement).style.color = 'var(--text-primary)'; }}
                  onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.background = 'var(--color-surface-2)'; (e.currentTarget as HTMLButtonElement).style.color = 'var(--text-secondary)'; }}
                >
                  <span style={{ color: DB_OPTIONS.find(d => d.value === ex.db)?.color, fontSize: 16 }}>
                    {DB_OPTIONS.find(d => d.value === ex.db)?.label.split(' ')[0]}
                  </span>
                  {ex.label}
                </button>
              ))}
            </div>
          </div>

          {/* Schema helper */}
          <div style={{
            background: 'var(--color-surface)',
            border: '1px solid var(--color-border)',
            borderRadius: 14,
            overflow: 'hidden',
          }}>
            <button
              onClick={() => setSchemaOpen(o => !o)}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '14px 20px',
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                color: 'var(--text-secondary)',
              }}
            >
              <span style={{ fontSize: 12, fontWeight: 700, letterSpacing: '0.05em' }}>📊 TABLE SCHEMAS</span>
              <span style={{ fontSize: 12, color: 'var(--text-muted)', transition: 'transform 0.2s', transform: schemaOpen ? 'rotate(180deg)' : 'none' }}>▾</span>
            </button>
            {schemaOpen && schema && (
              <div style={{ padding: '0 20px 16px', maxHeight: 400, overflowY: 'auto' }}>
                {Object.entries(schema).map(([dbName, dbInfo]) => {
                  const color = DB_OPTIONS.find(d => d.value === dbName)?.color ?? '#aaa';
                  return (
                    <div key={dbName} style={{ marginBottom: 16 }}>
                      <div style={{ fontSize: 11, fontWeight: 700, color, marginBottom: 6, letterSpacing: '0.06em' }}>
                        {dbName.toUpperCase()} DATABASE
                      </div>
                      {Object.entries(dbInfo.tables || {}).map(([tableName, cols]) => (
                        <div key={tableName} style={{ marginBottom: 8 }}>
                          <div style={{ fontSize: 12, color: 'var(--text-secondary)', fontWeight: 600, marginBottom: 3 }}>
                            📋 {tableName}
                          </div>
                          <div style={{ paddingLeft: 12, display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                            {(cols as SchemaTable[]).map(col => (
                              <span key={col.name} style={{
                                fontSize: 10,
                                padding: '2px 7px',
                                borderRadius: 4,
                                background: col.pk ? `${color}33` : 'var(--color-surface-2)',
                                color: col.pk ? color : 'var(--text-muted)',
                                border: col.pk ? `1px solid ${color}55` : '1px solid var(--color-border)',
                                fontFamily: 'monospace',
                              }}>
                                {col.pk ? '🔑 ' : ''}{col.name}
                              </span>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div style={{
          color: 'var(--color-danger)',
          background: 'var(--color-danger-dim)',
          border: '1px solid rgba(239,68,68,0.3)',
          borderRadius: 12,
          padding: '14px 18px',
          marginBottom: 20,
          fontFamily: 'monospace',
          fontSize: 13,
        }}>
          ❌ {error}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="loading-center"><div className="spinner" /><span>Executing query…</span></div>
      )}

      {/* Write Result */}
      {writeResult && !loading && (
        <div style={{
          background: 'var(--color-surface)',
          border: '1px solid var(--color-success)',
          borderRadius: 14,
          padding: 20,
          marginBottom: 20,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
            <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'var(--color-success)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontSize: 18 }}>
              ✓
            </div>
            <h3 style={{ margin: 0, color: 'var(--color-success)' }}>Query Executed Successfully</h3>
          </div>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, background: 'var(--color-surface-2)', padding: 16, borderRadius: 8 }}>
            <div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4, letterSpacing: '0.05em' }}>DATABASE</div>
              <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{writeResult.database.toUpperCase()}</div>
            </div>
            <div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4, letterSpacing: '0.05em' }}>EXECUTED BY</div>
              <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{writeResult.owner}</div>
            </div>
            <div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4, letterSpacing: '0.05em' }}>AFFECTED ROWS</div>
              <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{writeResult.affected_rows}</div>
            </div>
            <div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4, letterSpacing: '0.05em' }}>LAST INSERT ID</div>
              <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{writeResult.last_insert_id || 'N/A'}</div>
            </div>
          </div>
          
          {writeResult.forwarded_to && (
            <div style={{ marginTop: 12, fontSize: 12, color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 6 }}>
              <span>📡</span> Request was forwarded to node at {writeResult.forwarded_to}
            </div>
          )}
        </div>
      )}

      {/* Results */}
      {results && !loading && (
        <div>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            marginBottom: 16,
          }}>
            <div className="card-title">Query Results</div>
            <span style={{
              background: 'var(--color-success-dim)',
              color: 'var(--color-success)',
              borderRadius: 20,
              padding: '3px 12px',
              fontSize: 12,
              fontWeight: 700,
            }}>
              {totalRows} row{totalRows !== 1 ? 's' : ''} total
            </span>
            {database === 'all' && (
              <span style={{ fontSize: 11, color: 'var(--text-muted)', marginLeft: 8 }}>
                ℹ️ Ran on all 5 DBs — only DBs where the table exists will show results
              </span>
            )}
          </div>

          {results.map((resultSet, i) => {
            const color = DB_OPTIONS.find(d => d.value === resultSet.database)?.color ?? '#aaa';
            // "no such table" is expected when running a table-specific query across all DBs.
            // Show it as a soft grey note, not a scary red error.
            const isNoTable = resultSet.error?.includes('no such table');
            if (resultSet.error && isNoTable && results.length > 1) {
              return (
                <div key={i} style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 6,
                  padding: '4px 10px',
                  borderRadius: 8,
                  background: 'var(--color-surface-2)',
                  border: '1px solid var(--color-border)',
                  color: 'var(--text-muted)',
                  fontSize: 11,
                  marginRight: 8,
                  marginBottom: 8,
                }}>
                  <span style={{ color }}>
                    {DB_OPTIONS.find(d => d.value === resultSet.database)?.label.split(' ')[0]}
                  </span>
                  {resultSet.database} — table not in this DB
                </div>
              );
            }
            if (resultSet.error && !isNoTable) {
              return (
                <div key={i} style={{
                  background: 'var(--color-surface)',
                  border: '1px solid rgba(239,68,68,0.3)',
                  borderRadius: 12,
                  padding: 16,
                  marginBottom: 16,
                  color: 'var(--color-danger)',
                  fontSize: 12,
                  fontFamily: 'monospace',
                }}>
                  <strong>{resultSet.database.toUpperCase()}:</strong> {resultSet.error}
                </div>
              );
            }
            if (resultSet.row_count === 0 && results.length > 1) return null;
            return (
              <div key={i} style={{
                background: 'var(--color-surface)',
                border: `1px solid ${color}33`,
                borderRadius: 14,
                marginBottom: 20,
                overflow: 'hidden',
              }}>
                {/* Table header */}
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  padding: '12px 16px',
                  background: `${color}11`,
                  borderBottom: `1px solid ${color}22`,
                }}>
                  <span style={{ color, fontWeight: 700, fontSize: 13 }}>
                    {DB_OPTIONS.find(d => d.value === resultSet.database)?.label}
                  </span>
                  <span style={{
                    background: `${color}22`,
                    color,
                    borderRadius: 10,
                    padding: '1px 8px',
                    fontSize: 11,
                    fontWeight: 700,
                  }}>
                    {resultSet.row_count} rows
                  </span>
                  {resultSet.columns.length > 0 && (
                    <span style={{ fontSize: 11, color: 'var(--text-muted)', marginLeft: 'auto' }}>
                      {resultSet.columns.length} columns
                    </span>
                  )}
                </div>

                {/* Table data */}
                {resultSet.columns.length > 0 ? (
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{
                      width: '100%',
                      borderCollapse: 'collapse',
                      fontSize: 12,
                    }}>
                      <thead>
                        <tr>
                          {resultSet.columns.map(col => (
                            <th key={col} style={{
                              padding: '8px 14px',
                              textAlign: 'left',
                              background: 'var(--color-surface-2)',
                              color,
                              fontWeight: 700,
                              fontSize: 11,
                              letterSpacing: '0.04em',
                              borderBottom: `1px solid ${color}22`,
                              whiteSpace: 'nowrap',
                              fontFamily: 'monospace',
                            }}>
                              {col}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {resultSet.rows.map((row, ri) => (
                          <tr key={ri} style={{ borderBottom: '1px solid var(--color-border)' }}
                            onMouseEnter={e => (e.currentTarget as HTMLTableRowElement).style.background = `${color}08`}
                            onMouseLeave={e => (e.currentTarget as HTMLTableRowElement).style.background = 'transparent'}
                          >
                            {resultSet.columns.map(col => (
                              <td key={col} style={{
                                padding: '8px 14px',
                                color: 'var(--text-secondary)',
                                whiteSpace: 'nowrap',
                                maxWidth: 300,
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                fontFamily: 'monospace',
                                fontSize: 12,
                              }}>
                                {row[col] == null
                                  ? <span style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>NULL</span>
                                  : String(row[col])}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div style={{ padding: 20, color: 'var(--text-muted)', textAlign: 'center', fontSize: 13 }}>
                    No results from this database for the given query.
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
