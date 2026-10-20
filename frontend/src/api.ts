// API base URL — reads from .env file (VITE_API_BASE)
// Change .env to your LAN IP (e.g. http://192.168.1.105:8000) when sharing with friends
const API_BASE = (import.meta.env.VITE_API_BASE as string) || 'http://localhost:8000';

export const api = {
  // Vehicle endpoints
  getVehicle: async (plate: string) => {
    const res = await fetch(`${API_BASE}/api/vehicle/${plate}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },
  searchVehicle: async (plate: string) => {
    const res = await fetch(`${API_BASE}/api/vehicle/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ registration_number: plate }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },
  scanVehicle: async (file: File) => {
    const fd = new FormData();
    fd.append('file', file);
    const res = await fetch(`${API_BASE}/api/vehicle/scan`, { method: 'POST', body: fd });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },
  getVehicleHistory: async (plate: string) => {
    const res = await fetch(`${API_BASE}/api/vehicle/${plate}/history`);
    return res.json();
  },
  getVehicleInsurance: async (plate: string) => {
    const res = await fetch(`${API_BASE}/api/vehicle/${plate}/insurance`);
    return res.json();
  },
  getVehicleSecurity: async (plate: string) => {
    const res = await fetch(`${API_BASE}/api/vehicle/${plate}/security`);
    return res.json();
  },
  getVehicleReports: async (plate: string) => {
    const res = await fetch(`${API_BASE}/api/vehicle/${plate}/reports`);
    return res.json();
  },

  // ─── Phase 2: Approximate Matching & Data Cleansing ────────────────
  approximateMatch: async (noisyPlate: string, method: string = 'ensemble', maxCandidates: number = 10) => {
    const res = await fetch(`${API_BASE}/api/vehicle/approximate-match`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        noisy_plate: noisyPlate,
        matching_method: method,
        max_candidates: maxCandidates,
        sensor_confidence: 0.85,
      }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },

  cleanseRecord: async (noisyPlate: string, detectedColor?: string, detectedType?: string, detectedMake?: string) => {
    const res = await fetch(`${API_BASE}/api/vehicle/cleanse`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        noisy_plate: noisyPlate,
        detected_color: detectedColor || null,
        detected_vehicle_type: detectedType || null,
        detected_make: detectedMake || null,
        sensor_confidence: 0.85,
      }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },

  scanAndMatch: async (file: File) => {
    const fd = new FormData();
    fd.append('file', file);
    const res = await fetch(`${API_BASE}/api/vehicle/scan-and-match`, { method: 'POST', body: fd });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },

  // Reports
  createReport: async (data: { vehicle_ref: string; report_type: string; reason: string; severity: string; submitted_by: string }) => {
    const res = await fetch(`${API_BASE}/api/reports/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return res.json();
  },
  getAllReports: async (skip = 0, limit = 50) => {
    const res = await fetch(`${API_BASE}/api/reports/all?skip=${skip}&limit=${limit}`);
    return res.json();
  },
  getReportStats: async () => {
    const res = await fetch(`${API_BASE}/api/reports/statistics`);
    return res.json();
  },

  // Integration
  getStatistics: async () => {
    const res = await fetch(`${API_BASE}/api/statistics`);
    return res.json();
  },
  getDataSources: async () => {
    const res = await fetch(`${API_BASE}/api/data-sources`);
    return res.json();
  },
  getIntegrationSchema: async () => {
    const res = await fetch(`${API_BASE}/api/integration/schema`);
    return res.json();
  },
  getDemoVehicles: async () => {
    const res = await fetch(`${API_BASE}/api/demo-vehicles`);
    return res.json();
  },

  // SQL Query
  sqlQuery: async (query: string, database: string = 'all') => {
    const res = await fetch(`${API_BASE}/api/sql-query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, database }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  },
  sqlWrite: async (query: string, database: string) => {
    const res = await fetch(`${API_BASE}/api/sql-write`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, database }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  },
  getSqlTables: async () => {
    const res = await fetch(`${API_BASE}/api/sql-query/tables`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },
  getDbOwnership: async () => {
    const res = await fetch(`${API_BASE}/api/sql-write/ownership`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },

  // Week 6-8: Indexing & Uncertainty API
  getIndexingStats: async () => {
    const res = await fetch(`${API_BASE}/api/indexing/stats`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },
  searchIndexCandidates: async (query: string, method: string = 'prefix_index', threshold: number = 0.4) => {
    const res = await fetch(`${API_BASE}/api/indexing/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, method, threshold }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },
  compareStringMetrics: async (string1: string, string2: string) => {
    const res = await fetch(`${API_BASE}/api/indexing/metrics`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ string1, string2 }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },
  evaluateUncertainty: async (query_plate: string, candidate_plate: string, sensor_confidence: number = 0.9) => {
    const res = await fetch(`${API_BASE}/api/uncertainty/evaluate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query_plate, candidate_plate, sensor_confidence }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },
};
