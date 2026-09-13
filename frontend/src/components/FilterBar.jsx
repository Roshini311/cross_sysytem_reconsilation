import React from 'react';

export default function FilterBar({
  orgs,
  selectedOrg,
  onOrgChange,
  selectedReason,
  onReasonChange,
  sortOrder,
  onSortToggle,
}) {
  const reasonOptions = [
    { value: 'ALL', label: 'All Reasons' },
    { value: 'MISSING_IN_SYSTEM_B', label: 'Missing in System B' },
    { value: 'ORPHAN_IN_SYSTEM_B', label: 'Orphan in System B' },
    { value: 'DUPLICATE_IN_SYSTEM_B', label: 'Duplicate in System B' },
    { value: 'VALUE_MISMATCH', label: 'Value Mismatch' },
  ];

  return (
    <div
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: '16px',
        alignItems: 'center',
        background: '#ffffff',
        padding: '16px 24px',
        borderRadius: '8px',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        marginBottom: '24px',
      }}
    >
      <div>
        <label style={{ fontWeight: '600', marginRight: '8px', fontSize: '14px' }}>
          Tenant / Organization:
        </label>
        <select
          value={selectedOrg}
          onChange={(e) => onOrgChange(e.target.value)}
          style={{
            padding: '8px 12px',
            borderRadius: '6px',
            border: '1px solid #cbd5e1',
            fontSize: '14px',
          }}
        >
          {orgs.map((org) => (
            <option key={org.org_id} value={org.org_id}>
              {org.name || org.org_id}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label style={{ fontWeight: '600', marginRight: '8px', fontSize: '14px' }}>
          Discrepancy Reason:
        </label>
        <select
          value={selectedReason}
          onChange={(e) => onReasonChange(e.target.value)}
          style={{
            padding: '8px 12px',
            borderRadius: '6px',
            border: '1px solid #cbd5e1',
            fontSize: '14px',
          }}
        >
          {reasonOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <button
          onClick={onSortToggle}
          style={{
            padding: '8px 16px',
            borderRadius: '6px',
            border: '1px solid #2563eb',
            background: '#2563eb',
            color: '#ffffff',
            fontWeight: '500',
            fontSize: '14px',
            cursor: 'pointer',
          }}
        >
          Sort by Value: {sortOrder === 'asc' ? 'Ascending ↑' : sortOrder === 'desc' ? 'Descending ↓' : 'Default'}
        </button>
      </div>
    </div>
  );
}
