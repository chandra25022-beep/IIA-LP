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

type CrudAction = 'SELECT' | 'INSERT' | 'UPDATE' | 'DELETE';

interface CrudTemplate {
  action: CrudAction;
  db: string;
  label: string;
  table: string;
  keyCol: string;
  sql: string;
  sampleKey: string;
}

const CRUD_TEMPLATES: CrudTemplate[] = [
  // ── REGISTRATION ──
  {
    action: 'INSERT',
    db: 'registration',
    label: '➕ Registration: Add New Vehicle',
    table: 'vehicle_registration',
    keyCol: 'vehicle_reg_no',
    sampleKey: 'DL09VIVA2026',
    sql: `-- INSERT a new vehicle into RTO Registration Database (Node A)
INSERT INTO vehicle_registration (
  vehicle_reg_no, owner_name, owner_contact, owner_address,
  registration_date, manufacturer, model_name, vehicle_class,
  registered_color, fuel_type, registration_status, rto_office
) VALUES (
  'DL09VIVA2026',
  'Prof. Anupama Ray',
  '+91-98765-43210',
  'IIIT Delhi Campus, Okhla Phase 3',
  '2026-10-21',
  'Hyundai',
  'Creta 1.6 VTVT',
  'SUV / Private',
  'BLACK',
  'PETROL',
  'ACTIVE',
  'DL-09 Janakpuri, Delhi'
);`
  },
  {
    action: 'UPDATE',
    db: 'registration',
    label: '✏️ Registration: Modify Vehicle Details',
    table: 'vehicle_registration',
    keyCol: 'vehicle_reg_no',
    sampleKey: 'DL09VIVA2026',
    sql: `-- UPDATE an existing vehicle in RTO Registration Database (Node A)
UPDATE vehicle_registration
SET
  owner_name = 'Prof. Anupama Ray (HOD IIITD)',
  registered_color = 'OBSIDIAN_BLACK',
  registration_status = 'ACTIVE'
WHERE vehicle_reg_no = 'DL09VIVA2026';`
  },
  {
    action: 'DELETE',
    db: 'registration',
    label: '🗑️ Registration: Delete Vehicle Record',
    table: 'vehicle_registration',
    keyCol: 'vehicle_reg_no',
    sampleKey: 'DL09VIVA2026',
    sql: `-- DELETE vehicle record from RTO Registration Database (Node A)
DELETE FROM vehicle_registration
WHERE vehicle_reg_no = 'DL09VIVA2026';`
  },

  // ── INSURANCE ──
  {
    action: 'INSERT',
    db: 'insurance',
    label: '➕ Insurance: Add Policy Record',
    table: 'insurance_records',
    keyCol: 'registration_id',
    sampleKey: 'DL09VIVA2026',
    sql: `-- INSERT an insurance policy into National Insurance Registry (Node A)
INSERT INTO insurance_records (
  registration_id, insurer_name, policy_number,
  policy_start_date, policy_expiry_date, insurance_status,
  vehicle_category, premium_amount, nominee_name, coverage_type, claim_count
) VALUES (
  'DL09VIVA2026',
  'Bajaj Allianz General Insurance',
  'BAJAJ-LUX-2026-001',
  '2026-10-21',
  '2028-10-21',
  'ACTIVE',
  'Private Car',
  38500.0,
  'Rohan Ray',
  'Comprehensive Zero Dep',
  0
);`
  },
  {
    action: 'UPDATE',
    db: 'insurance',
    label: '✏️ Insurance: Update Policy Status / Expiry',
    table: 'insurance_records',
    keyCol: 'registration_id',
    sampleKey: 'DL09VIVA2026',
    sql: `-- UPDATE insurance status in National Insurance Registry (Node A)
UPDATE insurance_records
SET
  insurance_status = 'EXPIRED',
  policy_expiry_date = '2026-01-01',
  claim_count = 1
WHERE registration_id = 'DL09VIVA2026';`
  },
  {
    action: 'DELETE',
    db: 'insurance',
    label: '🗑️ Insurance: Cancel / Delete Policy',
    table: 'insurance_records',
    keyCol: 'registration_id',
    sampleKey: 'DL09VIVA2026',
    sql: `-- DELETE insurance policy from National Insurance Registry (Node A)
DELETE FROM insurance_records
WHERE registration_id = 'DL09VIVA2026';`
  },

  // ── THEFT / SECURITY ──
  {
    action: 'INSERT',
    db: 'theft',
    label: '➕ Theft: File Stolen / Security Report',
    table: 'vehicle_security_records',
    keyCol: 'vehicle_identifier',
    sampleKey: 'DL09VIVA2026',
    sql: `-- INSERT theft / wanted record into Police Crime Bureau (Node B)
INSERT INTO vehicle_security_records (
  vehicle_identifier, case_type, case_status,
  reported_date, police_reference, shredding_status, fir_number
) VALUES (
  'DL09VIVA2026',
  'THEFT',
  'OPEN',
  '2026-10-21',
  'PS-OKHLA-2026',
  'NOT_SCRAPPED',
  'FIR-DEL-9901'
);`
  },
  {
    action: 'UPDATE',
    db: 'theft',
    label: '✏️ Theft: Clear / Close Security Case',
    table: 'vehicle_security_records',
    keyCol: 'vehicle_identifier',
    sampleKey: 'DL09VIVA2026',
    sql: `-- UPDATE theft record to CLOSED / CLEARED (Node B)
UPDATE vehicle_security_records
SET
  case_status = 'CLOSED',
  case_type = 'CLEARED'
WHERE vehicle_identifier = 'DL09VIVA2026';`
  },
  {
    action: 'DELETE',
    db: 'theft',
    label: '🗑️ Theft: Remove Security Record',
    table: 'vehicle_security_records',
    keyCol: 'vehicle_identifier',
    sampleKey: 'DL09VIVA2026',
    sql: `-- DELETE security record from Police Crime Bureau (Node B)
DELETE FROM vehicle_security_records
WHERE vehicle_identifier = 'DL09VIVA2026';`
  },

  // ── MINISTRY ──
  {
    action: 'INSERT',
    db: 'ministry',
    label: '➕ Ministry: Issue Violation Report',
    table: 'transport_reports',
    keyCol: 'vehicle_ref',
    sampleKey: 'DL09VIVA2026',
    sql: `-- INSERT transport violation report into Ministry DB (Node B)
INSERT INTO transport_reports (
  vehicle_ref, report_type, report_date,
  reason, severity, report_status, action_taken
) VALUES (
  'DL09VIVA2026',
  'UNINSURED_VEHICLE',
  '2026-10-21',
  'Vehicle spotted operating on expressway without valid insurance',
  'HIGH',
  'PENDING',
  'Electronic challan issued to owner'
);`
  },
  {
    action: 'UPDATE',
    db: 'ministry',
    label: '✏️ Ministry: Mark Report Actioned / Resolved',
    table: 'transport_reports',
    keyCol: 'vehicle_ref',
    sampleKey: 'DL09VIVA2026',
    sql: `-- UPDATE ministry report status to ACTIONED (Node B)
UPDATE transport_reports
SET
  report_status = 'ACTIONED',
  severity = 'LOW',
  action_taken = 'Fine paid and insurance renewed by owner'
WHERE vehicle_ref = 'DL09VIVA2026';`
  },
  {
    action: 'DELETE',
    db: 'ministry',
    label: '🗑️ Ministry: Dismiss / Delete Violation Report',
    table: 'transport_reports',
    keyCol: 'vehicle_ref',
    sampleKey: 'DL09VIVA2026',
    sql: `-- DELETE report from Ministry DB (Node B)
DELETE FROM transport_reports
WHERE vehicle_ref = 'DL09VIVA2026';`
  },

  // ── CAPTURE ──
  {
    action: 'INSERT',
    db: 'capture',
    label: '➕ Capture: Add Surveillance Camera Event',
    table: 'vehicle_capture',
    keyCol: 'plate_number',
    sampleKey: 'DL09VIVA2026',
    sql: `-- INSERT camera surveillance detection into Capture DB (Master Local)
INSERT INTO vehicle_capture (
  plate_number, detected_vehicle_type, detected_color,
  capture_timestamp, capture_location, image_path,
  detection_confidence, ocr_confidence, camera_id, lane_number
) VALUES (
  'DL09VIVA2026',
  'SUV',
  'BLACK',
  '2026-10-21 14:30:00',
  'Sarita Vihar Checkpost, Delhi',
  'test_assets/assets/test0.9.jpeg',
  0.98,
  0.95,
  'CAM-DEL-01',
  1
);`
  },
  {
    action: 'UPDATE',
    db: 'capture',
    label: '✏️ Capture: Update Detected Color / Class',
    table: 'vehicle_capture',
    keyCol: 'plate_number',
    sampleKey: 'DL09VIVA2026',
    sql: `-- UPDATE detected attributes in Capture DB (Master Local)
UPDATE vehicle_capture
SET
  detected_color = 'OBSIDIAN_BLACK',
  detected_vehicle_type = 'SUV'
WHERE plate_number = 'DL09VIVA2026';`
  },
  {
    action: 'DELETE',
    db: 'capture',
    label: '🗑️ Capture: Remove Camera Capture Event',
    table: 'vehicle_capture',
    keyCol: 'plate_number',
    sampleKey: 'DL09VIVA2026',
    sql: `-- DELETE capture record from Capture DB (Master Local)
DELETE FROM vehicle_capture
WHERE plate_number = 'DL09VIVA2026';`
  },
];

interface TableFkInfo {
  tableName: string;
  isPrimary: boolean;
  pkCol: string;
  fkInfo?: string;
  description: string;
}

const DB_FK_METADATA: Record<string, {
  name: string;
  owner: string;
  color: string;
  primaryKey: string;
  primaryTable: string;
  joinSql: string;
  tables: TableFkInfo[];
}> = {
  registration: {
    name: 'Registration DB',
    owner: 'Node A (Laptop 2)',
    color: '#fbbf24',
    primaryKey: 'reg_serial',
    primaryTable: 'vehicle_registration',
    joinSql: `-- Phase 3 Rubric 1: Multi-table FK-PK Join across Registration DB
SELECT vr.vehicle_reg_no, vo.owner_name, vo.owner_contact, vs.manufacturer, vs.model_name, vs.engine_cc, fc.result as fitness_status, fc.expiry_date
FROM vehicle_registration vr
JOIN vehicle_owners vo ON vr.owner_id = vo.owner_id
JOIN vehicle_specs vs ON vr.reg_serial = vs.reg_serial
LEFT JOIN fitness_certificates fc ON vr.reg_serial = fc.reg_serial
LIMIT 15;`,
    tables: [
      { tableName: 'vehicle_registration', isPrimary: true, pkCol: 'reg_serial', description: 'Core vehicle registration registry' },
      { tableName: 'vehicle_owners', isPrimary: false, pkCol: 'owner_id', fkInfo: 'FK: owner_id ➔ vehicle_owners.owner_id', description: 'Owner personal identity & contact details' },
      { tableName: 'vehicle_specs', isPrimary: false, pkCol: 'spec_id', fkInfo: 'FK: reg_serial ➔ vehicle_registration.reg_serial', description: 'Technical specs (engine CC, emission norm)' },
      { tableName: 'fitness_certificates', isPrimary: false, pkCol: 'cert_id', fkInfo: 'FK: reg_serial ➔ vehicle_registration.reg_serial', description: 'RTO vehicle fitness inspection validity' },
      { tableName: 'rto_transactions', isPrimary: false, pkCol: 'txn_id', fkInfo: 'FK: reg_serial ➔ vehicle_registration.reg_serial', description: 'Ownership transfers & hypothecation history' },
    ]
  },
  insurance: {
    name: 'Insurance DB',
    owner: 'Node A (Laptop 2)',
    color: '#34d399',
    primaryKey: 'policy_id',
    primaryTable: 'insurance_policies',
    joinSql: `-- Phase 3 Rubric 1: Multi-table FK-PK Join across Insurance DB
SELECT ip.policy_number, ip.registration_id, ip.insurer_name, ip.insurance_status, ip.coverage_type, ic.claim_amount, ic.claim_status, pp.amount as last_premium_paid
FROM insurance_policies ip
LEFT JOIN insurance_claims ic ON ip.policy_id = ic.policy_id
LEFT JOIN premium_payments pp ON ip.policy_id = pp.policy_id
LIMIT 15;`,
    tables: [
      { tableName: 'insurance_policies', isPrimary: true, pkCol: 'policy_id', description: 'Active and expired policy master records' },
      { tableName: 'insurance_claims', isPrimary: false, pkCol: 'claim_id', fkInfo: 'FK: policy_id ➔ insurance_policies.policy_id', description: 'Accident and damage claims filed' },
      { tableName: 'premium_payments', isPrimary: false, pkCol: 'payment_id', fkInfo: 'FK: policy_id ➔ insurance_policies.policy_id', description: 'Transactional payment receipts & history' },
      { tableName: 'policy_endorsements', isPrimary: false, pkCol: 'endorsement_id', fkInfo: 'FK: policy_id ➔ insurance_policies.policy_id', description: 'Policy riders and coverage endorsements' },
    ]
  },
  theft: {
    name: 'Theft Bureau DB',
    owner: 'Node B (Laptop 3)',
    color: '#f87171',
    primaryKey: 'case_id',
    primaryTable: 'vehicle_security_records',
    joinSql: `-- Phase 3 Rubric 1: Multi-table FK-PK Join across Theft DB
SELECT vsr.vehicle_identifier, vsr.case_type, vsr.case_status, id.sighting_location, id.investigation_status, si.suspect_name, si.arrest_status
FROM vehicle_security_records vsr
JOIN investigation_details id ON vsr.case_id = id.case_id
LEFT JOIN suspect_info si ON vsr.case_id = si.case_id
LIMIT 15;`,
    tables: [
      { tableName: 'vehicle_security_records', isPrimary: true, pkCol: 'case_id', description: 'Stolen vehicle cases and FIR reports' },
      { tableName: 'investigation_details', isPrimary: false, pkCol: 'investigation_id', fkInfo: 'FK: case_id ➔ vehicle_security_records.case_id', description: 'Police sighting logs and status updates' },
      { tableName: 'recovery_records', isPrimary: false, pkCol: 'recovery_id', fkInfo: 'FK: case_id ➔ vehicle_security_records.case_id', description: 'Vehicle recovery locations and handovers' },
      { tableName: 'suspect_info', isPrimary: false, pkCol: 'suspect_id', fkInfo: 'FK: case_id ➔ vehicle_security_records.case_id', description: 'Identified suspects and arrest status' },
    ]
  },
  ministry: {
    name: 'Ministry Transport DB',
    owner: 'Node B (Laptop 3)',
    color: '#c084fc',
    primaryKey: 'report_id',
    primaryTable: 'transport_reports',
    joinSql: `-- Phase 3 Rubric 1: Multi-table FK-PK Join across Ministry DB
SELECT tr.vehicle_ref, tr.report_type, tr.severity, tr.report_status, ea.action_type, ea.fine_amount, ea.action_status
FROM transport_reports tr
JOIN enforcement_actions ea ON tr.report_id = ea.report_id
LIMIT 15;`,
    tables: [
      { tableName: 'transport_reports', isPrimary: true, pkCol: 'report_id', description: 'Transport violation & compliance incidents' },
      { tableName: 'enforcement_actions', isPrimary: false, pkCol: 'action_id', fkInfo: 'FK: report_id ➔ transport_reports.report_id', description: 'Electronic challans and fines issued' },
      { tableName: 'compliance_history', isPrimary: false, pkCol: 'compliance_id', fkInfo: 'FK: report_id ➔ transport_reports.report_id', description: 'Pollution & emission compliance tests' },
      { tableName: 'blacklisted_vehicles', isPrimary: false, pkCol: 'blacklist_id', fkInfo: 'Direct GAV link: vehicle_ref', description: 'National blacklist for impounded vehicles' },
    ]
  },
  capture: {
    name: 'Capture DB',
    owner: 'Master (Laptop 1)',
    color: '#38bdf8',
    primaryKey: 'capture_id',
    primaryTable: 'vehicle_capture',
    joinSql: `-- Phase 3 Rubric 1: Multi-table FK-PK Join across Capture DB
SELECT vc.plate_number, vc.detected_vehicle_type, vc.detected_color, c.location, c.city, ca.alert_type, ca.alert_severity
FROM vehicle_capture vc
JOIN cameras c ON vc.camera_id = c.camera_id
LEFT JOIN capture_alerts ca ON vc.capture_id = ca.capture_id
LIMIT 15;`,
    tables: [
      { tableName: 'vehicle_capture', isPrimary: true, pkCol: 'capture_id', description: 'Live ANPR camera surveillance events' },
      { tableName: 'cameras', isPrimary: false, pkCol: 'camera_id', fkInfo: 'FK: camera_id ➔ cameras.camera_id', description: 'ANPR smart camera hardware network' },
      { tableName: 'capture_alerts', isPrimary: false, pkCol: 'alert_id', fkInfo: 'FK: capture_id ➔ vehicle_capture.capture_id', description: 'Real-time security alert triggers' },
      { tableName: 'operator_logs', isPrimary: false, pkCol: 'log_id', fkInfo: 'FK: capture_id ➔ vehicle_capture.capture_id', description: 'Human operator triage and review logs' },
    ]
  },
};

const EXAMPLE_SELECT_QUERIES = [
  // ── PHASE 3: MULTI-TABLE FK-PK JOINS (RUBRIC 1 & 2 SHOWCASE) ──
  {
    label: '⭐ [Phase 3] Registration FK-PK Join (Owner + Specs + Fitness)',
    db: 'registration',
    query: `-- Phase 3 Rubric: FK-PK traversal across vehicle_registration, vehicle_owners, vehicle_specs, fitness_certificates
SELECT vr.vehicle_reg_no, vo.owner_name, vo.owner_contact, vs.manufacturer, vs.model_name, vs.engine_cc, fc.result as fitness_result, fc.expiry_date as fitness_expiry
FROM vehicle_registration vr
JOIN vehicle_owners vo ON vr.owner_id = vo.owner_id
JOIN vehicle_specs vs ON vr.reg_serial = vs.reg_serial
LEFT JOIN fitness_certificates fc ON vr.reg_serial = fc.reg_serial
LIMIT 15;`,
  },
  {
    label: '⭐ [Phase 3] Insurance FK-PK Join (Policies + Claims + Payments)',
    db: 'insurance',
    query: `-- Phase 3 Rubric: FK-PK traversal across insurance_policies, insurance_claims, premium_payments
SELECT ip.policy_number, ip.registration_id, ip.insurer_name, ip.insurance_status, ip.coverage_type, ic.claim_amount, ic.claim_status, pp.amount as last_premium_paid
FROM insurance_policies ip
LEFT JOIN insurance_claims ic ON ip.policy_id = ic.policy_id
LEFT JOIN premium_payments pp ON ip.policy_id = pp.policy_id
LIMIT 15;`,
  },
  {
    label: '⭐ [Phase 3] Theft Bureau FK-PK Join (Records + Investigations + Suspects)',
    db: 'theft',
    query: `-- Phase 3 Rubric: FK-PK traversal across vehicle_security_records, investigation_details, suspect_info
SELECT vsr.vehicle_identifier, vsr.case_type, vsr.case_status, id.sighting_location, id.investigation_status, si.suspect_name, si.arrest_status
FROM vehicle_security_records vsr
JOIN investigation_details id ON vsr.case_id = id.case_id
LEFT JOIN suspect_info si ON vsr.case_id = si.case_id
LIMIT 15;`,
  },
  {
    label: '⭐ [Phase 3] Ministry FK-PK Join (Transport Reports + Enforcement Actions)',
    db: 'ministry',
    query: `-- Phase 3 Rubric: FK-PK traversal across transport_reports and enforcement_actions
SELECT tr.vehicle_ref, tr.report_type, tr.severity, tr.report_status, ea.action_type, ea.fine_amount, ea.action_status
FROM transport_reports tr
JOIN enforcement_actions ea ON tr.report_id = ea.report_id
LIMIT 15;`,
  },
  {
    label: '⭐ [Phase 3] Capture FK-PK Join (Captures + Cameras + Real-time Alerts)',
    db: 'capture',
    query: `-- Phase 3 Rubric: FK-PK traversal across vehicle_capture, cameras, capture_alerts
SELECT vc.plate_number, vc.detected_vehicle_type, vc.detected_color, c.location, c.city, ca.alert_type, ca.alert_severity
FROM vehicle_capture vc
JOIN cameras c ON vc.camera_id = c.camera_id
LEFT JOIN capture_alerts ca ON vc.capture_id = ca.capture_id
LIMIT 15;`,
  },

  // ── PHASE 3: NEW EXPANDED TABLES ──
  {
    label: '📋 [Phase 3] Blacklisted Vehicles (Ministry National Blacklist)',
    db: 'ministry',
    query: `SELECT blacklist_id, vehicle_ref, blacklist_reason, blacklist_date, is_active\nFROM blacklisted_vehicles\nORDER BY blacklist_date DESC\nLIMIT 20;`,
  },
  {
    label: '📋 [Phase 3] Fitness Test Certificates (Registration RTO)',
    db: 'registration',
    query: `SELECT cert_id, reg_serial, cert_number, issue_date, expiry_date, result, inspection_center\nFROM fitness_certificates\nORDER BY issue_date DESC\nLIMIT 20;`,
  },
  {
    label: '📋 [Phase 3] Surveillance Cameras Network (Capture)',
    db: 'capture',
    query: `SELECT camera_id, location, city, state, camera_type, resolution, status\nFROM cameras\nLIMIT 20;`,
  },
  {
    label: '📋 [Phase 3] Premium Payments History (Insurance)',
    db: 'insurance',
    query: `SELECT payment_id, policy_id, amount, payment_mode, receipt_number, payment_date\nFROM premium_payments\nORDER BY payment_date DESC\nLIMIT 20;`,
  },
  {
    label: '📋 [Phase 3] Stolen Vehicle Recoveries (Theft Bureau)',
    db: 'theft',
    query: `SELECT recovery_id, case_id, recovery_date, recovery_location, condition_on_recovery\nFROM recovery_records\nLIMIT 20;`,
  },

  // ── FEDERATED & CROSS-DB GAV VIEWS ──
  {
    label: '🌐 [GAV View] Query DL7CQ1939 Across All 5 Databases',
    db: 'all',
    query: `SELECT * FROM vehicle_capture WHERE plate_number = 'DL7CQ1939';`,
  },
  {
    label: '📷 All Captures (Latest 20 Surveillance Events)',
    db: 'capture',
    query: `SELECT plate_number, detected_vehicle_type, detected_color, capture_location, capture_timestamp\nFROM vehicle_capture\nORDER BY capture_timestamp DESC\nLIMIT 20;`,
  },
  {
    label: '🛡️ Active Insurance Policies',
    db: 'insurance',
    query: `SELECT registration_id, insurer_name, policy_number, policy_expiry_date, insurance_status\nFROM insurance_policies\nWHERE insurance_status = 'ACTIVE'\nLIMIT 20;`,
  },
  {
    label: '🚨 Active Stolen / Wanted Cases',
    db: 'theft',
    query: `SELECT vehicle_identifier, case_type, case_status, reported_date, police_reference\nFROM vehicle_security_records\nWHERE case_status = 'OPEN'\nLIMIT 20;`,
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
  const [currentAction, setCurrentAction] = useState<CrudAction>('SELECT');
  const [database, setDatabase] = useState('registration');
  const [query, setQuery] = useState(EXAMPLE_SELECT_QUERIES[2].query);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<ResultSet[] | null>(null);
  const [writeResult, setWriteResult] = useState<WriteResult | null>(null);
  const [totalRows, setTotalRows] = useState(0);
  const [error, setError] = useState('');
  const [_schema, setSchema] = useState<Record<string, SchemaDB> | null>(null);
  const [schemaOpen, setSchemaOpen] = useState(true);
  const [ownership, setOwnership] = useState<Record<string, {owner: string, node: string, writable_here: boolean}> | null>(null);

  // Quick form helper fields for customizing templates on the fly
  const [customPlate, setCustomPlate] = useState('DL09VIVA2026');
  const [customName, setCustomName] = useState('Prof. Anupama Ray');
  const [customColor, setCustomColor] = useState('BLACK');
  const [customMake, setCustomMake] = useState('Hyundai');
  const [customModel, setCustomModel] = useState('Creta 1.6 VTVT');
  const [customStatus, setCustomStatus] = useState('ACTIVE');
  const [lastWrittenPlate, setLastWrittenPlate] = useState('');

  useEffect(() => {
    api.getSqlTables()
      .then(data => setSchema(data.databases))
      .catch(() => setSchema(null));
    api.getDbOwnership()
      .then(data => setOwnership(data.databases))
      .catch(() => setOwnership(null));
  }, []);

  const isWriteMode = currentAction !== 'SELECT';

  const runQuery = async (queryToRun?: string, dbToRun?: string, actionToRun?: CrudAction) => {
    const q = queryToRun || query;
    const db = dbToRun || database;
    const act = actionToRun || currentAction;

    if (!q.trim()) return;
    setLoading(true);
    setError('');
    setResults(null);
    setWriteResult(null);

    try {
      if (act !== 'SELECT') {
        if (db === 'all') throw new Error("Please select a specific database for write operations.");
        const data = await api.sqlWrite(q, db);
        setWriteResult(data);
        setLastWrittenPlate(customPlate);
      } else {
        const data = await api.sqlQuery(q, db);
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

  const loadCrudTemplate = (tmpl: CrudTemplate) => {
    setCurrentAction(tmpl.action);
    setDatabase(tmpl.db);
    setQuery(tmpl.sql);
    setCustomPlate(tmpl.sampleKey);
    setResults(null);
    setWriteResult(null);
    setError('');
  };

  const loadSelectExample = (ex: typeof EXAMPLE_SELECT_QUERIES[0]) => {
    setCurrentAction('SELECT');
    setQuery(ex.query);
    setDatabase(ex.db);
    setResults(null);
    setWriteResult(null);
    setError('');
  };

  const loadAndRunJoin = (dbKey: string) => {
    const meta = DB_FK_METADATA[dbKey];
    if (!meta) return;
    setCurrentAction('SELECT');
    setDatabase(dbKey);
    setQuery(meta.joinSql);
    setResults(null);
    setWriteResult(null);
    setError('');
    runQuery(meta.joinSql, dbKey, 'SELECT');
  };

  const quickQueryTable = (dbKey: string, tableName: string) => {
    const sql = `SELECT * FROM ${tableName} LIMIT 15;`;
    setCurrentAction('SELECT');
    setDatabase(dbKey);
    setQuery(sql);
    setResults(null);
    setWriteResult(null);
    setError('');
    runQuery(sql, dbKey, 'SELECT');
  };

  // Re-apply values from the Quick Form into the current query
  const applyQuickFormToQuery = () => {
    let updated = query;
    // Replace plate placeholder
    updated = updated.replace(/DL09VIVA2026/g, customPlate.trim().toUpperCase());
    updated = updated.replace(/Prof\. Anupama Ray/g, customName.trim());
    updated = updated.replace(/BLACK/g, customColor.trim().toUpperCase());
    updated = updated.replace(/Hyundai/g, customMake.trim());
    updated = updated.replace(/Creta 1\.6 VTVT/g, customModel.trim());
    updated = updated.replace(/ACTIVE/g, customStatus.trim().toUpperCase());
    setQuery(updated);
  };

  // Verify record in DB after INSERT / UPDATE
  const verifyInDb = (plateToVerify?: string) => {
    const p = plateToVerify || lastWrittenPlate || customPlate;
    const tableMap: Record<string, { table: string, col: string }> = {
      registration: { table: 'vehicle_registration', col: 'vehicle_reg_no' },
      insurance: { table: 'insurance_records', col: 'registration_id' },
      theft: { table: 'vehicle_security_records', col: 'vehicle_identifier' },
      ministry: { table: 'transport_reports', col: 'vehicle_ref' },
      capture: { table: 'vehicle_capture', col: 'plate_number' },
    };

    const targetInfo = tableMap[database] || { table: 'vehicle_registration', col: 'vehicle_reg_no' };
    const verifySql = `SELECT * FROM ${targetInfo.table} WHERE ${targetInfo.col} = '${p}'`;
    setCurrentAction('SELECT');
    setQuery(verifySql);
    runQuery(verifySql, database, 'SELECT');
  };

  const dbColor = DB_OPTIONS.find(d => d.value === database)?.color ?? '#a78bfa';

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">SQL Studio &amp; <span>Distributed CRUD</span></h1>
        <p className="page-subtitle">
          Directly <strong>INSERT, UPDATE, and DELETE</strong> records across all 5 independent databases with interactive SQL templates and live verification.
        </p>
      </div>

      {/* ─── PHASE 3 RUBRIC 1 SHOWCASE BANNER ─── */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(37, 99, 235, 0.12), rgba(168, 85, 247, 0.12))',
        border: '1px solid rgba(59, 130, 246, 0.3)',
        borderRadius: 14,
        padding: '16px 20px',
        marginBottom: 20,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10, marginBottom: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 22 }}>🎓</span>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>
                Phase 3 Rubric 1: Distributed Schemas (21 Tables across 5 DBs with Explicit PK-FK Relationships)
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                Entity information is distributed across 4–5 tables per authority (owners, specs, fitness, claims) and connected via PK-FK constraints.
              </div>
            </div>
          </div>
          <span style={{
            fontSize: 11,
            fontWeight: 700,
            padding: '4px 10px',
            borderRadius: 6,
            background: '#2563eb',
            color: '#fff',
            letterSpacing: '0.05em'
          }}>
            RUBRIC 1 (2 MARKS)
          </span>
        </div>

        {/* 1-Click Multi-Table FK-PK Join Buttons */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, alignItems: 'center' }}>
          <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)' }}>1-CLICK FK-PK JOINS:</span>
          {Object.entries(DB_FK_METADATA).map(([key, meta]) => (
            <button
              key={key}
              onClick={() => loadAndRunJoin(key)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                padding: '6px 12px',
                borderRadius: 8,
                border: `1px solid ${meta.color}55`,
                background: database === key && currentAction === 'SELECT' ? `${meta.color}25` : 'var(--color-surface)',
                color: meta.color,
                fontSize: 12,
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.15s',
              }}
              title={`Execute multi-table FK join on ${meta.name} (${meta.owner})`}
            >
              <span>🔗</span>
              <span>{meta.name} Join</span>
            </button>
          ))}
        </div>
      </div>

      {/* ─── ACTION SELECTOR TABS ─── */}
      <div style={{
        display: 'flex',
        gap: 8,
        marginBottom: 20,
        background: 'var(--color-surface)',
        borderRadius: 12,
        padding: 6,
        border: '1px solid var(--color-border)',
        flexWrap: 'wrap'
      }}>
        {[
          { key: 'SELECT', label: '🔍 SELECT (Read Query)', color: '#38bdf8' },
          { key: 'INSERT', label: '➕ INSERT (Add Record)', color: '#34d399' },
          { key: 'UPDATE', label: '✏️ UPDATE (Modify Record)', color: '#fbbf24' },
          { key: 'DELETE', label: '🗑️ DELETE (Remove Record)', color: '#f87171' },
        ].map(tab => {
          const isActive = currentAction === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => {
                const newAction = tab.key as CrudAction;
                setCurrentAction(newAction);
                if (newAction !== 'SELECT' && database === 'all') {
                  setDatabase('registration');
                }
                // Auto-load matching template for current DB
                if (newAction !== 'SELECT') {
                  const match = CRUD_TEMPLATES.find(t => t.action === newAction && t.db === (database === 'all' ? 'registration' : database));
                  if (match) setQuery(match.sql);
                } else {
                  setQuery(EXAMPLE_SELECT_QUERIES[2].query);
                }
                setResults(null);
                setWriteResult(null);
                setError('');
              }}
              style={{
                flex: 1,
                minWidth: 160,
                padding: '10px 16px',
                borderRadius: 8,
                border: 'none',
                cursor: 'pointer',
                fontSize: 13,
                fontWeight: 700,
                transition: 'all 0.2s',
                background: isActive ? tab.color : 'transparent',
                color: isActive ? '#000' : 'var(--text-secondary)',
                boxShadow: isActive ? '0 2px 8px rgba(0,0,0,0.2)' : 'none'
              }}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      <div className="grid-2" style={{ gap: 24, marginBottom: 24 }}>
        {/* Left: Query Editor & Quick Form */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

          {/* Database Selector Card */}
          <div style={{
            background: 'var(--color-surface)',
            border: '1px solid var(--color-border)',
            borderRadius: 14,
            padding: '16px 20px',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 700, letterSpacing: '0.05em' }}>
                TARGET DATABASE ({isWriteMode ? 'WRITE DESTINATION' : 'READ SOURCE'})
              </div>
              <span style={{
                fontSize: 11,
                padding: '2px 8px',
                borderRadius: 4,
                fontWeight: 700,
                background: isWriteMode ? 'rgba(239, 68, 68, 0.2)' : 'rgba(56, 189, 248, 0.2)',
                color: isWriteMode ? '#f87171' : '#38bdf8'
              }}>
                {currentAction} MODE
              </span>
            </div>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {DB_OPTIONS.map(opt => {
                if (isWriteMode && opt.value === 'all') return null;
                const dbOwner = ownership?.[opt.value];
                const isRemote = isWriteMode && dbOwner && !dbOwner.writable_here;
                const isSelected = database === opt.value;

                return (
                  <button
                    key={opt.value}
                    onClick={() => {
                      setDatabase(opt.value);
                      if (isWriteMode) {
                        const match = CRUD_TEMPLATES.find(t => t.action === currentAction && t.db === opt.value);
                        if (match) setQuery(match.sql);
                      } else {
                        const selectMatch = EXAMPLE_SELECT_QUERIES.find(ex => ex.db === opt.value);
                        if (selectMatch) setQuery(selectMatch.query);
                      }
                      setResults(null);
                      setWriteResult(null);
                      setError('');
                    }}
                    style={{
                      padding: '6px 14px',
                      borderRadius: 20,
                      border: isSelected ? `2px solid ${opt.color}` : '2px solid var(--color-border)',
                      background: isSelected ? `${opt.color}22` : 'var(--color-surface-2)',
                      color: isSelected ? opt.color : 'var(--text-muted)',
                      fontSize: 13,
                      fontWeight: isSelected ? 700 : 400,
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6
                    }}
                  >
                    {opt.label}
                    {isRemote && <span title={`Federated to ${dbOwner.owner}`}>🌐</span>}
                  </button>
                );
              })}
            </div>

            {/* Distributed Routing Badge */}
            {isWriteMode && ownership?.[database] && !ownership[database].writable_here && (
              <div style={{ marginTop: 12, fontSize: 12, color: '#38bdf8', background: 'rgba(56, 189, 248, 0.1)', padding: '8px 12px', borderRadius: 8, border: '1px solid rgba(56, 189, 248, 0.2)' }}>
                🌐 <strong>Distributed Federation:</strong> Writes to <strong>{database.toUpperCase()}</strong> will be routed over ngrok to <strong>{ownership[database].owner}</strong> ({ownership[database].node}).
              </div>
            )}
            {isWriteMode && ownership?.[database] && ownership[database].writable_here && (
              <div style={{ marginTop: 12, fontSize: 12, color: '#34d399', background: 'rgba(52, 211, 153, 0.1)', padding: '8px 12px', borderRadius: 8, border: '1px solid rgba(52, 211, 153, 0.2)' }}>
                💻 <strong>Local Database:</strong> Writes will be executed directly on Master Laptop's local SQLite database.
              </div>
            )}
          </div>

          {/* Quick Form Builder (for customizing details without memorizing SQL) */}
          {isWriteMode && (
            <div style={{
              background: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              borderRadius: 14,
              padding: 16,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--color-primary)' }}>
                  ⚡ QUICK DETAILS CUSTOMIZER (OPTIONAL)
                </span>
                <button
                  onClick={applyQuickFormToQuery}
                  style={{
                    padding: '4px 10px',
                    borderRadius: 6,
                    border: '1px solid var(--color-primary)',
                    background: 'var(--color-primary-glow)',
                    color: 'var(--color-primary)',
                    fontSize: 11,
                    fontWeight: 700,
                    cursor: 'pointer'
                  }}
                >
                  🔄 Apply Values to SQL
                </button>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: 10 }}>
                <div>
                  <label style={{ fontSize: 10, color: 'var(--text-muted)', display: 'block', marginBottom: 2 }}>PLATE NUMBER</label>
                  <input
                    type="text"
                    value={customPlate}
                    onChange={e => setCustomPlate(e.target.value.toUpperCase())}
                    style={{ width: '100%', padding: '6px 8px', borderRadius: 6, border: '1px solid var(--color-border)', background: 'var(--color-surface-2)', color: 'var(--text-primary)', fontSize: 12, fontFamily: 'monospace' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: 10, color: 'var(--text-muted)', display: 'block', marginBottom: 2 }}>OWNER / NAME</label>
                  <input
                    type="text"
                    value={customName}
                    onChange={e => setCustomName(e.target.value)}
                    style={{ width: '100%', padding: '6px 8px', borderRadius: 6, border: '1px solid var(--color-border)', background: 'var(--color-surface-2)', color: 'var(--text-primary)', fontSize: 12 }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: 10, color: 'var(--text-muted)', display: 'block', marginBottom: 2 }}>COLOR</label>
                  <input
                    type="text"
                    value={customColor}
                    onChange={e => setCustomColor(e.target.value.toUpperCase())}
                    style={{ width: '100%', padding: '6px 8px', borderRadius: 6, border: '1px solid var(--color-border)', background: 'var(--color-surface-2)', color: 'var(--text-primary)', fontSize: 12 }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: 10, color: 'var(--text-muted)', display: 'block', marginBottom: 2 }}>MAKE</label>
                  <input
                    type="text"
                    value={customMake}
                    onChange={e => setCustomMake(e.target.value)}
                    style={{ width: '100%', padding: '6px 8px', borderRadius: 6, border: '1px solid var(--color-border)', background: 'var(--color-surface-2)', color: 'var(--text-primary)', fontSize: 12 }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: 10, color: 'var(--text-muted)', display: 'block', marginBottom: 2 }}>MODEL</label>
                  <input
                    type="text"
                    value={customModel}
                    onChange={e => setCustomModel(e.target.value)}
                    style={{ width: '100%', padding: '6px 8px', borderRadius: 6, border: '1px solid var(--color-border)', background: 'var(--color-surface-2)', color: 'var(--text-primary)', fontSize: 12 }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: 10, color: 'var(--text-muted)', display: 'block', marginBottom: 2 }}>STATUS</label>
                  <select
                    value={customStatus}
                    onChange={e => setCustomStatus(e.target.value)}
                    style={{ width: '100%', padding: '6px 8px', borderRadius: 6, border: '1px solid var(--color-border)', background: 'var(--color-surface-2)', color: 'var(--text-primary)', fontSize: 12 }}
                  >
                    <option value="ACTIVE">ACTIVE</option>
                    <option value="EXPIRED">EXPIRED</option>
                    <option value="CANCELLED">CANCELLED</option>
                    <option value="OPEN">OPEN (Theft)</option>
                    <option value="CLOSED">CLOSED</option>
                  </select>
                </div>
              </div>
            </div>
          )}

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
                SQL EDITOR — {database.toUpperCase()} ({currentAction})
              </span>
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                {isWriteMode ? 'INSERT / UPDATE / DELETE Mode' : 'SELECT Query Mode'}
              </span>
            </div>

            <textarea
              id="sql-query-input"
              value={query}
              onChange={e => setQuery(e.target.value)}
              spellCheck={false}
              style={{
                width: '100%',
                minHeight: 220,
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
              onKeyDown={e => {
                if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                  e.preventDefault();
                  runQuery();
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
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Ctrl+Enter to execute</span>
              <button
                id="sql-run-btn"
                className="btn btn-primary"
                onClick={() => runQuery()}
                disabled={loading}
                style={{
                  background: isWriteMode ? '#ef4444' : dbColor,
                  border: 'none',
                  minWidth: 140,
                  fontWeight: 700
                }}
              >
                {loading ? 'Executing…' : (isWriteMode ? `▶ Execute ${currentAction}` : '▶ Run SELECT')}
              </button>
            </div>
          </div>
        </div>

        {/* Right: Interactive CRUD Templates & SELECT Examples */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

          {/* CRUD Sample SQL Templates */}
          <div style={{
            background: 'var(--color-surface)',
            border: '1px solid var(--color-border)',
            borderRadius: 14,
            padding: '16px 20px',
          }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--color-primary)', letterSpacing: '0.05em', marginBottom: 12 }}>
              ⚡ ONE-CLICK CRUD SQL TEMPLATES
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 320, overflowY: 'auto' }}>
              {CRUD_TEMPLATES.map((tmpl, i) => (
                <button
                  key={i}
                  onClick={() => loadCrudTemplate(tmpl)}
                  style={{
                    textAlign: 'left',
                    padding: '8px 12px',
                    borderRadius: 8,
                    border: '1px solid var(--color-border)',
                    background: currentAction === tmpl.action && database === tmpl.db ? 'var(--color-surface-3)' : 'var(--color-surface-2)',
                    color: 'var(--text-primary)',
                    fontSize: 12,
                    cursor: 'pointer',
                    transition: 'all 0.15s',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <span>{tmpl.label}</span>
                  <span style={{
                    fontSize: 10,
                    padding: '1px 6px',
                    borderRadius: 4,
                    background: tmpl.action === 'INSERT' ? '#34d39922' : (tmpl.action === 'UPDATE' ? '#fbbf2422' : '#f8717122'),
                    color: tmpl.action === 'INSERT' ? '#34d399' : (tmpl.action === 'UPDATE' ? '#fbbf24' : '#f87171'),
                    fontWeight: 700
                  }}>
                    {tmpl.action}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* SELECT Read Examples */}
          <div style={{
            background: 'var(--color-surface)',
            border: '1px solid var(--color-border)',
            borderRadius: 14,
            padding: '16px 20px',
          }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '0.05em', marginBottom: 12 }}>
              🔍 SAMPLE SELECT QUERIES
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {EXAMPLE_SELECT_QUERIES.map((ex, i) => (
                <button
                  key={i}
                  onClick={() => loadSelectExample(ex)}
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
                >
                  <span style={{ color: DB_OPTIONS.find(d => d.value === ex.db)?.color, fontSize: 16 }}>
                    {DB_OPTIONS.find(d => d.value === ex.db)?.label.split(' ')[0]}
                  </span>
                  {ex.label}
                </button>
              ))}
            </div>
          </div>

          {/* ─── ENHANCED SCHEMA & PK-FK RELATIONSHIP EXPLORER ─── */}
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
                padding: '12px 18px',
                background: 'var(--color-surface-2)',
                border: 'none',
                cursor: 'pointer',
                color: 'var(--text-primary)',
                fontWeight: 700,
                fontSize: 12,
                letterSpacing: '0.05em',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span>📊</span>
                <span>PK-FK SCHEMA EXPLORER (21 TABLES, 16 FK RELS)</span>
              </div>
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{schemaOpen ? '▲ Collapse' : '▼ Expand'}</span>
            </button>

            {schemaOpen && (
              <div style={{ padding: '16px', maxHeight: 420, overflowY: 'auto', fontSize: 12 }}>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 12, lineHeight: 1.4 }}>
                  Click <strong>[⚡ Query]</strong> to fetch any table or <strong>[🔗 Run Join]</strong> to execute live PK-FK joins across distributed nodes:
                </div>

                {Object.entries(DB_FK_METADATA).map(([dbKey, meta]) => (
                  <div key={dbKey} style={{
                    marginBottom: 16,
                    padding: '12px 14px',
                    borderRadius: 10,
                    border: `1px solid ${meta.color}40`,
                    background: 'var(--color-surface-2)'
                  }}>
                    {/* Database Title Bar */}
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8, flexWrap: 'wrap', gap: 6 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span style={{ fontWeight: 800, color: meta.color, fontSize: 13 }}>{meta.name}</span>
                        <span style={{ fontSize: 10, padding: '1px 6px', borderRadius: 4, background: 'var(--color-surface-3)', color: 'var(--text-muted)', fontWeight: 600 }}>
                          {meta.owner}
                        </span>
                      </div>
                      <button
                        onClick={() => loadAndRunJoin(dbKey)}
                        style={{
                          padding: '3px 8px',
                          borderRadius: 6,
                          border: `1px solid ${meta.color}66`,
                          background: `${meta.color}15`,
                          color: meta.color,
                          fontSize: 11,
                          fontWeight: 700,
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 4
                        }}
                        title={`Run FK-PK join query on ${meta.name}`}
                      >
                        <span>🔗</span>
                        <span>Run FK Join</span>
                      </button>
                    </div>

                    {/* Tables with PK / FK indicators */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                      {meta.tables.map(tbl => (
                        <div key={tbl.tableName} style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          padding: '6px 8px',
                          borderRadius: 6,
                          background: 'var(--color-surface)',
                          border: '1px solid var(--color-border)',
                          flexWrap: 'wrap',
                          gap: 6
                        }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                            <span style={{ fontFamily: 'monospace', fontWeight: 700, fontSize: 12, color: 'var(--text-primary)' }}>
                              {tbl.tableName}
                            </span>
                            {tbl.isPrimary ? (
                              <span style={{
                                fontSize: 10,
                                padding: '1px 6px',
                                borderRadius: 4,
                                background: '#34d39922',
                                color: '#34d399',
                                fontWeight: 700
                              }}>
                                PK: {tbl.pkCol}
                              </span>
                            ) : (
                              <span style={{
                                fontSize: 10,
                                padding: '1px 6px',
                                borderRadius: 4,
                                background: '#38bdf822',
                                color: '#38bdf8',
                                fontWeight: 600
                              }}>
                                {tbl.fkInfo || `FK: ${tbl.pkCol}`}
                              </span>
                            )}
                            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                              — {tbl.description}
                            </span>
                          </div>

                          <button
                            onClick={() => quickQueryTable(dbKey, tbl.tableName)}
                            style={{
                              padding: '2px 8px',
                              borderRadius: 4,
                              border: '1px solid var(--color-border)',
                              background: 'var(--color-surface-2)',
                              color: 'var(--text-secondary)',
                              fontSize: 10,
                              fontWeight: 700,
                              cursor: 'pointer'
                            }}
                            title={`Query SELECT * FROM ${tbl.tableName}`}
                          >
                            ⚡ Query
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>
      </div>

      {/* Error Banner */}
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

      {/* Loading Spinner */}
      {loading && (
        <div className="loading-center"><div className="spinner" /><span>Executing query…</span></div>
      )}

      {/* Write Result with Instant Database Verification Button */}
      {writeResult && !loading && (
        <div style={{
          background: 'var(--color-surface)',
          border: '1px solid var(--color-success)',
          borderRadius: 14,
          padding: 20,
          marginBottom: 20,
          boxShadow: '0 4px 16px rgba(52, 211, 153, 0.1)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'var(--color-success)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontSize: 18 }}>
                ✓
              </div>
              <h3 style={{ margin: 0, color: 'var(--color-success)' }}>
                {currentAction} Executed Successfully!
              </h3>
            </div>

            {/* Quick Verification Button */}
            <button
              onClick={() => verifyInDb()}
              style={{
                padding: '8px 16px',
                borderRadius: 8,
                border: 'none',
                background: 'var(--color-primary)',
                color: '#fff',
                fontWeight: 700,
                fontSize: 12,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 6
              }}
            >
              🔍 Verify Record in Database (SELECT)
            </button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 16, background: 'var(--color-surface-2)', padding: 16, borderRadius: 8 }}>
            <div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4, letterSpacing: '0.05em' }}>DATABASE</div>
              <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{writeResult.database.toUpperCase()}</div>
            </div>
            <div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4, letterSpacing: '0.05em' }}>EXECUTED BY</div>
              <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{writeResult.owner}</div>
            </div>
            <div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4, letterSpacing: '0.05em' }}>AFFECTED ROWS</div>
              <div style={{ fontWeight: 700, color: '#34d399' }}>{writeResult.affected_rows}</div>
            </div>
            <div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4, letterSpacing: '0.05em' }}>LAST INSERT ID</div>
              <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{writeResult.last_insert_id || 'N/A'}</div>
            </div>
          </div>

          {writeResult.forwarded_to && (
            <div style={{ marginTop: 12, fontSize: 12, color: '#38bdf8', display: 'flex', alignItems: 'center', gap: 6 }}>
              <span>📡</span> Request was forwarded over network to <strong>{writeResult.forwarded_to}</strong>
            </div>
          )}
        </div>
      )}

      {/* SELECT Results Display */}
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
          </div>

          {results.map((resultSet, i) => {
            const color = DB_OPTIONS.find(d => d.value === resultSet.database)?.color ?? '#aaa';
            const isNoTable = resultSet.error?.includes('no such table');
            if (resultSet.error && isNoTable && results.length > 1) {
              return null;
            }

            return (
              <div key={i} className="card" style={{ marginBottom: 20 }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  marginBottom: 12,
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{
                      display: 'inline-block',
                      width: 10,
                      height: 10,
                      borderRadius: '50%',
                      background: color,
                    }} />
                    <span style={{ fontWeight: 700, color }}>{resultSet.database.toUpperCase()}</span>
                  </div>
                  <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                    {resultSet.row_count} row{resultSet.row_count !== 1 ? 's' : ''}
                  </span>
                </div>

                {resultSet.error ? (
                  <div style={{ color: 'var(--color-danger)', fontSize: 12, fontFamily: 'monospace', padding: '10px 14px', background: 'rgba(239,68,68,0.1)', borderRadius: 8, border: '1px solid rgba(239,68,68,0.2)' }}>
                    <div>❌ {resultSet.error}</div>
                    {isNoTable && (
                      <div style={{ marginTop: 8, color: '#38bdf8', fontFamily: 'system-ui, sans-serif', fontSize: 12 }}>
                        💡 <strong>Table Location Guide:</strong>
                        <ul style={{ margin: '4px 0 0 16px', padding: 0 }}>
                          <li><code>vehicle_registration</code> ➔ <strong>Registration DB</strong> (Node A)</li>
                          <li><code>insurance_records</code> ➔ <strong>Insurance DB</strong> (Node A)</li>
                          <li><code>vehicle_capture</code> ➔ <strong>Capture DB</strong> (Master)</li>
                          <li><code>vehicle_security_records</code> ➔ <strong>Theft DB</strong> (Node B)</li>
                          <li><code>transport_reports</code> ➔ <strong>Ministry DB</strong> (Node B)</li>
                        </ul>
                      </div>
                    )}
                  </div>
                ) : resultSet.rows.length === 0 ? (
                  <div style={{ color: 'var(--text-muted)', fontSize: 12 }}>No records found.</div>
                ) : (
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                      <thead>
                        <tr style={{ borderBottom: '1px solid var(--color-border)', textAlign: 'left' }}>
                          {resultSet.columns.map(col => (
                            <th key={col} style={{ padding: '8px 12px', color: 'var(--text-muted)', fontWeight: 600 }}>{col}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {resultSet.rows.map((row, rIdx) => (
                          <tr key={rIdx} style={{ borderBottom: '1px solid var(--color-border)' }}>
                            {resultSet.columns.map(col => (
                              <td key={col} style={{ padding: '8px 12px', fontFamily: typeof row[col] === 'string' && (row[col] as string).length < 20 ? 'monospace' : 'inherit' }}>
                                {row[col] === null ? <span style={{ color: 'var(--text-muted)' }}>NULL</span> : String(row[col])}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
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
