interface StatusBadgeProps {
  status: string;
  size?: 'sm' | 'lg';
}

const statusConfig: Record<string, { label: string; className: string; icon: string }> = {
  INSURED:            { label: 'Insured', className: 'insured', icon: '✓' },
  INSURANCE_EXPIRED:  { label: 'Expired Insurance', className: 'expired', icon: '⚠' },
  UNINSURED:          { label: 'Uninsured', className: 'uninsured', icon: '✗' },
  STOLEN:             { label: 'Stolen', className: 'stolen', icon: '🚨' },
  SCRAPPED:           { label: 'Scrapped', className: 'scrapped', icon: '⬛' },
  SUSPICIOUS:         { label: 'Suspicious', className: 'suspicious', icon: '⚠' },
  DATA_CONFLICT:      { label: 'Data Conflict', className: 'conflict', icon: '⚡' },
  UNKNOWN:            { label: 'Unknown', className: 'unknown', icon: '?' },
  ACTIVE:             { label: 'Active', className: 'active', icon: '●' },
  EXPIRED:            { label: 'Expired', className: 'expired', icon: '●' },
  CANCELLED:          { label: 'Cancelled', className: 'uninsured', icon: '●' },
  NOT_FOUND:          { label: 'Not Found', className: 'unknown', icon: '–' },
  PENDING:            { label: 'Pending', className: 'pending', icon: '⏳' },
  RESOLVED:           { label: 'Resolved', className: 'resolved', icon: '✓' },
  ACTIONED:           { label: 'Actioned', className: 'insured', icon: '✓' },
  OPEN:               { label: 'Open', className: 'expired', icon: '●' },
  CLOSED:             { label: 'Closed', className: 'resolved', icon: '●' },
  NOT_SCRAPPED:       { label: 'Not Scrapped', className: 'active', icon: '✓' },
  NOT_REPORTED:       { label: 'Not Reported', className: 'unknown', icon: '–' },
  UNCERTAIN_MATCH_REVIEW: { label: 'Uncertain Match (Review)', className: 'suspicious', icon: '⚡' },
  AUTO_MERGE:         { label: 'Auto-Merged (STP)', className: 'insured', icon: '✓' },
  UNCERTAIN_REVIEW:   { label: 'Needs Review', className: 'pending', icon: '⚠' },
  REJECT:             { label: 'Rejected Match', className: 'uninsured', icon: '✗' },
};

export default function StatusBadge({ status, size = 'sm' }: StatusBadgeProps) {
  const config = statusConfig[status] || { label: status, className: 'unknown', icon: '?' };
  return (
    <span className={`badge${size === 'lg' ? ' badge-lg' : ''} ${config.className}`}>
      <span>{config.icon}</span>
      {config.label}
    </span>
  );
}
