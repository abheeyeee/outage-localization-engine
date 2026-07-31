import React, { useState } from 'react';
import { Zap, RefreshCw, AlertOctagon, Flame, Calendar } from 'lucide-react';

export default function SimulationPanel({ onSimulate, onReset, isSimulating }) {
  return (
    <div className="glass-panel" style={{
      position: 'absolute',
      bottom: '24px',
      left: '24px',
      zIndex: 1000,
      padding: '14px 20px',
      display: 'flex',
      alignItems: 'center',
      gap: '12px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginRight: '8px', borderRight: '1px solid var(--border-color)', paddingRight: '16px' }}>
        <Zap size={18} color="#f97316" />
        <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#f1f5f9' }}>Simulate Grid Event:</span>
      </div>

      {/* Snap Wire Button */}
      <button
        disabled={isSimulating}
        onClick={() => onSimulate('span')}
        style={{
          background: 'rgba(239, 68, 68, 0.2)',
          border: '1px solid rgba(239, 68, 68, 0.4)',
          color: '#ef4444',
          borderRadius: '8px',
          padding: '8px 14px',
          fontSize: '0.8rem',
          fontWeight: 600,
          cursor: isSimulating ? 'not-allowed' : 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '6px'
        }}
      >
        <Zap size={14} />
        Snap Wire (Span Fault)
      </button>

      {/* Blow DT Button */}
      <button
        disabled={isSimulating}
        onClick={() => onSimulate('dt')}
        style={{
          background: 'rgba(249, 115, 22, 0.2)',
          border: '1px solid rgba(249, 115, 22, 0.4)',
          color: '#f97316',
          borderRadius: '8px',
          padding: '8px 14px',
          fontSize: '0.8rem',
          fontWeight: 600,
          cursor: isSimulating ? 'not-allowed' : 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '6px'
        }}
      >
        <Flame size={14} />
        Blow Transformer (DT Fault)
      </button>

      {/* Trip Feeder Button */}
      <button
        disabled={isSimulating}
        onClick={() => onSimulate('feeder')}
        style={{
          background: 'rgba(234, 179, 8, 0.2)',
          border: '1px solid rgba(234, 179, 8, 0.4)',
          color: '#eab308',
          borderRadius: '8px',
          padding: '8px 14px',
          fontSize: '0.8rem',
          fontWeight: 600,
          cursor: isSimulating ? 'not-allowed' : 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '6px'
        }}
      >
        <AlertOctagon size={14} />
        Trip Substation Feeder
      </button>

      {/* Trigger Scheduled Outage Button */}
      <button
        disabled={isSimulating}
        onClick={() => onSimulate('scheduled')}
        style={{
          background: 'rgba(168, 85, 247, 0.2)',
          border: '1px solid rgba(168, 85, 247, 0.4)',
          color: '#c084fc',
          borderRadius: '8px',
          padding: '8px 14px',
          fontSize: '0.8rem',
          fontWeight: 600,
          cursor: isSimulating ? 'not-allowed' : 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '6px'
        }}
      >
        <Calendar size={14} />
        Trigger Scheduled Outage
      </button>

      {/* Reset Grid Button */}
      <button
        disabled={isSimulating}
        onClick={onReset}
        style={{
          background: 'rgba(34, 197, 94, 0.2)',
          border: '1px solid rgba(34, 197, 94, 0.4)',
          color: '#22c55e',
          borderRadius: '8px',
          padding: '8px 14px',
          fontSize: '0.8rem',
          fontWeight: 600,
          cursor: isSimulating ? 'not-allowed' : 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          marginLeft: '12px'
        }}
      >
        <RefreshCw size={14} />
        Reset Grid State
      </button>
    </div>
  );
}
