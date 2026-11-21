import { useState } from 'react';
import { api } from '../api';

const DEMO_PLATES = ['DL7CQ1939', 'MH12AB1234', 'KA01MN5678', 'TN10CD9012', 'UP80EF3456'];

interface NodeContext {
  source: string;
  found: boolean;
  plate?: string;
  risk_flags?: string[];
  context_keywords?: string[];
  fk_tables_joined?: string[];
  [key: string]: any;
}

interface UnstructuredResult {
  document: string;
  relevance_score: number;
  matched_keywords: string[];
  snippet: string;
}

export default function ContextDiscovery() {
  const [plate, setPlate] = useState('DL7CQ1939');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');
  const [schemaGraph, setSchemaGraph] = useState<any>(null);

  const runSearch = async () => {
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const data = await api.contextSearch(plate);
      setResult(data);
    } catch (e: any) {
      setError(e.message || 'Context search failed');
    }
    setLoading(false);
  };

  const loadSchema = async () => {
    try {
      const data = await api.getSchemaGraph();
      setSchemaGraph(data);
    } catch (e: any) {
      setError(e.message);
    }
  };

  const riskColor = (level: string) => {
    if (level === 'CRITICAL') return '#dc2626';
    if (level === 'HIGH') return '#ea580c';
    if (level === 'MEDIUM') return '#d97706';
    return '#16a34a';
  };

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 4 }}>
        🔍 Phase 3: Context Discovery & Unstructured Data Integration
      </h1>
      <p style={{ color: '#6b7280', marginBottom: 20, fontSize: 14 }}>
        Federated FK-PK context discovery across distributed databases + TF-IDF unstructured search
      </p>

      {/* Search bar */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 12, flexWrap: 'wrap' }}>
        <input
          value={plate}
          onChange={e => setPlate(e.target.value.toUpperCase())}
          placeholder="Enter plate number..."
          onKeyDown={e => e.key === 'Enter' && runSearch()}
          style={{
            padding: '10px 16px', borderRadius: 8, border: '1px solid #d1d5db',
            fontSize: 15, fontFamily: 'monospace', width: 220,
          }}
        />
        <button onClick={runSearch} disabled={loading} style={{
          padding: '10px 24px', borderRadius: 8, border: 'none',
          background: loading ? '#9ca3af' : '#2563eb', color: '#fff',
          fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer', fontSize: 14,
        }}>
          {loading ? '⏳ Searching...' : '🔍 Context Search'}
        </button>
        <button onClick={loadSchema} style={{
          padding: '10px 16px', borderRadius: 8, border: '1px solid #d1d5db',
          background: '#f9fafb', cursor: 'pointer', fontSize: 14,
        }}>
          📊 FK-PK Schema
        </button>
      </div>

      {/* Quick plates */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 24, flexWrap: 'wrap' }}>
        <span style={{ fontSize: 12, color: '#9ca3af', lineHeight: '28px' }}>Quick:</span>
        {DEMO_PLATES.map(p => (
          <button key={p} onClick={() => { setPlate(p); }} style={{
            padding: '4px 10px', borderRadius: 6, border: '1px solid #e5e7eb',
            background: plate === p ? '#dbeafe' : '#fff', cursor: 'pointer',
            fontSize: 12, fontFamily: 'monospace',
          }}>{p}</button>
        ))}
      </div>

      {error && <div style={{ padding: 12, background: '#fef2f2', color: '#dc2626', borderRadius: 8, marginBottom: 16 }}>❌ {error}</div>}

      {/* Schema Graph */}
      {schemaGraph && (
        <div style={{ marginBottom: 24, padding: 16, background: '#f0fdf4', borderRadius: 12, border: '1px solid #bbf7d0' }}>
          <h3 style={{ marginTop: 0, fontSize: 16 }}>📊 FK-PK Relationship Graph — {schemaGraph.total_tables} Tables, {schemaGraph.total_fk_relationships} FK Relationships</h3>
          <p style={{ fontSize: 12, color: '#6b7280', margin: '4px 0 12px' }}>{schemaGraph.global_key}</p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12 }}>
            {Object.entries(schemaGraph.databases).map(([dbName, db]: [string, any]) => (
              <div key={dbName} style={{ padding: 12, background: '#fff', borderRadius: 8, border: '1px solid #d1d5db' }}>
                <div style={{ fontWeight: 700, fontSize: 14, color: '#1e40af', marginBottom: 6 }}>
                  {dbName}.db
                </div>
                <div style={{ fontSize: 12, color: '#059669', marginBottom: 4 }}>
                  PK: {db.primary_table} ({db.vehicle_key})
                </div>
                {Object.entries(db.related_tables).map(([tbl, info]: [string, any]) => (
                  <div key={tbl} style={{ fontSize: 11, padding: '2px 0', color: '#374151' }}>
                    → {tbl} <span style={{ color: '#9ca3af' }}>({info.relationship}, FK: {info.fk})</span>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Results */}
      {result && (
        <div>
          {/* Risk & Performance header */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12, marginBottom: 20 }}>
            <div style={{
              padding: 16, borderRadius: 12, border: '2px solid',
              borderColor: riskColor(result.risk_assessment?.risk_level),
              background: '#fff',
            }}>
              <div style={{ fontSize: 12, color: '#6b7280' }}>Risk Assessment</div>
              <div style={{ fontSize: 28, fontWeight: 800, color: riskColor(result.risk_assessment?.risk_level) }}>
                {result.risk_assessment?.risk_score}/100
              </div>
              <div style={{ fontSize: 13, fontWeight: 600, color: riskColor(result.risk_assessment?.risk_level) }}>
                {result.risk_assessment?.risk_level}
              </div>
              {result.risk_assessment?.risk_flags?.map((f: string, i: number) => (
                <span key={i} style={{
                  display: 'inline-block', margin: '4px 4px 0 0', padding: '2px 8px',
                  background: '#fef2f2', color: '#dc2626', borderRadius: 4, fontSize: 11,
                }}>{f}</span>
              ))}
            </div>
            <div style={{ padding: 16, borderRadius: 12, background: '#eff6ff', border: '1px solid #bfdbfe' }}>
              <div style={{ fontSize: 12, color: '#6b7280' }}>Structured Context</div>
              <div style={{ fontSize: 28, fontWeight: 800, color: '#1e40af' }}>
                {result.structured_context?.nodes_with_data}/{result.structured_context?.nodes_queried}
              </div>
              <div style={{ fontSize: 13 }}>Nodes with data</div>
              <div style={{ fontSize: 12, color: '#6b7280', marginTop: 4 }}>
                {result.structured_context?.total_fk_tables_joined} FK tables joined
              </div>
            </div>
            <div style={{ padding: 16, borderRadius: 12, background: '#fefce8', border: '1px solid #fde68a' }}>
              <div style={{ fontSize: 12, color: '#6b7280' }}>Performance</div>
              <div style={{ fontSize: 28, fontWeight: 800, color: '#a16207' }}>
                {result.performance?.total_ms}ms
              </div>
              <div style={{ fontSize: 13 }}>Total round-trip</div>
              {result.performance?.per_step_ms && Object.entries(result.performance.per_step_ms).map(([k, v]: [string, any]) => (
                <div key={k} style={{ fontSize: 11, color: '#6b7280' }}>
                  {k}: {typeof v === 'number' ? `${v}ms` : v}
                </div>
              ))}
            </div>
          </div>

          {/* Distributed processing info */}
          {result.distributed_processing && (
            <div style={{ marginBottom: 20, padding: 16, background: '#faf5ff', borderRadius: 12, border: '1px solid #e9d5ff' }}>
              <h3 style={{ marginTop: 0, fontSize: 15 }}>🖧 Distributed Processing (Real-Time)</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
                {['master', 'node_a', 'node_b'].map(key => {
                  const node = result.distributed_processing[key];
                  if (!node) return null;
                  const online = node.status === 'ONLINE';
                  return (
                    <div key={key} style={{
                      padding: 10, background: '#fff', borderRadius: 8,
                      border: `1px solid ${online ? '#86efac' : '#fca5a5'}`,
                    }}>
                      <div style={{ fontWeight: 600, fontSize: 13 }}>{node.node}</div>
                      <div style={{ fontSize: 11, color: '#6b7280' }}>DBs: {node.databases?.join(', ')}</div>
                      <div style={{
                        fontSize: 11, fontWeight: 600, marginTop: 4,
                        color: online ? '#16a34a' : (node.status?.includes('OFFLINE') ? '#dc2626' : '#6b7280'),
                      }}>
                        {node.status || 'LOCAL'}
                      </div>
                      <div style={{ fontSize: 10, color: '#9ca3af', marginTop: 2 }}>{node.processing?.substring(0, 80)}...</div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Per-node context cards */}
          <h3 style={{ fontSize: 16, marginBottom: 12 }}>📋 Per-Node Context (FK-PK Joined Results)</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 12, marginBottom: 20 }}>
            {result.structured_context?.per_node_context?.map((ctx: NodeContext, i: number) => (
              <div key={i} style={{
                padding: 14, borderRadius: 10, background: '#fff',
                border: `1px solid ${ctx.found ? '#d1d5db' : '#fecaca'}`,
                opacity: ctx.found ? 1 : 0.6,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <span style={{ fontWeight: 700, fontSize: 14, color: '#1e3a5f' }}>
                    {ctx.source?.toUpperCase()}.db
                  </span>
                  <span style={{
                    padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 600,
                    background: ctx.found ? '#dcfce7' : '#fef2f2',
                    color: ctx.found ? '#16a34a' : '#dc2626',
                  }}>
                    {ctx.found ? 'FOUND' : 'NO DATA'}
                  </span>
                </div>
                {ctx.fk_tables_joined && (
                  <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 6 }}>
                    FK joins: {ctx.fk_tables_joined.join(', ')}
                  </div>
                )}
                {ctx.risk_flags && ctx.risk_flags.length > 0 && (
                  <div style={{ marginBottom: 6 }}>
                    {ctx.risk_flags.map((f: string, j: number) => (
                      <span key={j} style={{
                        display: 'inline-block', margin: '0 4px 4px 0', padding: '1px 6px',
                        background: '#fef2f2', color: '#dc2626', borderRadius: 4, fontSize: 10,
                      }}>{f}</span>
                    ))}
                  </div>
                )}
                {/* Show summary data */}
                <pre style={{
                  fontSize: 11, background: '#f9fafb', padding: 8, borderRadius: 6,
                  overflow: 'auto', maxHeight: 200, whiteSpace: 'pre-wrap', margin: 0,
                }}>
                  {JSON.stringify(
                    Object.fromEntries(
                      Object.entries(ctx).filter(([k]) =>
                        !['source', 'found', 'plate', 'risk_flags', 'context_keywords', 'fk_tables_joined', 'error'].includes(k)
                      )
                    ), null, 2
                  )}
                </pre>
              </div>
            ))}
          </div>

          {/* Unstructured data results */}
          {result.unstructured_data && (
            <div style={{ marginBottom: 20 }}>
              <h3 style={{ fontSize: 16, marginBottom: 8 }}>
                📄 Unstructured Data (TF-IDF Search) — {result.unstructured_data.documents_found} documents matched
              </h3>
              <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 12 }}>
                Keywords: {result.unstructured_data.search_keywords_used?.slice(0, 15).join(', ')}
                {result.unstructured_data.search_keywords_used?.length > 15 && '...'}
              </div>
              {result.unstructured_data.results?.map((doc: UnstructuredResult, i: number) => (
                <div key={i} style={{
                  padding: 12, marginBottom: 8, borderRadius: 8, background: '#fffbeb',
                  border: '1px solid #fde68a',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ fontWeight: 600, fontSize: 13 }}>📎 {doc.document}</span>
                    <span style={{
                      padding: '2px 8px', borderRadius: 4, fontSize: 11,
                      background: doc.relevance_score > 0.3 ? '#dcfce7' : '#fefce8',
                      fontWeight: 600,
                    }}>
                      Score: {(doc.relevance_score * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 4 }}>
                    Matched: {doc.matched_keywords?.join(', ')}
                  </div>
                  <div style={{
                    fontSize: 12, color: '#374151', background: '#fff',
                    padding: 8, borderRadius: 6, fontStyle: 'italic',
                  }}>
                    {doc.snippet}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Accumulated keywords */}
          {result.accumulated_keywords && (
            <div style={{ marginBottom: 20 }}>
              <h3 style={{ fontSize: 14, marginBottom: 8 }}>🔑 Accumulated Context Keywords</h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                {result.accumulated_keywords.map((kw: string, i: number) => (
                  <span key={i} style={{
                    padding: '3px 8px', background: '#eff6ff', color: '#1e40af',
                    borderRadius: 4, fontSize: 11,
                  }}>{kw}</span>
                ))}
              </div>
            </div>
          )}

          {/* Integration metadata */}
          {result.integration_metadata && (
            <div style={{ padding: 14, background: '#f0fdf4', borderRadius: 10, border: '1px solid #bbf7d0' }}>
              <h3 style={{ marginTop: 0, fontSize: 14 }}>📐 Integration Metadata (Phase 3 Rubric Coverage)</h3>
              <div style={{ fontSize: 12 }}>
                <div><strong>Phase:</strong> {result.integration_metadata.phase}</div>
                <div><strong>Method:</strong> {result.integration_metadata.method}</div>
                {result.integration_metadata.rubric_coverage && Object.entries(result.integration_metadata.rubric_coverage).map(([k, v]: [string, any]) => (
                  <div key={k}><strong>{k}:</strong> {v}</div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
