import React from 'react';
import { Activity, ShieldAlert, Cpu, Network, Zap } from 'lucide-react';

export default function Navbar({ stats, activeFaultCount, isConnected }) {
  return (
    <header className="glass-panel" style={{
      margin: '12px 16px',
      padding: '12px 24px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      zIndex: 1000,
      position: 'relative'
    }}>
      {/* Brand Title */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{
          width: '36px',
          height: '36px',
          borderRadius: '8px',
          background: 'linear-gradient(135deg, #818cf8 0%, var(--accent-primary) 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 0 12px rgba(79, 70, 229, 0.4)'
        }}>
          <Zap size={20} color="#ffffff" />
        </div>
        <div>
          <h1 style={{ fontSize: '1.1rem', fontWeight: 700, letterSpacing: '-0.02em', color: 'var(--text-main)' }}>
            Fault Locator Dashboard
          </h1>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{
              width: '6px',
              height: '6px',
              borderRadius: '50%',
              backgroundColor: isConnected ? 'var(--accent-success)' : 'var(--accent-danger)',
              display: 'inline-block',
              boxShadow: isConnected ? '0 0 8px var(--accent-success)' : 'none'
            }}></span>
            {isConnected ? 'Ingestion Live' : 'Connecting to API...'}
          </p>
        </div>
      </div>

      {/* Grid Live Statistics */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div className="glass-pill" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Cpu size={14} color="var(--accent-primary)" />
          <span>Poles: <strong style={{ color: 'var(--text-main)' }}>{stats.total_poles || 2889}</strong></span>
        </div>

        <div className="glass-pill" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Activity size={14} color="var(--accent-info)" />
          <span>Transformers: <strong style={{ color: 'var(--text-main)' }}>{stats.total_dts || 40}</strong></span>
        </div>

        <div className="glass-pill" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Network size={14} color="var(--accent-warning)" />
          <span>Imputed DTs: <strong style={{ color: 'var(--accent-warning)' }}>{stats.imputed_dts_count || 24} (60%)</strong></span>
        </div>

        {/* Active Fault Badge */}
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
          padding: '6px 12px',
          borderRadius: '8px',
          fontSize: '0.8rem',
          fontWeight: 600,
          letterSpacing: '0.05em',
          background: 'rgba(255, 255, 255, 0.03)',
          border: '1px solid var(--border-color)',
          color: 'var(--text-main)'
        }}>
          <ShieldAlert size={14} color={activeFaultCount > 0 ? 'var(--accent-danger)' : 'var(--accent-success)'} />
          <span>{activeFaultCount > 0 ? `${activeFaultCount} ACTIVE FAULT(S)` : 'GRID NOMINAL'}</span>
        </div>
      </div>
    </header>
  );
}
