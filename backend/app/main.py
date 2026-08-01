from fastapi import FastAPI, BackgroundTasks, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
import random

try:
    from app.models import TelemetryEvent, FaultResponse
    from app.graph_engine import GraphEngine
    from app.ai_briefing import generate_crew_briefing
    from scripts.simulator import Simulator
except ModuleNotFoundError:
    from backend.app.models import TelemetryEvent, FaultResponse
    from backend.app.graph_engine import GraphEngine
    from backend.app.ai_briefing import generate_crew_briefing
    from backend.scripts.simulator import Simulator

app = FastAPI(title="KSPDB Fault Localization & Control Room API")

# Enable CORS for React Dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the graph engine (loads data and runs spatial imputation on boot)
data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend/data'))
engine = GraphEngine(data_dir)
sim = Simulator(data_dir)

class SimulateFaultRequest(BaseModel):
    fault_type: str = "span"  # "span", "dt", or "feeder"
    parent_id: Optional[str] = None
    child_id: Optional[str] = None
    dt_id: Optional[str] = None
    feeder_id: Optional[str] = None
    drop_rate: float = 0.30

@app.get("/health")
def health_check():
    return {
        "status": "healthy", 
        "poles_loaded": len(engine.poles),
        "dts_loaded": len(engine.dts),
        "dts_imputed": len(engine.imputed_dts)
    }

@app.get("/api/grid/topology")
def get_grid_topology():
    """
    Returns full grid topology (nodes and edges) formatted for Map rendering.
    """
    nodes = []
    for n, data in engine.graph.nodes(data=True):
        nodes.append({
            "id": n,
            "type": data.get("type", "pole"),
            "lat": data.get("lat"),
            "lon": data.get("lon"),
            "feeder_id": data.get("feeder_id"),
            "dt_id": data.get("dt_id"),
            "is_live": data.get("is_live", True),
            "reported_state": data.get("reported_state"),
            "device_id": data.get("device_id", "")
        })

    edges = []
    for u, v, data in engine.graph.edges(data=True):
        edges.append({
            "source": u,
            "target": v,
            "is_imputed": data.get("is_imputed", False)
        })

    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "total_poles": len(engine.poles),
            "total_dts": len(engine.dts),
            "imputed_dts_count": len(engine.imputed_dts)
        }
    }

MOCK_SCHEDULED_OUTAGES = [
    {
        "id": "SO-2026-07-29-014",
        "scope": "feeder",
        "target_id": "F-07-03",
        "start": "2026-07-29T10:00:00Z",
        "end": "2026-08-01T23:59:59Z",
        "reason": "Planned maintenance - jumper replacement"
    },
    {
        "id": "SO-2026-07-29-021",
        "scope": "dt",
        "target_id": "D-0005",
        "start": "2026-07-29T14:00:00Z",
        "end": "2026-08-01T23:59:59Z",
        "reason": "Load shedding"
    }
]

@app.get("/scheduled-outages")
@app.get("/api/scheduled-outages")
def get_scheduled_outages(from_ts: str = None, to_ts: str = None):
    """ Returns active scheduled maintenance and load shedding outages """
    return MOCK_SCHEDULED_OUTAGES

@app.get("/api/faults")
def get_localized_faults():
    """ Returns active localized fault tickets """
    return engine.localize_faults(MOCK_SCHEDULED_OUTAGES)

@app.post("/telemetry", response_model=FaultResponse)
def ingest_telemetry(events: List[TelemetryEvent]):
    """ Ingest telemetry batch into graph engine """
    processed = 0
    for event in events:
        pole_id = event.pole_id
        if pole_id in engine.graph.nodes:
            current_seq = engine.graph.nodes[pole_id].get('last_seq', -1)
            if event.seq <= current_seq:
                continue # Drop stale out-of-order packets
                
            engine.graph.nodes[pole_id]['is_live'] = event.energized
            engine.graph.nodes[pole_id]['reported_state'] = event.energized
            engine.graph.nodes[pole_id]['last_seq'] = event.seq
            processed += 1
            
    faults = engine.localize_faults(MOCK_SCHEDULED_OUTAGES)
    return FaultResponse(
        status="success",
        message=f"Processed {processed} telemetry events.",
        faults_detected=len(faults)
    )

@app.post("/api/simulate/fault")
def simulate_fault(req: SimulateFaultRequest):
    """ Inject a fault via Simulator and process output telemetry """
    sim.drop_rate = req.drop_rate
    
    if req.fault_type == "span":
        parent = req.parent_id
        child = req.child_id
        
        # Pick random span if not provided
        if not parent or not child:
            candidates = [p for p in sim.children_map.keys() if p.startswith("P-")]
            parent = random.choice(candidates)
            child = sim.children_map[parent][0]
            
        telemetry_raw = sim.inject_span_fault(parent, child)
        
    elif req.fault_type == "dt":
        dt_id = req.dt_id or random.choice(list(engine.dts.keys()))
        telemetry_raw = sim.inject_dt_fault(dt_id)
        
    else:  # feeder
        if req.feeder_id:
            feeder_id = req.feeder_id
        else:
            feeders = list(set(dt.get('feeder_id') for dt in engine.dts.values() if dt.get('feeder_id')))
            feeder_id = random.choice(feeders) if feeders else "F-07-01"
        telemetry_raw = sim.inject_feeder_fault(feeder_id)

    # Ingest generated noisy telemetry
    events = [TelemetryEvent(**msg) for msg in telemetry_raw]
    res = ingest_telemetry(events)
    
    # For DT/Feeder faults: the equipment itself knows it failed.
    # Directly mark affected DT nodes dark so the algorithm correctly
    # classifies the outage (instead of scattered span_faults due to 30% telemetry drop).
    if req.fault_type == "dt":
        dt_id = req.dt_id or dt_id
        if dt_id in engine.graph.nodes:
            engine.graph.nodes[dt_id]['is_live'] = False
            engine.graph.nodes[dt_id]['reported_state'] = False
    elif req.fault_type == "feeder":
        for node, data in engine.graph.nodes(data=True):
            if data.get('type') == 'dt' and data.get('feeder_id') == feeder_id:
                engine.graph.nodes[node]['is_live'] = False
                engine.graph.nodes[node]['reported_state'] = False

    return {
        "status": "success",
        "telemetry_sent": len(telemetry_raw),
        "telemetry_processed": res.message,
        "faults": engine.localize_faults(MOCK_SCHEDULED_OUTAGES)
    }

@app.post("/api/simulate/scheduled_outage")
def simulate_scheduled_outage():
    """ Inject a blackout matching an active scheduled outage feed """
    # Trigger outage on Transformer D-0005 (in MOCK_SCHEDULED_OUTAGES)
    telemetry_raw = sim.inject_dt_fault("D-0005")
    events = [TelemetryEvent(**msg) for msg in telemetry_raw]
    res = ingest_telemetry(events)
    
    # Directly mark the DT node dark (equipment-level knowledge, not sensor telemetry)
    if "D-0005" in engine.graph.nodes:
        engine.graph.nodes["D-0005"]["is_live"] = False
        engine.graph.nodes["D-0005"]["reported_state"] = False
    
    return {
        "status": "success",
        "telemetry_sent": len(telemetry_raw),
        "telemetry_processed": res.message,
        "faults": engine.localize_faults(MOCK_SCHEDULED_OUTAGES)
    }

@app.post("/api/simulate/fast_forward")
def fast_forward():
    """ Simulates 15 minutes passing. Finds nodes that missed heartbeats. """
    swept = 0
    for pole_id in sim.physically_dead_nodes:
        if pole_id in engine.graph.nodes:
            # If the engine still thinks it's live, but it's physically dead,
            # this simulates the 15-minute heartbeat missing
            if engine.graph.nodes[pole_id].get('is_live', True):
                engine.graph.nodes[pole_id]['is_live'] = False
                engine.graph.nodes[pole_id]['reported_state'] = False
                swept += 1
                
    faults = engine.localize_faults(MOCK_SCHEDULED_OUTAGES)
    return {
        "status": "success",
        "swept_nodes": swept,
        "message": f"Swept {swept} silent nodes via heartbeat timeout.",
        "faults": faults
    }

@app.post("/api/simulate/restore")
def restore_power():
    """ Simulates a crew physically repairing the fault and power returning """
    telemetry_raw = sim.restore_grid()
    events = [TelemetryEvent(**msg) for msg in telemetry_raw]
    res = ingest_telemetry(events)
    
    # A physical crew repair restores ALL power.
    # Force every dead node in the entire graph back to live.
    # This handles: deviceless poles, 30% telemetry drop, DT nodes, and imputed topology gaps.
    force_restored = 0
    for node_id in engine.graph.nodes:
        if not engine.graph.nodes[node_id].get('is_live', True):
            engine.graph.nodes[node_id]['is_live'] = True
            engine.graph.nodes[node_id]['reported_state'] = True
            force_restored += 1
    
    return {
        "status": "success",
        "telemetry_sent": len(telemetry_raw),
        "force_restored": force_restored,
        "faults": engine.localize_faults(MOCK_SCHEDULED_OUTAGES)
    }

@app.post("/api/faults/resolve")
def resolve_ticket(req: Dict = Body(...)):
    """ Attempt to close a ticket manually. Pushes back if power is still out. """
    target_id = req.get("target_id")
    if not target_id:
        raise HTTPException(status_code=400, detail="Missing target_id")
    
    # Check if target is a feeder ID (not a graph node — check DTs under it)
    if target_id.startswith("F-"):
        dark_dts = []
        for node, data in engine.graph.nodes(data=True):
            if data.get('type') == 'dt' and data.get('feeder_id') == target_id:
                if not data.get('is_live', True):
                    dark_dts.append(node)
        if dark_dts:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot close ticket: {len(dark_dts)} transformers on feeder {target_id} still have no power."
            )
    elif target_id in engine.graph.nodes:
        is_live = engine.graph.nodes[target_id].get("is_live", True)
        if not is_live:
            raise HTTPException(
                status_code=400, 
                detail="Cannot close ticket: Telemetry confirms power is still OUT at this location."
            )
            
    return {"status": "success", "message": "Ticket successfully closed."}

@app.post("/api/grid/reset")
def reset_grid():
    """ Reset all nodes in graph engine to healthy Live state """
    sim.reset()
    for n in engine.graph.nodes:
        engine.graph.nodes[n]['is_live'] = True
        engine.graph.nodes[n]['reported_state'] = None
        engine.graph.nodes[n]['last_seq'] = -1
    return {"status": "success", "message": "Grid state reset to Live."}

@app.post("/api/briefing")
def get_briefing(fault: Dict = Body(...)):
    """ Generate structured AI Crew Dispatch Briefing """
    return generate_crew_briefing(fault, engine.graph)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
