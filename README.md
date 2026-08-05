# Outage Localization Engine

This repository contains the Outage Localization Engine. The system ingests noisy, lossy "dying gasp" telemetry from grid IoT devices, spatially imputes missing topology data, and uses a Topological Graph Engine to precisely localize span and equipment faults while aggressively preventing ticket storms via Hierarchical Aggregation.

## Quickstart

The entire stack is containerized. To build and start the system (frontend + backend + auto-seeding the mock data):

```bash
docker compose up --build
```

- **Frontend UI:** [http://localhost:5173](http://localhost:5173)
- **Backend API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

*Note: On first run, the backend container will automatically generate 2,800+ mock poles and 40 transformers before starting the server. This may take a few seconds.*

### Auto-Seeding & G3 Gate Fulfillment
To satisfy the assignment's **G3 Acceptance Gate** (seeding on startup with no manual intervention), this project utilizes a custom `backend/entrypoint.sh` script. When `docker compose up` is executed, the entrypoint intercepts the boot process, detects if the `dts.csv` and `poles.csv` data files are missing, and automatically triggers the Python data generator to build the synthetic grid before handing control over to the FastAPI server. You will never see an empty screen.

## Public Access (Live Demo)
- **Frontend URL:** [https://outagelocalizationengine.vercel.app/](https://outagelocalizationengine.vercel.app/)
- **Backend API URL:** [https://outage-localization-engine.onrender.com/docs](https://outage-localization-engine.onrender.com/docs)
- **Demo Video (5-min):** [PLACEHOLDER_FOR_LOOM_OR_YOUTUBE_LINK]

*(Note to Reviewer: The live demo is hosted on a free tier. Please allow 30-60 seconds for the containers to cold-start when you first open the URL before assuming the system is broken.)*

## Documentation Map

For grading and review, please refer to the following documents in this repository:

1. **[ARCHITECTURE.md](./ARCHITECTURE.md)**: Details the Topological Graph Engine, spatial imputation algorithm, the two-pass Implied State resolver for quiet failures, and the backend data model.
2. **[AI-WORKFLOW.md](./AI-WORKFLOW.md)**: Concrete examples of how LLMs failed, hallucinated, and were corrected during the engineering of this system.
3. **[DECISIONS.md](./DECISIONS.md)**: A log of key technical tradeoffs made, including my strategy for preventing ticket storms and what I know is currently fragile.
4. **[DEPLOYMENT.md](./DEPLOYMENT.md)**: Troubleshooting guide for Docker, CORS, and port conflicts.

---

## 🧪 Testing Guide for Graders (Simulation Panel)

To strictly evaluate this submission against the rubric, a fully integrated **Grid Simulator** is provided on the bottom panel of the UI. This simulator generates real-time telemetry events injected with realistic 30% packet drops and firmware failure rates.

### 1. Test Task 2 (Localizing Span Faults)
- **Action:** Click **"Snap Wire (Span Fault)"**.
- **What happens:** The simulator physically cuts a wire in the generated backend graph. All downstream poles instantly lose power and attempt to send a dying gasp. The cellular network drops ~30% of these packets.
- **Verification:** Watch the AI Engine effortlessly parse through the noisy, incomplete telemetry. It will traverse the `NetworkX` graph, mathematically impute the missing packets, and output **exactly one Ticket**. The ticket will explicitly state the specific span, the `Lat/Lon` coordinates for the truck, the PIN code, and exactly how many poles are affected downstream.

### 2. Test Task 2 (Substation/DT Equipment Defaults)
- **Action:** Click **"Blow Transformer (DT Fault)"**.
- **What happens:** An entire transformer goes dark, wiping out hundreds of downstream poles.
- **Verification:** The localization engine will *not* flood the control room with hundreds of span fault tickets. It correctly groups the failure to the single root cause (the DT) using Top-Down graph traversal.

### 3. Test Task 2 (Massive Scale Feeder Faults)
- **Action:** Click **"Blow Substation (Feeder Fault)"**.
- **What happens:** An entire 11kV Feeder trips, knocking out multiple transformers and up to 500+ poles simultaneously.
- **Verification:** The engine's Top-Down hierarchy aggressively aggregates this. It will suppress both the individual pole span faults AND the individual DT faults, outputting exactly one root-cause **Feeder Fault** ticket.

### 4. Test Task 3 (Don't Cry Wolf - Mathematical Validation)
- **Action:** Click **"Trigger Scheduled Outage"**.
- **What happens:** The simulator drops power to a block of poles due to scheduled load shedding.
- **Verification:** The engine will process the power loss but **generate zero tickets**. The backend strictly suppresses expected failures to prevent "crying wolf". Furthermore, the engine utilizes a *Bottom-Up Implied State Check*: if any sensor lies or sends an isolated failure ping while its children are alive, the algorithm mathematically proves the parent is lying and suppresses the false alarm.

### 5. Test Task 3 (Silent Failures & Heartbeat Sweeping)
- **When to use:** Sometimes when you click "Snap Wire", the simulator will return a **"Silent Disconnect: 0 dying gasp messages received"** warning. This simulates the 30% failure rate where devices lose power without broadcasting an alert, leaving the engine temporarily blind.
- **Action:** Click **"Fast Forward 15 Mins"**.
- **What happens:** The UI simulates the passage of 15 minutes. 
- **Verification:** Fast-forwarding triggers the backend's Watchdog Sweeper. It scans for missed 15-minute heartbeats, retroactively discovers the silent dead sensors, and generates the correct localized tickets despite receiving zero `power_lost` packets.

### 4. Test Task 4 & 5 (Ticket Workflow & Operator UI)
- **Action:** Click **"Repair Fault (Restore Power)"**.
- **What happens:** The simulator restores physical power. 100% of sensors instantly boot up and flood the network with `energized=True` pings.
- **Verification:** The system seamlessly resolves the active fault tickets. The minimalist Operator Console is explicitly designed to reduce cognitive load at 2 a.m.—hiding complex SVG topologies in favor of direct, actionable AI Crew Briefings.

---

## 🛠️ Automated Tests (Localization Logic)

Per the assignment instructions: *"Tests where they matter. We are looking for tests on the localization logic specifically — that is where correctness lives. Broad coverage of controllers and components is not what we want. If you test one thing, test that a known fault in a known topology produces the expected span."*

I explicitly adhered to this. All tests target the mathematical core of `GraphEngine.localize_faults()`.

To run the algorithmic test suite:
```bash
# Ensure your docker containers are running, then execute:
docker compose exec backend pytest -v
```

### What these tests verify:
1. **`test_mid_line_span_fault`**: Programmatically builds a known linear `NetworkX` topology (DT -> P1 -> P2 -> P3 -> P4), cuts power at P3, and asserts the engine outputs exactly 1 span fault between P2 and P3.
2. **`test_fault_at_head_of_line`**: Tests Hierarchical Aggregation. Plunges an entire DT and 4 poles into darkness and asserts that 0 span faults are generated, outputting exactly 1 DT fault instead.
3. **`test_lying_parent_with_live_child`**: Tests the Implied State Resolver. Forces a parent pole to report `False` while its child reports `True`, and asserts the engine overrides the lie and generates 0 tickets.
4. **`test_scheduled_outage_tagged`**: Validates the "Don't Cry Wolf" scheduled outage suppression.

---

## 🚀 Performance Benchmarking (5,000 Burst)

To mathematically prove the backend satisfies **Task 1** (sustained 39 msg/s and a 5,000 message burst), an integration load-testing script is included. 

Because `O(1)` memory dictionary updates (`engine.graph.nodes[id]['is_live'] = False`) are exponentially faster than database I/O, the API handles the burst effortlessly.

To run the load test:
```bash
# Ensure the docker containers are running, then execute:
docker compose exec backend python scripts/benchmark.py
```

### What this benchmark verifies:
1. **Operator Console Load:** Simulates fetching the entire grid topology for the frontend map and asserts it resolves in under 2 seconds.
2. **Sustained Ingest Throughput:** Shoots 1,000 telemetry packets and asserts the API consumes them at a rate of > 500 msg/s.
3. **Ingest Burst Tolerance:** Shoots an instantaneous burst of **5,000 dying gasps and heartbeats** at the API and asserts it is successfully ingested and validated in under 10 seconds.
