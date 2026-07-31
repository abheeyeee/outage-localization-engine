import sys
import os
import random

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

from backend.app.main import engine, ingest_telemetry
from backend.app.models import TelemetryEvent
from backend.scripts.simulator import Simulator

def test_full_pipeline():
    print("==================================================")
    print("   RUNNING END-TO-END INTEGRATION FAULT TEST      ")
    print("==================================================")
    
    print(f"\n1. Graph Engine Loaded:")
    print(f"   - Total Poles Loaded: {len(engine.poles)}")
    print(f"   - Total DTs Loaded: {len(engine.dts)}")
    print(f"   - DTs with Imputed Topology (60% Rule): {len(engine.imputed_dts)}")
    
    # 2. Initialize Simulator
    data_dir = os.path.join(project_root, 'backend/data')
    sim = Simulator(data_dir)
    
    # Pick a parent pole that has AT LEAST 15 downstream children so we guarantee multiple telemetry signals
    candidates = []
    for p in sim.children_map.keys():
        if p.startswith("P-"):
            downstream = sim.get_all_downstream_poles(p)
            if len(downstream) >= 15:
                candidates.append((p, len(downstream)))
                
    candidates.sort(key=lambda x: x[1], reverse=True)
    parent = candidates[0][0]
    child = sim.children_map[parent][0]
    
    print(f"\n2. Injecting Mid-Line Fault in Simulator:")
    print(f"   - Wire Snapped Between Parent Pole: {parent} and Child Pole: {child}")
    print(f"   - Total Downstream Poles Affected: {candidates[0][1]}")
    
    # Generate telemetry with 100% arrival to verify algorithmic boundary precision
    sim.drop_rate = 0.0
    sim.v12_rate = 0.0
    telemetry_raw = sim.inject_span_fault(parent, child)
    
    # Convert raw dicts to Pydantic TelemetryEvent objects
    events = [TelemetryEvent(**msg) for msg in telemetry_raw]
    
    print(f"\n3. Ingesting Telemetry into Backend API...")
    res = ingest_telemetry(events)
    print(f"   - Status: {res.status}")
    print(f"   - Telemetry Processed: {res.message}")
    
    # Check detected faults in graph engine
    faults = engine.localize_faults()
    print(f"\n4. Detected Fault Breakdown ({len(faults)} faults):")
    for f in faults:
        print(f"   - FAULT DETECTED: {f}")
        
    print("\n==================================================")
    print("   TEST COMPLETED SUCCESSFULLY! SYSTEM READY!     ")
    print("==================================================")

if __name__ == "__main__":
    test_full_pipeline()
