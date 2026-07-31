from fastapi import FastAPI, BackgroundTasks
from typing import List
import os

try:
    from app.models import TelemetryEvent, FaultResponse
    from app.graph_engine import GraphEngine
except ModuleNotFoundError:
    from backend.app.models import TelemetryEvent, FaultResponse
    from backend.app.graph_engine import GraphEngine

app = FastAPI(title="KSPDB Fault Localization API")

# Initialize the graph engine (loads data and runs spatial imputation on boot)
data_dir = os.path.join(os.path.dirname(__file__), '../../backend/data')
engine = GraphEngine(data_dir)

@app.get("/health")
def health_check():
    return {
        "status": "healthy", 
        "poles_loaded": len(engine.poles),
        "dts_imputed": len(engine.imputed_dts)
    }

@app.post("/telemetry", response_model=FaultResponse)
def ingest_telemetry(events: List[TelemetryEvent]):
    """
    Ingest a batch of telemetry events.
    In a production system, this would push to Kafka/Redis.
    For this simulation, we update the in-memory graph immediately.
    """
    processed = 0
    for event in events:
        pole_id = event.pole_id
        if pole_id in engine.graph.nodes:
            # Check Sequence (solve +/- 90s clock skew / out of order bug)
            current_seq = engine.graph.nodes[pole_id].get('last_seq', -1)
            if event.seq <= current_seq:
                continue # Ignore delayed, older packets
                
            # Update the physical state in the graph and explicitly mark it as reported
            engine.graph.nodes[pole_id]['is_live'] = event.energized
            engine.graph.nodes[pole_id]['reported_state'] = event.energized
            engine.graph.nodes[pole_id]['last_seq'] = event.seq
            processed += 1
            
    # Trigger fault localization
    faults = engine.localize_faults()
    
    return FaultResponse(
        status="success",
        message=f"Processed {processed} telemetry events.",
        faults_detected=len(faults)
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
