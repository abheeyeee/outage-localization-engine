import React from 'react';
import { AlertTriangle, Sparkles, Network, ArrowRight } from 'lucide-react';

export default function IncidentFeed({ faults, onSelectFault }) {
  return (
    <aside className="glass-panel" style={{
      width: '380px',
      height: 'calc(100vh - 100px)',
      display: 'flex',
      flexDirection: 'column',
      padding: '16px',
      gap: '12px'
    }}>
      {/* Feed Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px' }}>
        <h2 style={{ fontSize: '1rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
          <AlertTriangle size={18} color="#ef4444" />
          Active Incident Feed
        </h2>
        <span className="glass-pill">{faults.length} Active</span>
      </div>

      {/* Incident List */}
      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px', paddingRight: '4px' }}>
        {faults.length === 0 ? (
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100%',
            color: '#64748b',
            textAlign: 'center',
            gap: '8px'
          }}>
            <Sparkles size={32} color="#3b82f6" style={{ opacity: 0.5 }} />
            <p style={{ fontSize: '0.85rem' }}>No active power grid faults detected.</p>
            <p style={{ fontSize: '0.75rem', color: '#475569' }}>Grid operating nominally. Use simulation panel to inject a fault.</p>
          </div>
        ) : (
          faults.map((fault, idx) => {
            const isSpan = fault.fault_type === 'span_fault';
            const isDT = fault.fault_type === 'dt_fault';
            const isImputed = fault.is_imputed;

            return (
              <div 
                key={idx}
                style={{
                  background: 'rgba(15, 23, 42, 0.6)',
                  border: isImputed ? '1px solid rgba(249, 115, 22, 0.4)' : '1px solid rgba(239, 68, 68, 0.3)',
                  borderRadius: '10px',
                  padding: '14px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '10px',
                  boxShadow: '0 4px 12px rgba(0, 0, 0, 0.2)'
                }}
              >
                {/* Title & Badge */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span className={fault.is_scheduled ? 'badge' : isSpan ? 'badge badge-red' : isDT ? 'badge badge-orange' : 'badge badge-red'} style={fault.is_scheduled ? { background: 'rgba(168, 85, 247, 0.2)', color: '#c084fc', border: '1px solid rgba(168, 85, 247, 0.4)' } : {}}>
                    {fault.is_scheduled ? 'SCHEDULED OUTAGE' : fault.fault_type.replace('_', ' ').toUpperCase()}
                  </span>
                  
                  {isImputed && (
                    <span className="glass-pill" style={{ color: '#f97316', borderColor: 'rgba(249, 115, 22, 0.4)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Network size={12} />
                      MST IMPUTED
                    </span>
                  )}
                </div>

                {/* Details */}
                <div style={{ fontSize: '0.9rem', fontWeight: 600, color: '#f1f5f9' }}>
                  {fault.is_scheduled ? (
                    <div>
                      <span style={{ color: '#c084fc' }}>{fault.reason || 'Scheduled Maintenance'}</span>
                      <div style={{ fontSize: '0.8rem', color: '#cbd5e1', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>
                        Target: {fault.dt_id || fault.feeder_id || fault.parent_id}
                      </div>
                    </div>
                  ) : isSpan ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontFamily: 'var(--font-mono)' }}>
                      <span>{fault.parent_id}</span>
                      <ArrowRight size={14} color="#ef4444" />
                      <span>{fault.child_id}</span>
                    </div>
                  ) : isDT ? (
                    <span>Transformer Failure: {fault.dt_id}</span>
                  ) : (
                    <span>Feeder Trip: {fault.feeder_id} ({fault.affected_dts} DTs)</span>
                  )}
                </div>

                {/* PIN Code & Area Location */}
                <div style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ color: '#38bdf8', fontWeight: 600 }}>PIN: {fault.pincode || '560001'}</span>
                  <span>•</span>
                  <span>{fault.pincode_area || 'Bangalore Urban'}</span>
                </div>

                {/* AI Briefing Button */}
                <button
                  onClick={() => onSelectFault(fault)}
                  style={{
                    marginTop: '4px',
                    background: 'linear-gradient(135deg, rgba(56, 189, 248, 0.2) 0%, rgba(59, 130, 246, 0.2) 100%)',
                    border: '1px solid var(--border-accent)',
                    color: '#38bdf8',
                    borderRadius: '6px',
                    padding: '8px 12px',
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px',
                    transition: 'all 0.2s ease'
                  }}
                  onMouseEnter={(e) => e.target.style.background = 'rgba(56, 189, 248, 0.3)'}
                  onMouseLeave={(e) => e.target.style.background = 'linear-gradient(135deg, rgba(56, 189, 248, 0.2) 0%, rgba(59, 130, 246, 0.2) 100%)'}
                >
                  <Sparkles size={14} />
                  Generate AI Crew Briefing
                </button>
              </div>
            );
          })
        )}
      </div>
    </aside>
  );
}
