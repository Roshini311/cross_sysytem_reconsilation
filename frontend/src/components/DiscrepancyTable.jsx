import React from 'react';

export default function DiscrepancyTable({ discrepancies, loading, error }) {
  if (loading) {
    return (
      <div style={{ padding: '32px', textAlign: 'center', background: '#fff', borderRadius: '8px' }}>
        <p style={{ fontSize: '16px', color: '#64748b' }}>Loading reconciliation discrepancies...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '24px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', color: '#991b1b' }}>
        <strong>Error: </strong> {error}
      </div>
    );
  }

  if (!discrepancies || discrepancies.length === 0) {
    return (
      <div style={{ padding: '32px', textAlign: 'center', background: '#fff', borderRadius: '8px', border: '1px dashed #cbd5e1' }}>
        <p style={{ fontSize: '16px', color: '#64748b' }}>No discrepancies found for this tenant organization filter.</p>
      </div>
    );
  }

  const getReasonBadgeStyle = (reason) => {
    switch (reason) {
      case 'MISSING_IN_SYSTEM_B':
        return { background: '#fef3c7', color: '#92400e', border: '1px solid #fde68a' };
      case 'ORPHAN_IN_SYSTEM_B':
        return { background: '#e0e7ff', color: '#3730a3', border: '1px solid #c7d2fe' };
      case 'DUPLICATE_IN_SYSTEM_B':
        return { background: '#fee2e2', color: '#991b1b', border: '1px solid #fca5a5' };
      case 'VALUE_MISMATCH':
        return { background: '#ffedd5', color: '#9a3412', border: '1px solid #fed7aa' };
      default:
        return { background: '#f1f5f9', color: '#475569', border: '1px solid #e2e8f0' };
    }
  };

  return (
    <div style={{ background: '#ffffff', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
        <thead>
          <tr style={{ background: '#f1f5f9', borderBottom: '2px solid #e2e8f0' }}>
            <th style={{ padding: '12px 16px', fontWeight: '600' }}>Record ID</th>
            <th style={{ padding: '12px 16px', fontWeight: '600' }}>Location</th>
            <th style={{ padding: '12px 16px', fontWeight: '600' }}>Tenant</th>
            <th style={{ padding: '12px 16px', fontWeight: '600' }}>Reason</th>
            <th style={{ padding: '12px 16px', fontWeight: '600' }}>System A Value</th>
            <th style={{ padding: '12px 16px', fontWeight: '600' }}>System B Value</th>
          </tr>
        </thead>
        <tbody>
          {discrepancies.map((item, idx) => (
            <tr
              key={idx}
              style={{
                borderBottom: '1px solid #f1f5f9',
                background: idx % 2 === 0 ? '#ffffff' : '#fafafa',
              }}
            >
              <td style={{ padding: '12px 16px', fontWeight: '500', fontFamily: 'monospace' }}>
                {item.record_id}
              </td>
              <td style={{ padding: '12px 16px' }}>{item.location_id}</td>
              <td style={{ padding: '12px 16px' }}>{item.org_id}</td>
              <td style={{ padding: '12px 16px' }}>
                <span
                  style={{
                    display: 'inline-block',
                    padding: '4px 8px',
                    borderRadius: '4px',
                    fontSize: '12px',
                    fontWeight: '600',
                    ...getReasonBadgeStyle(item.reason),
                  }}
                >
                  {item.reason}
                </span>
              </td>
              <td style={{ padding: '12px 16px', fontFamily: 'monospace' }}>
                {item.system_a_value !== null && item.system_a_value !== undefined ? (
                  item.system_a_value
                ) : (
                  <span style={{ color: '#94a3b8', italic: 'true' }}>—</span>
                )}
              </td>
              <td style={{ padding: '12px 16px', fontFamily: 'monospace' }}>
                {item.system_b_value !== null && item.system_b_value !== undefined ? (
                  item.system_b_value
                ) : (
                  <span style={{ color: '#94a3b8', italic: 'true' }}>—</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
