import React from 'react';
import { AlertTriangle, Sparkles, Network, ArrowRight, Zap, Flame, AlertOctagon, Calendar, CheckCircle } from 'lucide-react';

export default function IncidentFeed({ faults, onSelectFault, onResolveTicket }) {
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
          <AlertTriangle size={18} color="var(--text-muted)" />
          Active Incident Feed
        </h2>
        <span className="glass-pill" style={{ background: '#cbd5e1', color: '#121212', fontWeight: 700, border: 'none', padding: '4px 14px' }}>{faults.length} Active</span>
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
            color: 'var(--text-dim)',
            textAlign: 'center',
            gap: '8px'
          }}>
            <Sparkles size={32} color="var(--accent-primary)" style={{ opacity: 0.5 }} />
            <p style={{ fontSize: '0.85rem', color: 'var(--text-main)' }}>No active power grid faults detected.</p>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Grid operating nominally. Use simulation panel to inject a fault.</p>
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
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '16px',
                  padding: '14px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '10px',
                  boxShadow: '0 4px 12px rgba(0, 0, 0, 0.2)'
                }}
              >
                {/* Title & Badge */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span className="glass-pill" style={{ color: 'var(--text-main)', borderColor: 'var(--border-color)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
                    {fault.is_scheduled ? (
                      <Calendar size={14} color="#c084fc" />
                    ) : isSpan ? (
                      <Zap size={14} color="var(--accent-danger)" />
                    ) : isDT ? (
                      <Flame size={14} color="var(--accent-warning)" />
                    ) : (
                      <AlertOctagon size={14} color="var(--accent-warning)" />
                    )}
                    {fault.is_scheduled ? 'SCHEDULED OUTAGE' : fault.fault_type.replace('_', ' ').toUpperCase()}
                  </span>
                  
                  {isImputed && (
                    <span className="glass-pill" style={{ color: 'var(--text-muted)', borderColor: 'var(--border-color)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Network size={12} />
                      MST IMPUTED
                    </span>
                  )}
                </div>

                {/* Details */}
                <div style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-main)' }}>
                  {fault.is_scheduled ? (
                    <div>
                      <span style={{ color: 'var(--text-main)' }}>{fault.reason || 'Scheduled Maintenance'}</span>
                      <div style={{ fontSize: '0.8rem', color: '#cbd5e1', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>
                        Target: {fault.dt_id || fault.feeder_id || fault.parent_id}
                      </div>
                    </div>
                  ) : isSpan ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontFamily: 'var(--font-mono)' }}>
                      <span>{fault.parent_id}</span>
                      <ArrowRight size={14} color="var(--text-muted)" />
                      <span>{fault.child_id}</span>
                    </div>
                  ) : isDT ? (
                    <span>Transformer Failure: {fault.dt_id}</span>
                  ) : (
                    <span>Feeder Trip: {fault.feeder_id} ({fault.affected_dts} DTs)</span>
                  )}
                </div>

                {/* PIN Code & Area Location */}
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ color: 'var(--accent-primary)', fontWeight: 600 }}>PIN: {fault.pincode || '560001'}</span>
                  <span>•</span>
                  <span>{fault.pincode_area || 'Bangalore Urban'}</span>
                </div>

                {/* Action Buttons */}
                <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
                  <button
                    onClick={() => onSelectFault(fault)}
                    style={{
                      flex: 1,
                      background: 'var(--accent-primary)',
                      border: '1px solid transparent',
                      color: '#ffffff',
                      borderRadius: '10px',
                      padding: '8px 12px',
                      fontSize: '0.8rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '6px',
                      transition: 'all 0.2s ease',
                      boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
                    }}
                    onMouseEnter={(e) => e.target.style.background = 'var(--accent-hover)'}
                    onMouseLeave={(e) => e.target.style.background = 'var(--accent-primary)'}
                  >
                    <Sparkles size={14} />
                    Briefing
                  </button>

                  {!fault.is_scheduled && (
                    <button
                      onClick={(e) => { e.stopPropagation(); onResolveTicket({ ...fault, target: fault.dt_id || fault.child_id || fault.feeder_id }); }}
                      style={{
                        flex: 1,
                        background: 'rgba(34, 197, 94, 0.1)',
                        border: '1px solid rgba(34, 197, 94, 0.2)',
                        color: '#22c55e',
                        borderRadius: '10px',
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
                      onMouseEnter={(e) => { e.target.style.background = 'rgba(34, 197, 94, 0.2)'; }}
                      onMouseLeave={(e) => { e.target.style.background = 'rgba(34, 197, 94, 0.1)'; }}
                    >
                      <CheckCircle size={14} />
                      Resolve
                    </button>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </aside>
  );
}
