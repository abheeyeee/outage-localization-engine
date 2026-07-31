import React, { useMemo } from 'react';
import { MapContainer, TileLayer, CircleMarker, Polyline, Popup } from 'react-leaflet';

export default function GridMap({ nodes, edges, faults }) {
  // Center map on Bangalore grid base coordinate
  const center = [12.9680, 77.5940];

  // Map nodes dictionary for quick lookup by ID
  const nodeDict = useMemo(() => {
    const dict = {};
    nodes.forEach(n => { dict[n.id] = n; });
    return dict;
  }, [nodes]);

  // Set of faulted edge pairs for highlighting
  const faultedEdgeKeys = useMemo(() => {
    const set = new Set();
    faults.forEach(f => {
      if (f.fault_type === 'span_fault' && f.parent_id && f.child_id) {
        set.add(`${f.parent_id}->${f.child_id}`);
        set.add(`${f.child_id}->${f.parent_id}`);
      }
    });
    return set;
  }, [faults]);

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <MapContainer 
        center={center} 
        zoom={13} 
        scrollWheelZoom={true} 
        preferCanvas={true}
        style={{ width: '100%', height: '100%', borderRadius: '12px' }}
      >
        {/* Dark Mode Map Tiles */}
        <TileLayer
          attribution='&copy; <a href="https://carto.com/">CartoDB</a> Dark Matter'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />

        {/* 1. Render Wires (Edges) */}
        {edges.map((edge, idx) => {
          const source = nodeDict[edge.source];
          const target = nodeDict[edge.target];
          if (!source || !target || source.lat == null || target.lat == null) return null;

          const isFaulted = faultedEdgeKeys.has(`${edge.source}->${edge.target}`);
          const positions = [[source.lat, source.lon], [target.lat, target.lon]];

          // Color & Style logic
          let color = edge.is_imputed ? '#f97316' : '#3b82f6';
          let weight = edge.is_imputed ? 1.5 : 2;
          let dashArray = edge.is_imputed ? '4, 6' : null;
          let opacity = 0.65;

          if (isFaulted) {
            color = '#ef4444';
            weight = 4;
            dashArray = null;
            opacity = 1.0;
          }

          return (
            <Polyline
              key={`edge-${idx}`}
              positions={positions}
              pathOptions={{
                color: color,
                weight: weight,
                dashArray: dashArray,
                opacity: opacity
              }}
            />
          );
        })}

        {/* 2. Render Nodes (Poles & DTs) */}
        {nodes.map(node => {
          if (node.lat == null || node.lon == null) return null;

          const isDT = node.type === 'dt';
          
          // Color logic: Green = Live, Red = Dark, Yellow = Silent
          let fillColor = '#22c55e';
          if (!node.is_live) {
            fillColor = '#ef4444';
          } else if (node.reported_state === null && !isDT) {
            fillColor = '#eab308'; // Silent / Comms Loss
          }

          const radius = isDT ? 7 : 4;
          const strokeColor = isDT ? '#38bdf8' : '#0f172a';

          return (
            <CircleMarker
              key={node.id}
              center={[node.lat, node.lon]}
              radius={radius}
              pathOptions={{
                fillColor: fillColor,
                fillOpacity: 0.9,
                color: strokeColor,
                weight: isDT ? 2 : 1
              }}
            >
              <Popup>
                <div style={{ color: '#0f172a', fontSize: '0.85rem', fontFamily: 'sans-serif' }}>
                  <strong>{isDT ? `Transformer: ${node.id}` : `Pole: ${node.id}`}</strong>
                  <br />
                  <span>Feeder: {node.feeder_id || 'N/A'}</span><br />
                  <span>DT: {node.dt_id || 'N/A'}</span><br />
                  <span>Status: <strong style={{ color: node.is_live ? '#16a34a' : '#dc2626' }}>
                    {node.is_live ? 'LIVE' : 'DARK / FAULTED'}
                  </strong></span><br />
                  <span>Device ID: {node.device_id || 'No IoT Device'}</span>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>
    </div>
  );
}
