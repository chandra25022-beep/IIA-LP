import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import ScanVehicle from './pages/ScanVehicle';
import SearchVehicle from './pages/SearchVehicle';
import DataSources from './pages/DataSources';
import IntegrationView from './pages/IntegrationView';
import MinistryReports from './pages/MinistryReports';
import SqlQueryPage from './pages/SqlQueryPage';
import './index.css';

export default function App() {
  return (
    <BrowserRouter>
      <div className="layout">
        <Sidebar />
        <main className="main-content">
          <Routes>
            <Route path="/"            element={<Dashboard />} />
            <Route path="/scan"        element={<ScanVehicle />} />
            <Route path="/search"      element={<SearchVehicle />} />
            <Route path="/query"       element={<SqlQueryPage />} />
            <Route path="/sources"     element={<DataSources />} />
            <Route path="/integration" element={<IntegrationView />} />
            <Route path="/reports"     element={<MinistryReports />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
