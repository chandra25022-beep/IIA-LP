import { useState, useRef } from 'react';
import { api } from '../api';
import UnifiedVehicleView from '../components/UnifiedVehicleView';

const PIPELINE_STEPS = [
  { key: 'image_loaded',         label: 'Image Loaded',                icon: '📷' },
  { key: 'vehicle_detected',     label: 'Vehicle Detection (YOLOv8)',   icon: '🚗' },
  { key: 'color_detected',       label: 'Color Detection (HSV)',        icon: '🎨' },
  { key: 'plate_region_detected',label: 'Plate Region Detection',       icon: '🔲' },
  { key: 'ocr_run',              label: 'OCR — License Plate Only',     icon: '📖' },
  { key: 'normalized',           label: 'Plate Normalized',             icon: '✓'  },
];

const TIER_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  AUTO_MERGE:       { bg: 'rgba(34,197,94,0.12)',  text: '#22c55e', border: 'rgba(34,197,94,0.3)' },
  UNCERTAIN_REVIEW: { bg: 'rgba(251,191,36,0.12)', text: '#f59e0b', border: 'rgba(251,191,36,0.3)' },
  REJECT:           { bg: 'rgba(239,68,68,0.10)',  text: '#ef4444', border: 'rgba(239,68,68,0.3)' },
  EXACT_MATCH:      { bg: 'rgba(34,197,94,0.15)',  text: '#16a34a', border: 'rgba(34,197,94,0.4)' },
};

const METHOD_OPTIONS = [
  { value: 'ensemble', label: 'Ensemble (Recommended)' },
  { value: 'jaro_winkler', label: 'Jaro-Winkler Only' },
  { value: 'edit_distance', label: 'Edit Distance Only' },
  { value: 'qgram_jaccard', label: 'Q-Gram Jaccard Only' },
  { value: 'ocr_confusion', label: 'OCR Confusion Only' },
];

export default function ScanVehicle() {
  const [scanResult, setScanResult] = useState<any>(null);
  const [vehicleData, setVehicleData] = useState<any>(null);
  const [matchResult, setMatchResult] = useState<any>(null);
  const [cleanseResult, setCleanseResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<'scan' | 'match' | 'cleanse'>('scan');
  const [manualPlate, setManualPlate] = useState('');
  const [matchMethod, setMatchMethod] = useState('ensemble');
  const fileRef = useRef<HTMLInputElement>(null);

  const processFile = async (file: File) => {
    setLoading(true);
    setError('');
    setScanResult(null);
    setVehicleData(null);
    setMatchResult(null);
    setCleanseResult(null);
    setPreviewUrl(URL.createObjectURL(file));
    try {
      const scan = await api.scanVehicle(file);
      setScanResult(scan);
      if (scan.plate) {
        // Auto-run approximate match
        const matchRes = await api.approximateMatch(scan.plate, matchMethod);
        setMatchResult(matchRes);
        // Auto-run cleansing with contextual data
        const cleanseRes = await api.cleanseRecord(
          scan.plate,
          scan.detected_color,
          scan.vehicle_type
        );
        setCleanseResult(cleanseRes);
        // Integrate with cleansed plate
        const finalPlate = cleanseRes?.cleansed_plate || scan.plate;
        const vehicle = await api.getVehicle(finalPlate);
        setVehicleData(vehicle);
      }
    } catch (e) {
      setError('Scan failed. Please ensure the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleManualMatch = async () => {
    if (!manualPlate.trim()) return;
    setLoading(true);
    setError('');
    setMatchResult(null);
    setCleanseResult(null);
    setVehicleData(null);
    try {
      const matchRes = await api.approximateMatch(manualPlate, matchMethod);
      setMatchResult(matchRes);
      const cleanseRes = await api.cleanseRecord(manualPlate);
      setCleanseResult(cleanseRes);
      if (cleanseRes?.cleansed_plate) {
        const vehicle = await api.getVehicle(cleanseRes.cleansed_plate);
        setVehicleData(vehicle);
      }
    } catch (e) {
      setError('Match failed. Please ensure the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file?.type.startsWith('image/')) processFile(file);
  };

  const reset = () => {
    setScanResult(null);
    setVehicleData(null);
    setMatchResult(null);
    setCleanseResult(null);
    setPreviewUrl(null);
    setError('');
    setManualPlate('');
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Scan & <span>Match</span> Vehicle</h1>
        <p className="page-subtitle">
          Upload vehicle image or enter noisy plate → ANPR scan → Approximate Matching → Data Cleansing → Integrated View
        </p>
      </div>

      {/* Tab Switcher */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 20, background: 'var(--color-surface)', borderRadius: 10, padding: 4, border: '1px solid var(--color-border)' }}>
        <button onClick={() => setActiveTab('scan')} style={{
          flex: 1, padding: '10px 16px', borderRadius: 8, border: 'none', cursor: 'pointer',
          fontSize: 13, fontWeight: 600, transition: 'all 0.2s',
          background: activeTab === 'scan' ? 'var(--color-primary)' : 'transparent',
          color: activeTab === 'scan' ? '#fff' : 'var(--text-muted)',
        }}>📷 Image Scan</button>
        <button onClick={() => setActiveTab('match')} style={{
          flex: 1, padding: '10px 16px', borderRadius: 8, border: 'none', cursor: 'pointer',
          fontSize: 13, fontWeight: 600, transition: 'all 0.2s',
          background: activeTab === 'match' ? 'var(--color-primary)' : 'transparent',
          color: activeTab === 'match' ? '#fff' : 'var(--text-muted)',
        }}>🔍 Approximate Match</button>
        <button onClick={() => setActiveTab('cleanse')} style={{
          flex: 1, padding: '10px 16px', borderRadius: 8, border: 'none', cursor: 'pointer',
          fontSize: 13, fontWeight: 600, transition: 'all 0.2s',
          background: activeTab === 'cleanse' ? 'var(--color-primary)' : 'transparent',
          color: activeTab === 'cleanse' ? '#fff' : 'var(--text-muted)',
        }}>🧹 Data Cleansing</button>
      </div>

      {/* ─── TAB: Image Scan ─── */}
      {activeTab === 'scan' && (
        <div className="grid-2" style={{ marginBottom: 24 }}>
          <div>
            <div
              className={`upload-zone${dragging ? ' dragging' : ''}`}
              onClick={() => fileRef.current?.click()}
              onDragOver={e => { e.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onDrop={handleDrop}
            >
              {previewUrl ? (
                <div style={{ position: 'relative' }}>
                  <img src={previewUrl} alt="Uploaded vehicle" style={{ maxWidth: '100%', maxHeight: 220, borderRadius: 8, objectFit: 'contain' }} />
                  <button onClick={e => { e.stopPropagation(); reset(); }} style={{
                    position: 'absolute', top: -8, right: -8, background: 'var(--color-danger)',
                    border: 'none', borderRadius: '50%', width: 24, height: 24,
                    color: '#fff', fontSize: 12, cursor: 'pointer',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }} title="Clear">✕</button>
                </div>
              ) : (
                <>
                  <div className="upload-zone-icon">📤</div>
                  <h3>Upload Vehicle Image</h3>
                  <p>Drag &amp; drop or click to select<br />JPG, PNG, WebP supported</p>
                  <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 8 }}>
                    Full pipeline: ANPR → Approximate Match → Cleanse → Integrate
                  </p>
                </>
              )}
              <input type="file" ref={fileRef} style={{ display: 'none' }} accept="image/*"
                onChange={e => e.target.files?.[0] && processFile(e.target.files[0])} />
            </div>
            <div style={{ marginTop: 12, padding: '10px 14px', background: 'var(--color-surface)', borderRadius: 10, border: '1px solid var(--color-border)', fontSize: 12, color: 'var(--text-muted)' }}>
              💡 Want to test with a noisy plate? Use the <strong>Approximate Match</strong> tab to enter a plate manually.
            </div>
          </div>

          {/* ANPR Pipeline Status */}
          <div>
            <div className="card-title" style={{ marginBottom: 12 }}>ANPR Pipeline</div>
            <div className="pipeline">
              {PIPELINE_STEPS.map(step => {
                const isDone = scanResult?.pipeline_stages?.[step.key] === true;
                const isActive = loading;
                return (
                  <div key={step.key} className={`pipeline-step${isDone ? ' done' : isActive ? ' active' : ''}`}>
                    <div className="pipeline-dot">{isDone ? '✓' : step.icon}</div>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 600 }}>{step.label}</div>
                      {step.key === 'ocr_run' && scanResult?.raw_ocr && (
                        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                          Extracted: <code style={{ color: 'var(--color-primary)' }}>{scanResult.raw_ocr}</code>
                          {' '}({(scanResult.ocr_confidence * 100).toFixed(0)}% confidence)
                        </div>
                      )}
                      {step.key === 'normalized' && scanResult?.plate && (
                        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                          <code style={{ color: 'var(--color-success)', fontSize: 13 }}>{scanResult.plate}</code>
                          {' '}{scanResult.is_valid_format ? '✓ Valid Indian plate format' : '⚠ Non-standard format'}
                        </div>
                      )}
                      {step.key === 'vehicle_detected' && scanResult?.vehicle_type && (
                        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                          {scanResult.vehicle_type} · Confidence: {(scanResult.detection_confidence * 100).toFixed(0)}%
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {scanResult?.detection_method && (
              <div style={{ marginTop: 12, padding: '8px 14px', background: 'var(--color-surface-2)', borderRadius: 8, fontSize: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ color: 'var(--text-muted)' }}>Detection Strategy: </span>
                <span style={{ color: 'var(--color-primary)', fontWeight: 700, background: 'var(--color-primary-glow)', padding: '2px 8px', borderRadius: 4, fontFamily: 'JetBrains Mono, monospace' }}>
                  {scanResult.detection_method}
                </span>
              </div>
            )}

            {scanResult?.detected_color && (
              <div style={{ marginTop: 8, padding: '8px 14px', background: 'var(--color-surface-2)', borderRadius: 8, fontSize: 12 }}>
                <span style={{ color: 'var(--text-muted)' }}>Detected color: </span>
                <strong>{scanResult.detected_color}</strong>
              </div>
            )}

            {scanResult?.candidate_plates?.length > 1 && (
              <div style={{ marginTop: 12, padding: '10px 14px', background: 'var(--color-surface-2)', borderRadius: 8, border: '1px solid var(--color-border)' }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 6 }}>
                  Alternative Plate Candidates ({scanResult.candidate_plates.length})
                </div>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  {scanResult.candidate_plates.map((cand: any, i: number) => (
                    <button key={i} onClick={async () => {
                      setLoading(true);
                      try {
                        const v = await api.getVehicle(cand.plate);
                        setVehicleData(v);
                      } finally { setLoading(false); }
                    }} style={{
                      background: cand.plate === scanResult.plate ? 'var(--color-primary)' : 'var(--color-surface)',
                      color: cand.plate === scanResult.plate ? '#fff' : 'var(--text-primary)',
                      border: '1px solid var(--color-border)', borderRadius: 6, padding: '4px 10px',
                      fontSize: 11, fontFamily: 'JetBrains Mono, monospace', cursor: 'pointer',
                    }}>{cand.plate} ({(cand.confidence * 100).toFixed(0)}%)</button>
                  ))}
                </div>
              </div>
            )}

            {scanResult?.error && (
              <div style={{ marginTop: 12, color: 'var(--color-warning)', fontSize: 12, background: 'var(--color-warning-dim)', padding: '8px 12px', borderRadius: 8 }}>⚠ {scanResult.error}</div>
            )}
            {scanResult && !scanResult.plate && !scanResult.error && (
              <div style={{ marginTop: 12, padding: '10px 14px', background: 'rgba(251,191,36,0.1)', borderRadius: 8, fontSize: 12, color: 'var(--color-warning)', border: '1px solid rgba(251,191,36,0.2)' }}>
                ⚠ Could not extract a license plate. Try a clearer photo.
              </div>
            )}
          </div>
        </div>
      )}

      {/* ─── TAB: Approximate Match ─── */}
      {activeTab === 'match' && (
        <div style={{ marginBottom: 24 }}>
          <div style={{ display: 'flex', gap: 12, marginBottom: 16, alignItems: 'flex-end' }}>
            <div style={{ flex: 1 }}>
              <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>
                Enter Noisy / Scanned Plate Number
              </label>
              <input type="text" placeholder="e.g. UP32A81234, RJ070P556B, TN07BC66S5"
                value={manualPlate} onChange={e => setManualPlate(e.target.value.toUpperCase())}
                onKeyDown={e => e.key === 'Enter' && handleManualMatch()}
                style={{
                  width: '100%', padding: '10px 14px', borderRadius: 8,
                  border: '1px solid var(--color-border)', background: 'var(--color-surface)',
                  color: 'var(--text-primary)', fontSize: 16, fontFamily: 'JetBrains Mono, monospace',
                  letterSpacing: 2,
                }}
              />
            </div>
            <div>
              <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>
                Algorithm
              </label>
              <select value={matchMethod} onChange={e => setMatchMethod(e.target.value)}
                style={{
                  padding: '10px 14px', borderRadius: 8, border: '1px solid var(--color-border)',
                  background: 'var(--color-surface)', color: 'var(--text-primary)', fontSize: 13,
                }}>
                {METHOD_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </div>
            <button onClick={handleManualMatch} disabled={loading || !manualPlate.trim()}
              style={{
                padding: '10px 24px', borderRadius: 8, border: 'none', cursor: 'pointer',
                background: 'var(--color-primary)', color: '#fff', fontWeight: 700, fontSize: 14,
                opacity: loading || !manualPlate.trim() ? 0.5 : 1,
              }}>
              {loading ? '⏳ Matching…' : '🔍 Find Matches'}
            </button>
          </div>

          {/* Demo noisy plates for quick testing */}
          <div style={{ marginBottom: 16, padding: '10px 14px', background: 'var(--color-surface)', borderRadius: 10, border: '1px solid var(--color-border)' }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', marginBottom: 6, textTransform: 'uppercase' }}>
              Quick Test — Click a noisy plate:
            </div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {[
                { plate: 'UP32A81234', desc: '8↔B confusion' },
                { plate: 'RJ070P5566', desc: '0↔O confusion' },
                { plate: 'TN07BC66S5', desc: 'S↔5, 6↔G confusion' },
                { plate: 'DL0IGH3456', desc: '0↔O, I↔1 confusion' },
                { plate: 'MH02EF90I2', desc: 'I↔1 confusion' },
                { plate: 'UP32CD567B', desc: 'B↔8 confusion' },
                { plate: 'HR26PQ77B8', desc: 'B↔8 swap' },
              ].map(({ plate, desc }) => (
                <button key={plate} onClick={() => { setManualPlate(plate); }}
                  style={{
                    background: 'var(--color-surface-2)', border: '1px solid var(--color-border)',
                    borderRadius: 6, padding: '4px 10px', fontSize: 11, cursor: 'pointer',
                    color: 'var(--text-primary)', fontFamily: 'JetBrains Mono, monospace',
                  }} title={desc}>
                  {plate} <span style={{ color: 'var(--text-muted)', fontSize: 10 }}>({desc})</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ─── TAB: Data Cleansing ─── */}
      {activeTab === 'cleanse' && cleanseResult && (
        <div style={{ marginBottom: 24 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
            {/* Cleansing Summary */}
            <div style={{ padding: 16, background: 'var(--color-surface)', borderRadius: 12, border: '1px solid var(--color-border)' }}>
              <div className="card-title" style={{ marginBottom: 12 }}>🧹 Cleansing Result</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 10, color: 'var(--text-muted)', marginBottom: 2 }}>NOISY INPUT</div>
                  <div style={{ fontFamily: 'JetBrains Mono', fontSize: 18, color: 'var(--color-danger)', background: 'rgba(239,68,68,0.1)', padding: '6px 14px', borderRadius: 8 }}>
                    {cleanseResult.original_input}
                  </div>
                </div>
                <div style={{ fontSize: 24, color: 'var(--text-muted)' }}>→</div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 10, color: 'var(--text-muted)', marginBottom: 2 }}>CLEANSED</div>
                  <div style={{ fontFamily: 'JetBrains Mono', fontSize: 18, color: 'var(--color-success)', background: 'rgba(34,197,94,0.1)', padding: '6px 14px', borderRadius: 8 }}>
                    {cleanseResult.cleansed_plate}
                  </div>
                </div>
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                <div>Method: <strong>{cleanseResult.cleansing_method}</strong></div>
                <div>Confidence: <strong>{(cleanseResult.cleansing_confidence * 100).toFixed(1)}%</strong></div>
                <div>Anomalies Fixed: <strong>{cleanseResult.anomaly_count}</strong></div>
                <div>Valid Format: {cleanseResult.is_valid_format ? '✅ Yes' : '❌ No'}</div>
              </div>
            </div>

            {/* Anomalies Detected */}
            <div style={{ padding: 16, background: 'var(--color-surface)', borderRadius: 12, border: '1px solid var(--color-border)' }}>
              <div className="card-title" style={{ marginBottom: 12 }}>⚠ Anomalies Detected ({cleanseResult.anomaly_count})</div>
              {cleanseResult.anomalies_detected?.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {cleanseResult.anomalies_detected.map((a: any, i: number) => (
                    <div key={i} style={{
                      padding: '6px 10px', borderRadius: 6, fontSize: 11,
                      background: a.type === 'OCR_CHAR_CONFUSION' ? 'rgba(251,191,36,0.1)' : 'rgba(239,68,68,0.08)',
                      border: `1px solid ${a.type === 'OCR_CHAR_CONFUSION' ? 'rgba(251,191,36,0.2)' : 'rgba(239,68,68,0.15)'}`,
                    }}>
                      <span style={{ fontWeight: 700, color: a.type === 'OCR_CHAR_CONFUSION' ? '#f59e0b' : '#ef4444' }}>
                        {a.type === 'OCR_CHAR_CONFUSION' ? '🔤' : '📋'} {a.type}
                      </span>
                      <div style={{ color: 'var(--text-muted)', marginTop: 2 }}>{a.description}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>No anomalies detected — data is clean.</div>
              )}
            </div>
          </div>

          {/* Audit Trail */}
          {cleanseResult.cleansing_audit_trail?.length > 0 && (
            <div style={{ padding: 16, background: 'var(--color-surface)', borderRadius: 12, border: '1px solid var(--color-border)', marginBottom: 16 }}>
              <div className="card-title" style={{ marginBottom: 12 }}>📋 Cleansing Audit Trail</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {cleanseResult.cleansing_audit_trail.map((step: any, i: number) => (
                  <div key={i} style={{
                    display: 'flex', alignItems: 'flex-start', gap: 10,
                    padding: '8px 12px', borderRadius: 8, background: 'var(--color-surface-2)',
                  }}>
                    <div style={{
                      minWidth: 24, height: 24, borderRadius: '50%',
                      background: 'var(--color-primary)', color: '#fff',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 12, fontWeight: 700,
                    }}>{step.step}</div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--color-primary)' }}>{step.action}</div>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{step.description}</div>
                      {step.before && step.after && (
                        <div style={{ marginTop: 4, fontFamily: 'JetBrains Mono', fontSize: 11 }}>
                          <span style={{ color: 'var(--color-danger)' }}>{step.before}</span>
                          {' → '}
                          <span style={{ color: 'var(--color-success)' }}>{step.after}</span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ─── Approximate Match Results ─── */}
      {matchResult && (activeTab === 'match' || activeTab === 'scan') && (
        <div style={{ marginBottom: 24, padding: 16, background: 'var(--color-surface)', borderRadius: 12, border: '1px solid var(--color-border)' }}>
          <div className="card-title" style={{ marginBottom: 4 }}>
            🔍 Approximate Matches for <code style={{ color: 'var(--color-primary)' }}>{matchResult.query_plate}</code>
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 12 }}>
            Algorithm: <strong>{matchResult.matching_method}</strong> · Found: <strong>{matchResult.total_candidates_found}</strong> candidates ·
            Auto-merge: <span style={{ color: '#22c55e' }}>{matchResult.decision_summary?.auto_merge_count ?? 0}</span> ·
            Review: <span style={{ color: '#f59e0b' }}>{matchResult.decision_summary?.uncertain_review_count ?? 0}</span> ·
            Reject: <span style={{ color: '#ef4444' }}>{matchResult.decision_summary?.reject_count ?? 0}</span>
          </div>

          {matchResult.matches?.length > 0 ? (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                    <th style={{ textAlign: 'left', padding: '6px 8px', color: 'var(--text-muted)', fontSize: 10, fontWeight: 700 }}>PLATE</th>
                    <th style={{ textAlign: 'center', padding: '6px 8px', color: 'var(--text-muted)', fontSize: 10, fontWeight: 700 }}>P(MATCH)</th>
                    <th style={{ textAlign: 'center', padding: '6px 8px', color: 'var(--text-muted)', fontSize: 10, fontWeight: 700 }}>DECISION</th>
                    <th style={{ textAlign: 'center', padding: '6px 8px', color: 'var(--text-muted)', fontSize: 10, fontWeight: 700 }}>JARO-WINKLER</th>
                    <th style={{ textAlign: 'center', padding: '6px 8px', color: 'var(--text-muted)', fontSize: 10, fontWeight: 700 }}>EDIT SIM</th>
                    <th style={{ textAlign: 'center', padding: '6px 8px', color: 'var(--text-muted)', fontSize: 10, fontWeight: 700 }}>OCR CONF</th>
                    <th style={{ textAlign: 'center', padding: '6px 8px', color: 'var(--text-muted)', fontSize: 10, fontWeight: 700 }}>JACCARD</th>
                    <th style={{ textAlign: 'left', padding: '6px 8px', color: 'var(--text-muted)', fontSize: 10, fontWeight: 700 }}>SOURCES</th>
                    <th style={{ textAlign: 'center', padding: '6px 8px', color: 'var(--text-muted)', fontSize: 10, fontWeight: 700 }}>ACTION</th>
                  </tr>
                </thead>
                <tbody>
                  {matchResult.matches.map((m: any, i: number) => {
                    const tierStyle = TIER_COLORS[m.decision_tier] || TIER_COLORS.REJECT;
                    return (
                      <tr key={i} style={{ borderBottom: '1px solid var(--color-border)', background: i === 0 ? tierStyle.bg : 'transparent' }}>
                        <td style={{ padding: '8px', fontFamily: 'JetBrains Mono', fontWeight: 700, fontSize: 13 }}>{m.plate}</td>
                        <td style={{ padding: '8px', textAlign: 'center', fontWeight: 700, color: tierStyle.text }}>
                          {(m.match_probability * 100).toFixed(1)}%
                        </td>
                        <td style={{ padding: '8px', textAlign: 'center' }}>
                          <span style={{
                            padding: '2px 8px', borderRadius: 4, fontSize: 10, fontWeight: 700,
                            background: tierStyle.bg, color: tierStyle.text, border: `1px solid ${tierStyle.border}`,
                          }}>{m.decision_tier}</span>
                        </td>
                        <td style={{ textAlign: 'center', padding: '8px', fontFamily: 'JetBrains Mono', fontSize: 11 }}>{m.all_metrics?.jaro_winkler?.toFixed(3)}</td>
                        <td style={{ textAlign: 'center', padding: '8px', fontFamily: 'JetBrains Mono', fontSize: 11 }}>{m.all_metrics?.normalized_edit?.toFixed(3)}</td>
                        <td style={{ textAlign: 'center', padding: '8px', fontFamily: 'JetBrains Mono', fontSize: 11 }}>{m.all_metrics?.ocr_confusion?.toFixed(3)}</td>
                        <td style={{ textAlign: 'center', padding: '8px', fontFamily: 'JetBrains Mono', fontSize: 11 }}>{m.all_metrics?.jaccard_qgrams?.toFixed(3)}</td>
                        <td style={{ padding: '8px' }}>
                          <div style={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
                            {m.sources?.map((s: string) => (
                              <span key={s} style={{ fontSize: 9, padding: '1px 5px', borderRadius: 3, background: 'var(--color-surface-2)', color: 'var(--text-muted)' }}>{s}</span>
                            ))}
                          </div>
                        </td>
                        <td style={{ padding: '8px', textAlign: 'center' }}>
                          <button onClick={async () => {
                            setLoading(true);
                            try {
                              const v = await api.getVehicle(m.plate);
                              setVehicleData(v);
                            } finally { setLoading(false); }
                          }} style={{
                            padding: '3px 10px', borderRadius: 4, border: '1px solid var(--color-border)',
                            background: 'var(--color-surface)', cursor: 'pointer', fontSize: 10, color: 'var(--color-primary)',
                          }}>View</button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div style={{ fontSize: 12, color: 'var(--text-muted)', textAlign: 'center', padding: 20 }}>No approximate matches found.</div>
          )}

          {/* Algorithm Justification */}
          {matchResult.algorithm_justification && (
            <div style={{ marginTop: 12, padding: '10px 14px', borderRadius: 8, background: 'var(--color-surface-2)', fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.5 }}>
              <strong>Algorithm Justification:</strong> {matchResult.algorithm_justification}
            </div>
          )}
        </div>
      )}

      {error && (
        <div style={{
          color: 'var(--color-danger)', background: 'var(--color-danger-dim)',
          border: '1px solid rgba(239,68,68,0.3)', borderRadius: 12, padding: '14px 18px', marginBottom: 20,
        }}>{error}</div>
      )}

      {loading && (
        <div className="loading-center"><div className="spinner" /><span>Processing…</span></div>
      )}

      {/* Global vehicle view */}
      {vehicleData && !loading && <UnifiedVehicleView data={vehicleData} />}
    </div>
  );
}
