import React, { useState, useEffect } from 'react';
import FilterBar from './components/FilterBar';
import DiscrepancyTable from './components/DiscrepancyTable';

export default function App() {
  const [orgs, setOrgs] = useState([]);
  const [selectedOrg, setSelectedOrg] = useState('');
  const [selectedReason, setSelectedReason] = useState('ALL');
  const [sortOrder, setSortOrder] = useState('none'); // 'none', 'asc', 'desc'
  const [discrepancies, setDiscrepancies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 1. Fetch available tenant organizations
  useEffect(() => {
    fetch('/api/orgs/')
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}: Failed to fetch organizations`);
        return res.json();
      })
      .then((data) => {
        setOrgs(data);
        if (data.length > 0) {
          setSelectedOrg(data[0].org_id);
        }
      })
      .catch((err) => {
        console.error('Error fetching orgs:', err);
        setError(err.message);
      });
  }, []);

  // 2. Fetch discrepancies when tenant org, reason filter, or sort order changes
  useEffect(() => {
    if (!selectedOrg) return;

    setLoading(true);
    setError(null);

    let url = `/api/discrepancies/?org_id=${encodeURIComponent(selectedOrg)}`;
    if (selectedReason && selectedReason !== 'ALL') {
      url += `&reason=${encodeURIComponent(selectedReason)}`;
    }
    if (sortOrder === 'asc' || sortOrder === 'desc') {
      url += `&sort=${sortOrder}`;
    }

    fetch(url)
      .then((res) => {
        if (!res.ok) {
          return res.json().then((errData) => {
            throw new Error(errData.error || `HTTP ${res.status}: Failed to fetch discrepancies`);
          });
        }
        return res.json();
      })
      .then((data) => {
        setDiscrepancies(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Error fetching discrepancies:', err);
        setError(err.message);
        setLoading(false);
      });
  }, [selectedOrg, selectedReason, sortOrder]);

  const handleSortToggle = () => {
    if (sortOrder === 'none') setSortOrder('asc');
    else if (sortOrder === 'asc') setSortOrder('desc');
    else setSortOrder('none');
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '32px 16px' }}>
      <header style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '28px', fontWeight: '700', color: '#0f172a', margin: '0 0 8px 0' }}>
          Cross-System Reconciliation
        </h1>
        <p style={{ margin: 0, color: '#64748b', fontSize: '15px' }}>
          Tenant-isolated data discrepancy audit dashboard between System A and System B.
        </p>
      </header>

      <FilterBar
        orgs={orgs}
        selectedOrg={selectedOrg}
        onOrgChange={setSelectedOrg}
        selectedReason={selectedReason}
        onReasonChange={setSelectedReason}
        sortOrder={sortOrder}
        onSortToggle={handleSortToggle}
      />

      <DiscrepancyTable
        discrepancies={discrepancies}
        loading={loading}
        error={error}
      />
    </div>
  );
}
