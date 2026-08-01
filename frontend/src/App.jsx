import React, { useState, useEffect, useCallback } from 'react';
import Navbar from './components/Navbar';
import GridMap from './components/GridMap';
import IncidentFeed from './components/IncidentFeed';
import SimulationPanel from './components/SimulationPanel';
import BriefingModal from './components/BriefingModal';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

export default function App() {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [stats, setStats] = useState({});
  const [faults, setFaults] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);
  const [selectedBriefing, setSelectedBriefing] = useState(null);
  const [toastMessage, setToastMessage] = useState(null);

  // Fetch full topology (nodes and edges)
  const fetchTopology = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/grid/topology`);
      if (res.ok) {
        const data = await res.json();
        setNodes(data.nodes);
        setEdges(data.edges);
        setStats(data.stats);
        setIsConnected(true);
      }
    } catch (err) {
      console.error('Failed to fetch topology:', err);
      setIsConnected(false);
    }
  }, []);

  // Fetch active faults
  const fetchFaults = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/faults`);
      if (res.ok) {
        const data = await res.json();
        setFaults(data);
      }
    } catch (err) {
      console.error('Failed to fetch faults:', err);
    }
  }, []);

  // Initial load and periodic polling
  useEffect(() => {
    fetchTopology();
    fetchFaults();

    const interval = setInterval(() => {
      fetchTopology();
      fetchFaults();
    }, 3000);

    return () => clearInterval(interval);
  }, [fetchTopology, fetchFaults]);

  const [simInfo, setSimInfo] = useState(null);

  // Simulate Fault Trigger
  const handleSimulate = async (type) => {
    setIsSimulating(true);
    try {
      const endpoint = type === 'scheduled' 
        ? `${API_BASE}/api/simulate/scheduled_outage`
        : `${API_BASE}/api/simulate/fault`;

      const options = type === 'scheduled'
        ? { method: 'POST' }
        : {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ fault_type: type })
          };

      const res = await fetch(endpoint, options);
      if (res.ok) {
        const data = await res.json();
        setSimInfo(data);
        await fetchTopology();
        await fetchFaults();
      }
    } catch (err) {
      console.error('Simulation error:', err);
    } finally {
      setIsSimulating(false);
    }
  };

  // Reset Grid State
  const handleReset = async () => {
    setIsSimulating(true);
    try {
      const res = await fetch(`${API_BASE}/api/grid/reset`, { method: 'POST' });
      if (res.ok) {
        await fetchTopology();
        await fetchFaults();
        setSelectedBriefing(null);
        setSimInfo(null);
      }
    } catch (err) {
      console.error('Reset error:', err);
    } finally {
      setIsSimulating(false);
    }
  };

  // Fast Forward Time
  const handleFastForward = async () => {
    setIsSimulating(true);
    try {
      const res = await fetch(`${API_BASE}/api/simulate/fast_forward`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setSimInfo(data);
        await fetchTopology();
        await fetchFaults();
      }
    } catch (err) {
      console.error('Fast forward error:', err);
    } finally {
      setIsSimulating(false);
    }
  };

  // Restore Power (Repair Faults)
  const handleRestorePower = async () => {
    setIsSimulating(true);
    try {
      const res = await fetch(`${API_BASE}/api/simulate/restore`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setSimInfo({ ...data, message: "Lineman repaired fault. Power restored!" });
        await fetchTopology();
        await fetchFaults();
      }
    } catch (err) {
      console.error('Restore power error:', err);
    } finally {
      setIsSimulating(false);
    }
  };

  // Resolve Ticket manually
  const handleResolveTicket = async (fault) => {
    try {
      const res = await fetch(`${API_BASE}/api/faults/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_id: fault.target })
      });
      if (!res.ok) {
        const errData = await res.json();
        setToastMessage({ type: 'error', text: `System Rejected: ${errData.detail}` });
        setTimeout(() => setToastMessage(null), 5000);
      } else {
        setToastMessage({ type: 'success', text: "Ticket resolved successfully!" });
        setTimeout(() => setToastMessage(null), 3000);
        fetchFaults();
      }
    } catch (err) {
      console.error('Resolve ticket error:', err);
    }
  };

  // Generate AI Crew Briefing
  const handleSelectFault = async (fault) => {
    try {
      const res = await fetch(`${API_BASE}/api/briefing`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(fault)
      });
      if (res.ok) {
        const briefing = await res.json();
        setSelectedBriefing(briefing);
      }
    } catch (err) {
      console.error('Briefing error:', err);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', width: '100vw', overflow: 'hidden' }}>
      {/* Top Navbar */}
      <Navbar stats={stats} activeFaultCount={faults.length} isConnected={isConnected} />

      {/* Main Grid View Workspace */}
      <main style={{
        flex: 1,
        display: 'flex',
        gap: '16px',
        padding: '0 16px 16px 16px',
        height: 'calc(100vh - 80px)',
        position: 'relative'
      }}>
        {/* Left Side: Interactive GIS Map */}
        <div className="glass-panel" style={{ flex: 1, position: 'relative', overflow: 'hidden', padding: '4px' }}>
          <GridMap nodes={nodes} edges={edges} faults={faults} />
          
          {/* Floating Simulation Panel */}
          <SimulationPanel 
            onSimulate={handleSimulate} 
            onReset={handleReset} 
            onFastForward={handleFastForward}
            onRestorePower={handleRestorePower}
            isSimulating={isSimulating} 
            simInfo={simInfo}
          />
        </div>

        {/* Right Side: Incident Feed Sidebar */}
        <IncidentFeed 
            faults={faults} 
            onSelectFault={handleSelectFault} 
            onResolveTicket={handleResolveTicket} 
        />
      </main>

      {/* AI Briefing Modal Popup */}
      {selectedBriefing && (
        <BriefingModal 
          briefing={selectedBriefing} 
          onClose={() => setSelectedBriefing(null)} 
        />
      )}

      {/* Custom Toast Notification */}
      {toastMessage && (
        <div style={{
          position: 'fixed',
          top: '20px',
          left: '50%',
          transform: 'translateX(-50%)',
          background: toastMessage.type === 'error' ? '#ef4444' : '#22c55e',
          color: '#ffffff',
          padding: '12px 24px',
          borderRadius: '8px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
          zIndex: 9999,
          fontWeight: 'bold',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          {toastMessage.type === 'error' ? '⚠️' : '✅'} {toastMessage.text}
        </div>
      )}
    </div>
  );
}
