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
          background: 'linear-gradient(135deg, #38bdf8 0%, #3b82f6 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 0 12px rgba(56, 189, 248, 0.4)'
        }}>
          <Zap size={20} color="#ffffff" />
        </div>
        <div>
          <h1 style={{ fontSize: '1.1rem', fontWeight: 700, letterSpacing: '-0.02em', color: '#f1f5f9' }}>
            KSPDB Fault-Locator Engine
          </h1>
          <p style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{
              width: '6px',
              height: '6px',
              borderRadius: '50%',
              backgroundColor: isConnected ? '#22c55e' : '#ef4444',
              display: 'inline-block',
              boxShadow: isConnected ? '0 0 8px #22c55e' : 'none'
            }}></span>
            {isConnected ? 'FastAPI Ingestion Live' : 'Connecting to API...'}
          </p>
        </div>
      </div>

      {/* Grid Live Statistics */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div className="glass-pill" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Cpu size={14} color="#38bdf8" />
          <span>Poles: <strong style={{ color: '#ffffff' }}>{stats.total_poles || 2889}</strong></span>
        </div>

        <div className="glass-pill" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Activity size={14} color="#3b82f6" />
          <span>Transformers: <strong style={{ color: '#ffffff' }}>{stats.total_dts || 40}</strong></span>
        </div>

        <div className="glass-pill" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Network size={14} color="#f97316" />
          <span>Imputed DTs: <strong style={{ color: '#f97316' }}>{stats.imputed_dts_count || 24} (60%)</strong></span>
        </div>

        {/* Active Fault Badge */}
        <div className={`badge ${activeFaultCount > 0 ? 'badge-red' : 'badge-green'}`} style={{ fontSize: '0.8rem', padding: '6px 12px' }}>
          <ShieldAlert size={14} />
          <span>{activeFaultCount > 0 ? `${activeFaultCount} ACTIVE FAULT(S)` : 'GRID NOMINAL'}</span>
        </div>
      </div>
    </header>
  );
}
