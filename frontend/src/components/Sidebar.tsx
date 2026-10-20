import { NavLink } from 'react-router-dom';

const navItems = [
  { to: '/',           icon: '⬡', label: 'Dashboard',       section: 'main' },
  { to: '/scan',       icon: '⌖', label: 'Scan Vehicle',    section: 'main' },
  { to: '/search',     icon: '⌕', label: 'Search Vehicle',  section: 'main' },
  { to: '/query',      icon: '⌨', label: 'SQL Query',       section: 'main' },
  { to: '/sources',    icon: '⬢', label: 'Data Sources',    section: 'integration' },
  { to: '/integration',icon: '⎈', label: 'Integration View',section: 'integration' },
  { to: '/reports',    icon: '⚑', label: 'Ministry Reports',section: 'ministry' },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">🚗</div>
        <div>
          <div className="sidebar-logo-text">VehicleIIA</div>
          <div className="sidebar-logo-sub">Info Integration System</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        <div className="sidebar-section-label">Main</div>
        {navItems.filter(n => n.section === 'main').map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
          >
            <span style={{ fontSize: 16 }}>{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}

        <div className="sidebar-section-label">Integration</div>
        {navItems.filter(n => n.section === 'integration').map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
          >
            <span style={{ fontSize: 16 }}>{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}

        <div className="sidebar-section-label">Authority</div>
        {navItems.filter(n => n.section === 'ministry').map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
          >
            <span style={{ fontSize: 16 }}>{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div style={{ fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 4 }}>IIA Project — Part A</div>
        <div>Mediation / Federated Architecture</div>
        <div style={{ marginTop: 6, color: 'var(--color-primary)', fontSize: 10 }}>Backend: {import.meta.env.VITE_API_BASE || 'localhost:8000'}</div>
      </div>
    </aside>
  );
}
