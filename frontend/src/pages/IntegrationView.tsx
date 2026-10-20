import { useEffect, useState } from 'react';
import { api } from '../api';

const SOURCE_COLORS: Record<string, string> = {
  capture:      '#6366f1',
  insurance:    '#22c55e',
  registration: '#f59e0b',
  theft:        '#ef4444',
  ministry:     '#a855f7',
};

export default function IntegrationView() {
  const [schema, setSchema] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'mapping' | 'matching' | 'indexing' | 'uncertainty' | 'mediator'>('mapping');

  // Indexing tab state
  const [indexStats, setIndexStats] = useState<any>(null);
  const [searchQuery, setSearchQuery] = useState('UP32AB123B');
  const [searchMethod, setSearchMethod] = useState('prefix_index');
  const [searchThreshold, setSearchThreshold] = useState(0.4);
  const [searchResults, setSearchResults] = useState<any>(null);
  const [searchLoading, setSearchLoading] = useState(false);

  // Uncertainty tab state
  const [str1, setStr1] = useState('UP32AB1234');
  const [str2, setStr2] = useState('UP32AB123B');
  const [metricsResult, setMetricsResult] = useState<any>(null);
  const [metricsLoading, setMetricsLoading] = useState(false);
  const [sensorConfidence, setSensorConfidence] = useState(0.90);
  const [uncertaintyResult, setUncertaintyResult] = useState<any>(null);
  const [uncertaintyLoading, setUncertaintyLoading] = useState(false);

  useEffect(() => {
    api.getIntegrationSchema()
      .then(setSchema)
      .catch(() => setSchema(null))
      .finally(() => setLoading(false));

    api.getIndexingStats()
      .then(setIndexStats)
      .catch(() => setIndexStats(null));
  }, []);

  const handleRunIndexSearch = async () => {
    if (!searchQuery.trim()) return;
    setSearchLoading(true);
    try {
      const res = await api.searchIndexCandidates(searchQuery.trim().toUpperCase(), searchMethod, searchThreshold);
      setSearchResults(res);
    } catch (e) {
      console.error(e);
    } finally {
      setSearchLoading(false);
    }
  };

  const handleComputeMetrics = async () => {
    if (!str1.trim() || !str2.trim()) return;
    setMetricsLoading(true);
    try {
      const res = await api.compareStringMetrics(str1.trim().toUpperCase(), str2.trim().toUpperCase());
      setMetricsResult(res);
    } catch (e) {
      console.error(e);
    } finally {
      setMetricsLoading(false);
    }
  };

  const handleEvaluateUncertainty = async () => {
    if (!str1.trim() || !str2.trim()) return;
    setUncertaintyLoading(true);
    try {
      const res = await api.evaluateUncertainty(str1.trim().toUpperCase(), str2.trim().toUpperCase(), sensorConfidence);
      setUncertaintyResult(res);
    } catch (e) {
      console.error(e);
    } finally {
      setUncertaintyLoading(false);
    }
  };

  const keyCorrespondences = schema?.key_correspondences || [];

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Integration <span>View</span></h1>
        <p className="page-subtitle">
          GAV Schema Mapping · Schema Matching · Week 6–8 Inverted Indexing &amp; Prefix Filtering · Part B: Data Integration Under Uncertainty
        </p>
      </div>

      {/* Architecture Diagram */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="section-header">
          <span>⎈</span>
          <h2>Mediation / Federated Architecture (IIA-1)</h2>
        </div>

        {/* Visual diagram */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0, padding: '8px 0' }}>
          {/* Global Query */}
          <div style={{ background: 'var(--color-primary-glow)', border: '2px solid var(--color-primary)', borderRadius: 12, padding: '12px 32px', fontWeight: 700, color: 'var(--color-primary)', fontSize: 14 }}>
            Global Query: SELECT * WHERE registration_number = 'UP32AB1234'
          </div>
          <div style={{ height: 20, width: 2, background: 'var(--color-primary)', margin: '0 auto' }} />

          {/* Mediator */}
          <div style={{ background: 'var(--color-surface-2)', border: '2px solid var(--color-border)', borderRadius: 16, padding: '18px 40px', textAlign: 'center', width: 'fit-content' }}>
            <div style={{ fontWeight: 800, fontSize: 16, marginBottom: 4 }}>⎈ MEDIATOR</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              Schema Mapper (GAV) · Q-Gram Inverted Index (Bayardo '07) · Uncertainty Evaluator (STP Policy)
            </div>
          </div>
          <div style={{ height: 16, width: 2, background: 'var(--color-border)', margin: '0 auto' }} />

          {/* Decomposed sub-queries */}
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', justifyContent: 'center' }}>
            {Object.entries({
              capture:      'plate_number',
              insurance:    'registration_id',
              registration: 'vehicle_reg_no',
              theft:        'vehicle_identifier',
              ministry:     'vehicle_ref',
            }).map(([src, key]) => (
              <div key={src} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
                <div style={{ height: 16, width: 2, background: SOURCE_COLORS[src] }} />
                <div style={{
                  background: `${SOURCE_COLORS[src]}18`,
                  border: `2px solid ${SOURCE_COLORS[src]}55`,
                  borderRadius: 10, padding: '10px 14px', textAlign: 'center', minWidth: 130,
                }}>
                  <div style={{ fontWeight: 700, color: SOURCE_COLORS[src], fontSize: 12, marginBottom: 3 }}>{src}.db</div>
                  <code style={{ fontSize: 11, color: '#94a3b8', fontFamily: 'JetBrains Mono, monospace' }}>WHERE {key}</code>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>= 'UP32AB1234'</div>
                </div>
              </div>
            ))}
          </div>

          <div style={{ height: 16, width: 2, background: 'var(--color-border)', margin: '0 auto' }} />
          {/* Result Integration */}
          <div style={{ background: 'var(--color-success-dim)', border: '2px solid rgba(34,197,94,0.4)', borderRadius: 12, padding: '12px 32px', fontWeight: 700, color: 'var(--color-success)', fontSize: 14 }}>
            ✓ Unified Vehicle View — Multi-Source Join + Calibrated Probability P(Match)
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs">
        {(['mapping', 'matching', 'indexing', 'uncertainty', 'mediator'] as const).map(tab => (
          <button key={tab} className={`tab${activeTab === tab ? ' active' : ''}`} onClick={() => setActiveTab(tab)}>
            {tab === 'mapping' ? 'GAV Schema Mapping' :
             tab === 'matching' ? 'Schema Matching' :
             tab === 'indexing' ? '⚡ Week 6-8 Indexing & Blocking' :
             tab === 'uncertainty' ? '🎯 Part B: Uncertainty & Decision Policy (15M)' :
             'Query Decomposition'}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="loading-center"><div className="spinner" /></div>
      ) : activeTab === 'mapping' ? (
        <div>
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16 }}>
              <strong style={{ color: 'var(--color-primary)' }}>Global-As-View (GAV)</strong>: The global schema attribute <code style={{ color: 'var(--color-success)' }}>registration_number</code> is defined as a view over source-local attributes. Each source reports its local key; the mediator maps them to the global concept. (IIA-3, slides 18-24)
            </div>
          </div>
          <div className="mapping-container">
            <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr auto auto', gap: '0 16px', alignItems: 'center', marginBottom: 12, padding: '0 0 10px', borderBottom: '1px solid var(--color-border)' }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Source DB</div>
              <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Local Attribute</div>
              <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}></div>
              <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Global Attribute</div>
            </div>
            {Object.entries(schema?.all_source_keys || {}).map(([src, localKey]: [string, any]) => (
              <div key={src} style={{ display: 'grid', gridTemplateColumns: 'auto 1fr auto auto', gap: '0 16px', alignItems: 'center', padding: '10px 0', borderBottom: '1px solid var(--color-border)' }}>
                <div style={{ fontWeight: 700, color: SOURCE_COLORS[src], fontSize: 13 }}>{src}.db</div>
                <div>
                  <code style={{ color: SOURCE_COLORS[src], fontFamily: 'JetBrains Mono, monospace', fontSize: 13, fontWeight: 700, background: `${SOURCE_COLORS[src]}15`, padding: '3px 10px', borderRadius: 5 }}>
                    {localKey}
                  </code>
                </div>
                <span style={{ color: 'var(--text-muted)', fontSize: 18 }}>↔</span>
                <code style={{ color: 'var(--color-success)', fontFamily: 'JetBrains Mono, monospace', fontSize: 13, fontWeight: 700, background: 'var(--color-success-dim)', padding: '3px 10px', borderRadius: 5 }}>
                  registration_number
                </code>
              </div>
            ))}
          </div>

          {/* Secondary mappings */}
          <div style={{ marginTop: 20 }}>
            <div className="card-title" style={{ marginBottom: 10 }}>All GAV Mappings</div>
            <div className="table-wrapper">
              <table className="table">
                <thead><tr><th>Global Attribute</th><th>Source</th><th>Local Attribute</th><th>Mapping Type</th></tr></thead>
                <tbody>
                  {(schema?.gav_mapping || []).map((m: any, i: number) => (
                    <tr key={i}>
                      <td><code style={{ color: 'var(--color-success)', fontSize: 12 }}>{m.global_attribute}</code></td>
                      <td><span style={{ color: SOURCE_COLORS[m.source] || 'var(--text-primary)', fontWeight: 600 }}>{m.source}</span></td>
                      <td><code style={{ color: SOURCE_COLORS[m.source] || 'var(--text-primary)', fontSize: 12 }}>{m.local_attribute}</code></td>
                      <td><span style={{ fontSize: 11, color: 'var(--color-primary)', background: 'var(--color-primary-glow)', padding: '2px 8px', borderRadius: 100 }}>{m.mapping_type}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : activeTab === 'matching' ? (
        <div>
          <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16 }}>
            <strong style={{ color: 'var(--color-primary)' }}>Schema Matching</strong>: Automatic discovery of correspondences between source schemas using linguistic similarity (edit distance + Jaccard + cosine bigrams). (IIA-3, slides 9-17)
          </div>
          <div className="card" style={{ marginBottom: 20 }}>
            <div className="card-title" style={{ marginBottom: 12 }}>Key Identifier Correspondences</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 16 }}>
              Pairwise similarity scores between the vehicle identifier attributes across all sources. Demonstrates that despite different names, the system can automatically discover they represent the same concept.
            </div>
            <div className="table-wrapper">
              <table className="table">
                <thead><tr><th>Source 1</th><th>Attribute 1</th><th>Source 2</th><th>Attribute 2</th><th>Similarity</th><th>Match Type</th></tr></thead>
                <tbody>
                  {keyCorrespondences.map((c: any, i: number) => (
                    <tr key={i}>
                      <td style={{ color: SOURCE_COLORS[c.source1] || 'var(--text-primary)' }}>{c.source1}</td>
                      <td><code style={{ color: SOURCE_COLORS[c.source1], fontSize: 12 }}>{c.attr1}</code></td>
                      <td style={{ color: SOURCE_COLORS[c.source2] || 'var(--text-primary)' }}>{c.source2}</td>
                      <td><code style={{ color: SOURCE_COLORS[c.source2], fontSize: 12 }}>{c.attr2}</code></td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <div style={{ flex: 1, height: 6, background: 'var(--color-border)', borderRadius: 3, maxWidth: 80, overflow: 'hidden' }}>
                            <div style={{ height: '100%', width: `${c.similarity * 100}%`, background: c.similarity > 0.7 ? 'var(--color-success)' : c.similarity > 0.5 ? 'var(--color-warning)' : 'var(--color-danger)', borderRadius: 3 }} />
                          </div>
                          <span style={{ fontSize: 12, fontWeight: 600 }}>{(c.similarity * 100).toFixed(0)}%</span>
                        </div>
                      </td>
                      <td>
                        <span className={`badge ${c.match_type === 'EXACT' ? 'insured' : c.match_type === 'HIGH' ? 'active' : c.match_type === 'MEDIUM' ? 'pending' : 'unknown'}`}>
                          {c.match_type}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div style={{ marginTop: 14, fontSize: 12, color: 'var(--text-muted)', background: 'var(--color-surface-2)', padding: '10px 14px', borderRadius: 8 }}>
              <strong>Hybrid Similarity Formula (IIA-3 slide 16):</strong> W_sim = 0.4 × L_sim (edit distance) + 0.3 × J_sim (Jaccard tokens) + 0.3 × C_sim (cosine bigrams)
            </div>
          </div>
        </div>
      ) : activeTab === 'indexing' ? (
        <div>
          {/* Week 6-8 Indexing & Inverted Lists Tab */}
          <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 20 }}>
            <strong style={{ color: 'var(--color-primary)' }}>Week 6–8 String Matching Indexing Framework: </strong>
            To avoid an exhaustive quadratic comparison <code style={{ color: '#f59e0b' }}>O(|R| × |S|)</code>, the mediator constructs an in-memory <strong>Q-Gram Inverted Index</strong> with <strong>Size Filtering (Arasu et al. VLDB '06)</strong> and <strong>Prefix-Inverted Index (Bayardo et al. WWW '07)</strong>. Only candidates satisfying the prefix bound <code style={{ color: 'var(--color-success)' }}>p = |x| - ⌈τ · |x|⌉ + 1</code> are verified.
          </div>

          {/* Index Stats Grid */}
          <div className="grid-3" style={{ marginBottom: 24 }}>
            <div className="card">
              <div className="card-title">Indexed Vehicle Plates</div>
              <div className="card-value" style={{ color: 'var(--color-primary)' }}>{indexStats?.total_records || '—'}</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>Aggregated across all 5 distributed DBs</div>
            </div>
            <div className="card">
              <div className="card-title">Q-Gram Vocabulary</div>
              <div className="card-value" style={{ color: 'var(--color-success)' }}>{indexStats?.qgram_vocabulary_size || '—'}</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>Unique bigrams (q=2) with IDF weights</div>
            </div>
            <div className="card">
              <div className="card-title">Avg Postings per Inverted List</div>
              <div className="card-value" style={{ color: 'var(--color-warning)' }}>{indexStats?.avg_postings_per_list || '—'}</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>Rare-token ordering optimizes prefix pruning</div>
            </div>
          </div>

          {/* Interactive Candidate Search Playground */}
          <div className="card" style={{ marginBottom: 24 }}>
            <div className="section-header">
              <span>🔍</span>
              <h2>Interactive Candidate Index Retrieval (Playground)</h2>
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 16 }}>
              Simulate noisy camera OCR or user typos and inspect the candidates extracted by the indexing filtering pipelines before verification.
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginBottom: 16 }}>
              <div>
                <label style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', display: 'block', marginBottom: 6 }}>
                  Query String / Noisy OCR Plate
                </label>
                <input
                  type="text"
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  style={{
                    width: '100%', padding: '10px 14px', borderRadius: 8,
                    background: 'var(--color-surface-2)', border: '1px solid var(--color-border)',
                    color: 'var(--text-primary)', fontFamily: 'JetBrains Mono, monospace', fontSize: 14, fontWeight: 700
                  }}
                  placeholder="e.g. UP32AB123B"
                />
              </div>

              <div>
                <label style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', display: 'block', marginBottom: 6 }}>
                  Filtering Strategy (Course Literature)
                </label>
                <select
                  value={searchMethod}
                  onChange={e => setSearchMethod(e.target.value)}
                  style={{
                    width: '100%', padding: '10px 14px', borderRadius: 8,
                    background: 'var(--color-surface-2)', border: '1px solid var(--color-border)',
                    color: 'var(--text-primary)', fontSize: 13
                  }}
                >
                  <option value="prefix_index">Prefix-Inverted Index (Bayardo WWW '07) [RECOMMENDED]</option>
                  <option value="inverted_index">Q-Gram Inverted Lists (Sarawagi SIGMOD '04)</option>
                  <option value="size_filter">Size &amp; Length Filtering (Arasu VLDB '06)</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', display: 'block', marginBottom: 6 }}>
                  Jaccard Threshold τ: {(searchThreshold).toFixed(2)}
                </label>
                <input
                  type="range"
                  min="0.2"
                  max="0.8"
                  step="0.05"
                  value={searchThreshold}
                  onChange={e => setSearchThreshold(parseFloat(e.target.value))}
                  style={{ width: '100%', marginTop: 8 }}
                />
              </div>
            </div>

            <button
              onClick={handleRunIndexSearch}
              disabled={searchLoading}
              style={{
                background: 'var(--color-primary)', border: 'none', borderRadius: 8,
                padding: '10px 20px', color: '#fff', fontWeight: 700, fontSize: 13,
                cursor: searchLoading ? 'not-allowed' : 'pointer'
              }}
            >
              {searchLoading ? 'Filtering candidates…' : '⚡ Execute Candidate Search'}
            </button>

            {/* Results display */}
            {searchResults && (
              <div style={{ marginTop: 20, paddingTop: 16, borderTop: '1px solid var(--color-border)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>
                    Retrieved {searchResults.candidates_found} Candidate(s) for "{searchResults.query}"
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--color-success)', background: 'var(--color-success-dim)', padding: '3px 8px', borderRadius: 100 }}>
                    Method: {searchResults.method}
                  </div>
                </div>

                {searchResults.candidates?.length === 0 ? (
                  <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>No candidate records satisfied the threshold.</div>
                ) : (
                  <div className="table-wrapper">
                    <table className="table">
                      <thead>
                        <tr>
                          <th>Candidate Plate</th>
                          <th>Shared Q-Grams</th>
                          <th>Jaccard Bound / Sim</th>
                          <th>Plate Length</th>
                          <th>Verification Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {searchResults.candidates.map((cand: any, idx: number) => (
                          <tr key={idx}>
                            <td>
                              <code style={{ color: 'var(--color-primary)', fontSize: 13, fontWeight: 700 }}>
                                {cand.plate}
                              </code>
                            </td>
                            <td>
                              <span style={{ fontSize: 12 }}>{cand.shared_qgrams} common bigrams</span>
                            </td>
                            <td>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                <div style={{ flex: 1, height: 6, background: 'var(--color-border)', borderRadius: 3, maxWidth: 80, overflow: 'hidden' }}>
                                  <div style={{ height: '100%', width: `${cand.similarity * 100}%`, background: 'var(--color-success)', borderRadius: 3 }} />
                                </div>
                                <span style={{ fontSize: 12, fontWeight: 700 }}>{(cand.similarity * 100).toFixed(1)}%</span>
                              </div>
                            </td>
                            <td>{cand.length} chars</td>
                            <td>
                              <a
                                href={`/search?plate=${cand.plate}`}
                                style={{
                                  fontSize: 11, padding: '4px 8px', borderRadius: 4,
                                  background: 'var(--color-primary-glow)', color: 'var(--color-primary)', fontWeight: 600
                                }}
                              >
                                Query Full Record →
                              </a>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Academic Literature Summary */}
          <div className="grid-2">
            <div className="card">
              <div className="card-title">Size Filtering Theorem (Arasu et al. VLDB '06)</div>
              <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 8 }}>
                For any two strings <code>x</code> and <code>y</code> with Jaccard similarity <code>J(x, y) ≥ τ</code>, their lengths must satisfy:
              </p>
              <div style={{ background: 'var(--color-surface-2)', padding: '10px 14px', borderRadius: 8, margin: '10px 0', fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: 'var(--color-primary)' }}>
                ⌈τ · |x|⌉ ≤ |y| ≤ ⌊|x| / τ⌋
              </div>
              <p style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                All database records outside this length window are pruned in O(1) time without scanning individual tokens.
              </p>
            </div>

            <div className="card">
              <div className="card-title">Prefix Filtering Theorem (Chaudhuri ICDE '06 / Bayardo WWW '07)</div>
              <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 8 }}>
                If tokens in <code>x</code> and <code>y</code> are ordered by increasing global frequency (rarest first), they share at least one prefix token of length:
              </p>
              <div style={{ background: 'var(--color-surface-2)', padding: '10px 14px', borderRadius: 8, margin: '10px 0', fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: 'var(--color-success)' }}>
                prefix_len(x) = |x| - ⌈τ · |x|⌉ + 1
              </div>
              <p style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                Only the rare prefix tokens need to be added to inverted index lists, reducing inverted index size by 60–80%.
              </p>
            </div>
          </div>
        </div>
      ) : activeTab === 'uncertainty' ? (
        <div>
          {/* Part B: Uncertainty & Decision Policy (15 Marks) Tab */}
          <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 20 }}>
            <strong style={{ color: 'var(--color-primary)' }}>Part B (15 Marks) — Data Integration Under Uncertainty: </strong>
            Real-world ANPR camera captures and human registrations suffer from sensor noise, character confusion (e.g. <code>B ↔ 8</code>, <code>0 ↔ O</code>), and conflicting values. The system computes a <strong>multi-signal feature vector</strong>, calibrates match posterior probability <code style={{ color: 'var(--color-success)' }}>P(Match)</code>, routes entities via a <strong>3-Tier STP Decision Policy (Week 2 Slide 24)</strong>, and performs <strong>Probabilistic Truth Discovery</strong>.
          </div>

          {/* Section 1: 8-Metric Comparison Calculator */}
          <div className="card" style={{ marginBottom: 24 }}>
            <div className="section-header">
              <span>📐</span>
              <h2>Week 6–8 String Similarity Metrics (Live DP / Vector Engine)</h2>
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 16 }}>
              Compare two plates or string attributes across all 8 string matching algorithms from Week 6–8 lecture notes.
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16, marginBottom: 16 }}>
              <div>
                <label style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', display: 'block', marginBottom: 6 }}>
                  String 1 (Observed / Camera Plate)
                </label>
                <input
                  type="text"
                  value={str1}
                  onChange={e => setStr1(e.target.value)}
                  style={{
                    width: '100%', padding: '10px 14px', borderRadius: 8,
                    background: 'var(--color-surface-2)', border: '1px solid var(--color-border)',
                    color: 'var(--text-primary)', fontFamily: 'JetBrains Mono, monospace', fontSize: 14, fontWeight: 700
                  }}
                />
              </div>

              <div>
                <label style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', display: 'block', marginBottom: 6 }}>
                  String 2 (Registered / Database Plate)
                </label>
                <input
                  type="text"
                  value={str2}
                  onChange={e => setStr2(e.target.value)}
                  style={{
                    width: '100%', padding: '10px 14px', borderRadius: 8,
                    background: 'var(--color-surface-2)', border: '1px solid var(--color-border)',
                    color: 'var(--text-primary)', fontFamily: 'JetBrains Mono, monospace', fontSize: 14, fontWeight: 700
                  }}
                />
              </div>
            </div>

            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              <button
                onClick={handleComputeMetrics}
                disabled={metricsLoading}
                style={{
                  background: 'var(--color-primary)', border: 'none', borderRadius: 8,
                  padding: '10px 20px', color: '#fff', fontWeight: 700, fontSize: 13,
                  cursor: metricsLoading ? 'not-allowed' : 'pointer'
                }}
              >
                {metricsLoading ? 'Computing DP Matrix…' : '📐 Compute All 8 Similarity Metrics'}
              </button>

              <button
                onClick={handleEvaluateUncertainty}
                disabled={uncertaintyLoading}
                style={{
                  background: 'linear-gradient(135deg, #6366f1, #a855f7)', border: 'none', borderRadius: 8,
                  padding: '10px 20px', color: '#fff', fontWeight: 700, fontSize: 13,
                  cursor: uncertaintyLoading ? 'not-allowed' : 'pointer'
                }}
              >
                {uncertaintyLoading ? 'Evaluating…' : '🎯 Calibrate Match & STP Decision Policy'}
              </button>
            </div>

            {/* Metrics Results Table */}
            {metricsResult && (
              <div style={{ marginTop: 20, paddingTop: 16, borderTop: '1px solid var(--color-border)' }}>
                <div className="card-title" style={{ marginBottom: 12 }}>
                  Metric Comparison Results: "{metricsResult.string1}" vs "{metricsResult.string2}"
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12 }}>
                  {Object.entries(metricsResult.metrics || {}).map(([key, val]: [string, any]) => (
                    <div key={key} style={{ background: 'var(--color-surface-2)', padding: '12px 16px', borderRadius: 8, border: '1px solid var(--color-border)' }}>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        {key.replace(/_/g, ' ')}
                      </div>
                      <div style={{ fontSize: 18, fontWeight: 800, color: typeof val === 'number' && val >= 0.7 ? 'var(--color-success)' : 'var(--text-primary)', marginTop: 4 }}>
                        {typeof val === 'number' ? val.toFixed(4) : String(val)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Section 2: Uncertainty Evaluation & 3-Tier STP Policy */}
          {uncertaintyResult && (
            <div className="card" style={{ marginBottom: 24, border: '1px solid rgba(99,102,241,0.3)', background: 'linear-gradient(135deg, rgba(99,102,241,0.05) 0%, rgba(168,85,247,0.05) 100%)' }}>
              <div className="section-header">
                <span>🎯</span>
                <h2>Calibrated Probability &amp; 3-Tier STP Decision Routing (Week 2 Slide 24)</h2>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16, marginBottom: 16 }}>
                <div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Calibrated Match Posterior Probability P(Match)</div>
                  <div style={{ fontSize: 32, fontWeight: 900, color: uncertaintyResult.calibrated_probability >= 0.85 ? 'var(--color-success)' : uncertaintyResult.calibrated_probability >= 0.50 ? 'var(--color-warning)' : 'var(--color-danger)' }}>
                    {(uncertaintyResult.calibrated_probability * 100).toFixed(1)}%
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>Straight-Through Decision Policy</div>
                  <span style={{
                    padding: '8px 16px', borderRadius: 100, fontSize: 14, fontWeight: 800,
                    background: uncertaintyResult.decision_tier === 'AUTO_MERGE' ? 'var(--color-success-dim)' : uncertaintyResult.decision_tier === 'UNCERTAIN_REVIEW' ? 'var(--color-warning-dim)' : 'var(--color-danger-dim)',
                    color: uncertaintyResult.decision_tier === 'AUTO_MERGE' ? 'var(--color-success)' : uncertaintyResult.decision_tier === 'UNCERTAIN_REVIEW' ? 'var(--color-warning)' : 'var(--color-danger)',
                    border: `1px solid ${uncertaintyResult.decision_tier === 'AUTO_MERGE' ? 'rgba(34,197,94,0.4)' : uncertaintyResult.decision_tier === 'UNCERTAIN_REVIEW' ? 'rgba(245,158,11,0.4)' : 'rgba(239,68,68,0.4)'}`
                  }}>
                    {uncertaintyResult.decision_tier === 'AUTO_MERGE' ? '✓ AUTO-MERGE (STP)' : uncertaintyResult.decision_tier === 'UNCERTAIN_REVIEW' ? '⚡ ROUTE TO REVIEW QUEUE' : '✗ REJECT MATCH'}
                  </span>
                </div>
              </div>

              {/* Progress Bar of probability with threshold markers */}
              <div style={{ marginBottom: 20 }}>
                <div style={{ position: 'relative', height: 16, background: 'var(--color-surface-2)', borderRadius: 8, overflow: 'hidden' }}>
                  <div
                    style={{
                      height: '100%',
                      width: `${uncertaintyResult.calibrated_probability * 100}%`,
                      background: uncertaintyResult.calibrated_probability >= 0.85
                        ? 'linear-gradient(90deg, #22c55e, #10b981)'
                        : uncertaintyResult.calibrated_probability >= 0.50
                        ? 'linear-gradient(90deg, #f59e0b, #fbbf24)'
                        : 'linear-gradient(90deg, #ef4444, #f87171)',
                      borderRadius: 8,
                      transition: 'width 0.5s ease'
                    }}
                  />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
                  <span>0.00 (Reject Bound)</span>
                  <span style={{ color: 'var(--color-warning)' }}>τ_review = 0.50</span>
                  <span style={{ color: 'var(--color-success)' }}>τ_merge = 0.85</span>
                  <span>1.00 (Certain)</span>
                </div>
              </div>

              <div style={{ fontSize: 13, color: 'var(--text-primary)', background: 'var(--color-surface)', padding: '12px 16px', borderRadius: 8, border: '1px solid var(--color-border)', marginBottom: 16 }}>
                <strong>Routing Decision: </strong>{uncertaintyResult.policy?.routing}
              </div>

              {/* Multi-Signal Feature Vector Breakdown */}
              <div className="card-title" style={{ marginBottom: 10 }}>Extracted Feature Vector φ(r_i, r_j)</div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 10 }}>
                {Object.entries(uncertaintyResult.features || {}).map(([fKey, fVal]: [string, any]) => (
                  <div key={fKey} style={{ background: 'var(--color-surface)', padding: '8px 12px', borderRadius: 8, border: '1px solid var(--color-border)' }}>
                    <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'capitalize' }}>
                      {fKey.replace(/_/g, ' ')}
                    </div>
                    <div style={{ fontSize: 14, fontWeight: 700, color: typeof fVal === 'number' && fVal > 0.7 ? 'var(--color-success)' : 'var(--text-primary)', marginTop: 2 }}>
                      {typeof fVal === 'number' ? fVal.toFixed(3) : String(fVal)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Section 3: Sensor Confidence Simulation & Truth Discovery */}
          <div className="grid-2">
            <div className="card">
              <div className="card-title">Camera / Sensor Confidence Slider</div>
              <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 8 }}>
                Simulate environmental degradation (nighttime, rainfall, camera lens blur) affecting sensor reliability weight:
              </p>
              <div style={{ margin: '14px 0' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, fontWeight: 700, marginBottom: 6 }}>
                  <span>Sensor Reliability P(Sensor):</span>
                  <span style={{ color: 'var(--color-primary)' }}>{(sensorConfidence * 100).toFixed(0)}%</span>
                </div>
                <input
                  type="range"
                  min="0.4"
                  max="1.0"
                  step="0.05"
                  value={sensorConfidence}
                  onChange={e => setSensorConfidence(parseFloat(e.target.value))}
                  style={{ width: '100%' }}
                />
              </div>
              <p style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                Lower sensor confidence downweights OCR confusion likelihood and penalizes match posterior towards the uncertain review queue.
              </p>
            </div>

            <div className="card">
              <div className="card-title">Probabilistic Truth Discovery (Conflict Resolution)</div>
              <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 8 }}>
                When sources disagree on an attribute (e.g. Camera detects <code>BLUE</code> vs Registration states <code>WHITE</code>):
              </p>
              <div style={{ background: 'var(--color-surface-2)', padding: '10px 14px', borderRadius: 8, margin: '10px 0', fontFamily: 'JetBrains Mono, monospace', fontSize: 11, color: 'var(--color-purple)' }}>
                P(Val=v | Obs) ∝ P(v) · ∏_s P(O_s | v)
              </div>
              <p style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                Government RTO registry carries prior reliability weight <code>w=0.98</code> whereas single-frame surveillance camera carries <code>w=0.88</code>. Conflicting records are resolved by computing maximum posterior marginal belief.
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div>
          <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16 }}>
            <strong style={{ color: 'var(--color-primary)' }}>Query Decomposition &amp; Federation</strong>: When a global query arrives at the mediator, it is decomposed into source-specific sub-queries using the GAV mapping. Each wrapper executes its own query independently. (IIA-1, slides 19-22)
          </div>
          <div className="card">
            <div style={{ fontWeight: 700, marginBottom: 14, color: 'var(--text-primary)' }}>
              Example: Global query for vehicle "UP32AB1234"
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <div style={{ background: 'var(--color-primary-glow)', border: '1px solid rgba(99,102,241,0.3)', borderRadius: 8, padding: '10px 14px' }}>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>GLOBAL QUERY (Mediator input)</div>
                <code style={{ color: 'var(--color-primary)', fontSize: 13 }}>SELECT * FROM global_vehicle WHERE registration_number = 'UP32AB1234'</code>
              </div>
              <div style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: 20 }}>↓ Decompose via GAV mapping</div>
              {Object.entries({
                capture:      { key: 'plate_number',       table: 'vehicle_capture' },
                insurance:    { key: 'registration_id',    table: 'insurance_records' },
                registration: { key: 'vehicle_reg_no',     table: 'vehicle_registration' },
                theft:        { key: 'vehicle_identifier', table: 'vehicle_security_records' },
                ministry:     { key: 'vehicle_ref',        table: 'transport_reports' },
              }).map(([src, info]) => (
                <div key={src} style={{ background: `${SOURCE_COLORS[src]}12`, border: `1px solid ${SOURCE_COLORS[src]}33`, borderRadius: 8, padding: '10px 14px' }}>
                  <div style={{ fontSize: 11, color: SOURCE_COLORS[src], fontWeight: 700, marginBottom: 4, textTransform: 'uppercase' }}>{src}.db → Wrapper</div>
                  <code style={{ color: '#94a3b8', fontSize: 12 }}>
                    SELECT * FROM <span style={{ color: SOURCE_COLORS[src] }}>{info.table}</span> WHERE <span style={{ color: SOURCE_COLORS[src] }}>{info.key}</span> = 'UP32AB1234'
                  </code>
                </div>
              ))}
              <div style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: 20 }}>↓ Merge + Conflict Check</div>
              <div style={{ background: 'var(--color-success-dim)', border: '1px solid rgba(34,197,94,0.3)', borderRadius: 8, padding: '10px 14px' }}>
                <div style={{ fontSize: 11, color: 'var(--color-success)', fontWeight: 700, marginBottom: 4 }}>UNIFIED VEHICLE VIEW (output)</div>
                <code style={{ color: '#94a3b8', fontSize: 12 }}>{'{ registration_number, vehicle, registration, insurance, security, ministry, conflicts, overall_status }'}</code>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
