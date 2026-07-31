import React, { useState, useEffect, useCallback } from 'react';
import Navbar from './components/Navbar';
import GridMap from './components/GridMap';
import IncidentFeed from './components/IncidentFeed';
import SimulationPanel from './components/SimulationPanel';
import BriefingModal from './components/BriefingModal';

const API_BASE = 'http://localhost:8000';

export default function App() {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [stats, setStats] = useState({});
  const [faults, setFaults] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);
  const [selectedBriefing, setSelectedBriefing] = useState(null);

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

  // Simulate Fault Trigger
  const handleSimulate = async (type) => {
    setIsSimulating(true);
    try {
      const res = await fetch(`${API_BASE}/api/simulate/fault`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fault_type: type })
      });
      if (res.ok) {
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
      }
    } catch (err) {
      console.error('Reset error:', err);
    } finally {
      setIsSimulating(false);
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
            isSimulating={isSimulating} 
          />
        </div>

        {/* Right Side: Incident Feed Sidebar */}
        <IncidentFeed faults={faults} onSelectFault={handleSelectFault} />
      </main>

      {/* AI Briefing Modal Popup */}
      {selectedBriefing && (
        <BriefingModal 
          briefing={selectedBriefing} 
          onClose={() => setSelectedBriefing(null)} 
        />
      )}
    </div>
  );
}
