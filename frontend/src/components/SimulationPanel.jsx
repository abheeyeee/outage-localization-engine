import React, { useState } from 'react';
import { Zap, RefreshCw, AlertOctagon, Flame, Calendar, FastForward } from 'lucide-react';

export default function SimulationPanel({ onSimulate, onReset, onFastForward, isSimulating, simInfo }) {
  return (
    <div style={{
      position: 'absolute',
      bottom: '24px',
      left: '24px',
      zIndex: 1000,
      display: 'flex',
      flexDirection: 'column',
      gap: '8px'
    }}>
      {simInfo && (
        <div className="glass-panel" style={{
          padding: '8px 14px',
          fontSize: '0.75rem',
          color: 'var(--accent-primary)',
          background: 'var(--bg-card)',
          border: '1px solid var(--border-color)',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          borderRadius: '8px',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
        }}>
          <Zap size={14} color="var(--accent-primary)" />
          <span>
            {simInfo.telemetry_sent > 0 ? (
              <>
                <strong>Telemetry Ingested:</strong> {simInfo.telemetry_sent} dying gasp message(s) received. (30% packet drop + Firmware 1.2 quiet failure applied)
              </>
            ) : (
              <>
                <strong>Silent Disconnect:</strong> 0 dying gasp messages received. (Fault inferred via Parent-Child state, or currently hidden).
              </>
            )}
          </span>
        </div>
      )}

      <div className="glass-panel" style={{
        padding: '14px 20px',
        display: 'flex',
        alignItems: 'center',
        gap: '12px'
      }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginRight: '8px', borderRight: '1px solid var(--border-color)', paddingRight: '16px' }}>
        <Zap size={18} color="var(--text-dim)" />
        <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-main)' }}>Simulate Grid Event:</span>
      </div>

      {/* Snap Wire Button */}
      <button
        disabled={isSimulating}
        onClick={() => onSimulate('span')}
        style={{
          background: 'transparent',
          border: '1px solid var(--border-color)',
          color: 'var(--text-muted)',
          borderRadius: '12px',
          padding: '8px 14px',
          fontSize: '0.8rem',
          fontWeight: 600,
          cursor: isSimulating ? 'not-allowed' : 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          transition: 'all 0.2s ease'
        }}
        onMouseEnter={(e) => { e.target.style.color = 'var(--text-main)'; e.target.style.background = 'var(--bg-secondary)'; }}
        onMouseLeave={(e) => { e.target.style.color = 'var(--text-muted)'; e.target.style.background = 'transparent'; }}
      >
        <Zap size={14} color="var(--accent-danger)" />
        Snap Wire (Span Fault)
      </button>

      {/* Blow DT Button */}
      <button
        disabled={isSimulating}
        onClick={() => onSimulate('dt')}
        style={{
          background: 'transparent',
          border: '1px solid var(--border-color)',
          color: 'var(--text-muted)',
          borderRadius: '12px',
          padding: '8px 14px',
          fontSize: '0.8rem',
          fontWeight: 600,
          cursor: isSimulating ? 'not-allowed' : 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          transition: 'all 0.2s ease'
        }}
        onMouseEnter={(e) => { e.target.style.color = 'var(--text-main)'; e.target.style.background = 'var(--bg-secondary)'; }}
        onMouseLeave={(e) => { e.target.style.color = 'var(--text-muted)'; e.target.style.background = 'transparent'; }}
      >
        <Flame size={14} color="var(--accent-warning)" />
        Blow Transformer (DT Fault)
      </button>

      {/* Trip Feeder Button */}
      <button
        disabled={isSimulating}
        onClick={() => onSimulate('feeder')}
        style={{
          background: 'transparent',
          border: '1px solid var(--border-color)',
          color: 'var(--text-muted)',
          borderRadius: '12px',
          padding: '8px 14px',
          fontSize: '0.8rem',
          fontWeight: 600,
          cursor: isSimulating ? 'not-allowed' : 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          transition: 'all 0.2s ease'
        }}
        onMouseEnter={(e) => { e.target.style.color = 'var(--text-main)'; e.target.style.background = 'var(--bg-secondary)'; }}
        onMouseLeave={(e) => { e.target.style.color = 'var(--text-muted)'; e.target.style.background = 'transparent'; }}
      >
        <AlertOctagon size={14} color="var(--accent-warning)" />
        Trip Substation Feeder
      </button>

      {/* Trigger Scheduled Outage Button */}
      <button
        disabled={isSimulating}
        onClick={() => onSimulate('scheduled')}
        style={{
          background: 'transparent',
          border: '1px solid var(--border-color)',
          color: 'var(--text-muted)',
          borderRadius: '12px',
          padding: '8px 14px',
          fontSize: '0.8rem',
          fontWeight: 600,
          cursor: isSimulating ? 'not-allowed' : 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          transition: 'all 0.2s ease'
        }}
        onMouseEnter={(e) => { e.target.style.color = 'var(--text-main)'; e.target.style.background = 'var(--bg-secondary)'; }}
        onMouseLeave={(e) => { e.target.style.color = 'var(--text-muted)'; e.target.style.background = 'transparent'; }}
      >
        <Calendar size={14} color="#c084fc" />
        Trigger Scheduled Outage
      </button>

      {/* Fast Forward Button */}
      <button
        disabled={isSimulating}
        onClick={onFastForward}
        style={{
          background: 'transparent',
          border: '1px solid var(--border-color)',
          color: 'var(--text-muted)',
          borderRadius: '12px',
          padding: '8px 14px',
          fontSize: '0.8rem',
          fontWeight: 600,
          cursor: isSimulating ? 'not-allowed' : 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          marginLeft: '12px',
          transition: 'all 0.2s ease'
        }}
        onMouseEnter={(e) => { e.target.style.color = 'var(--text-main)'; e.target.style.background = 'var(--bg-secondary)'; }}
        onMouseLeave={(e) => { e.target.style.color = 'var(--text-muted)'; e.target.style.background = 'transparent'; }}
      >
        <FastForward size={14} color="#38bdf8" />
        Fast-Forward 15 Mins
      </button>

      {/* Reset Grid Button */}
      <button
        disabled={isSimulating}
        onClick={onReset}
        style={{
          background: 'var(--bg-secondary)',
          border: '1px solid var(--border-color)',
          color: 'var(--text-main)',
          borderRadius: '12px',
          padding: '8px 14px',
          fontSize: '0.8rem',
          fontWeight: 600,
          cursor: isSimulating ? 'not-allowed' : 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          marginLeft: '12px',
          transition: 'all 0.2s ease'
        }}
        onMouseEnter={(e) => { e.target.style.background = 'rgba(255, 255, 255, 0.05)'; }}
        onMouseLeave={(e) => { e.target.style.background = 'var(--bg-secondary)'; }}
      >
        <RefreshCw size={14} color="var(--accent-success)" />
        Reset Grid State
      </button>
      </div>
    </div>
  );
}
