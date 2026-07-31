# Decision Log

This document records the meaningful architectural and product decisions made while building this system, sorted newest first. 

---

### Decision: Dual-CSV Ground Truth vs Incomplete Registry Strategy
**Date:** 2026-07-30 (Phase 1 Data Generation - Commit `a65a11d`)
**Context:** The assignment mandates that 60% of distribution transformers lack recorded wiring topology, while the simulator must physically calculate which poles lose power when a wire snaps.
**What I Chose:** I implemented a dual-export strategy in `data_generator.py`:
1. `poles.csv`: The incomplete utility registry given to `GraphEngine` (with `parent_pole_id` blank `""` for 60% of DTs).
2. `ground_truth_poles.csv`: The 100% complete physical topology map used strictly by `simulator.py`.
**Implementation Details:**
- **`has_topology` Flag:** Calculated as `[False] * 24 + [True] * 16` based on `MISSING_TOPOLOGY_PERCENTAGE = 0.60`.
- **Dual Memory Keys:** During generation, each pole dictionary stores both `"parent_pole_id": parent_pole_id if has_topology else ""` and `"_parent_pole_id": parent_pole_id`.
- **Export Overwrite:** `poles.csv` writes `parent_pole_id` as is (leaving 60% blank `""`), while `ground_truth_poles.csv` actively overwrites `parent_pole_id` with `_parent_pole_id` to restore the complete physical wiring map.
**Why I Chose It:** This ensures strict zero-cheating data separation. The simulator models physical reality, while `GraphEngine` is forced to use Geometric MST Spatial Imputation to infer the missing 60% topology.

---

### Decision: Non-Uniform Grid Generation (2,889 Poles Rationale)
**Date:** 2026-07-30 (Phase 1 Data Generation - Commit `a65a11d`)
**Context:** I needed to decide whether to generate a fixed 3,000 poles (75 poles per DT) or use a non-uniform random distribution.
**What I Chose:** I used a random uniform distribution `POLES_PER_DT_RANGE = (40, 100)` per DT, resulting in 2,889 poles across 40 DTs.
**Why I Chose It:** In real urban power distribution, transformers feed varying line lengths based on local consumer density. Non-uniform pole distribution represents authentic domain reality rather than an artificial, rigid grid.

---

### Decision: Omission of Standalone `feeders.csv` Table
**Date:** 2026-07-30 (Phase 1 Data Generation - Commit `a65a11d`)
**Context:** Reviewing `02-data-and-systems.md` §3 schema contracts revealed that `feeder_id` is defined as an attribute inside `dts.csv` and `poles.csv`.
**What I Chose:** I omitted creating a standalone `feeders.csv` file and embedded `feeder_id` directly as node metadata inside `GraphEngine`.
**Why I Chose It:** Adhering strictly to the assignment's asset database schema contract avoids redundant CSV files while retaining full support for feeder-level outage classification.

---

### Decision: Periodic Heartbeats and Watchdog Timeout Handling
**Date:** 2026-07-31
**Context:** In normal operations, IoT devices transmit periodic `heartbeat` events (e.g., every 60 seconds) with `energized=True` to confirm operational health. I needed to define how periodic heartbeats interact with state resolution.
**What I Chose:** 
1. **Heartbeat Processing:** Incoming `heartbeat` payloads refresh the pole's `is_live=True` and `last_heartbeat_ts` timestamp.
2. **Watchdog Evaluation:** If a device misses heartbeats, it enters a `silent` state. The system does not immediately declare it dark; instead, the **Implied State Post-Order Traversal** evaluates its children. If children continue emitting heartbeats (`Live`), the silent pole is flagged as a `Sensor Failure` (comms down). If all children miss heartbeats (`Dark`), it is confirmed as a `Power Loss`.
**Why I Chose It:** This prevents comms degradation (e.g., cellular signal drop) from triggering false-positive power outage alerts.

---

### Decision: Designing for Interview "Unseen Data" Curveballs
**Date:** 2026-07-31
**Context:** The evaluation criteria state that in the technical interview, reviewers will test candidates on "unseen data" or sudden constraint changes (e.g., customer complaints as a new data source, full GIS maps appearing, or mesh loops).
**What I Chose:** I designed the `GraphEngine` to be modularly decoupled from data sources. The ingestion layer translates any external signal (IoT, customer calls, SCADA) into a normalized node state update before feeding it into the post-order graph traversal engine.
**Why I Chose It:** Decoupling ingestion from graph evaluation ensures the core fault localization math remains invariant, allowing the system to easily integrate new data sources without refactoring the engine.

---

### Decision: Categorizing Faults and the "Actively Lying Sensor" Rule
**Date:** 2026-07-31
**Context:** The assignment brief demands we distinguish between a single broken span, a blown transformer (DT Fault), and a massive Feeder trip. It also explicitly notes the "broken lamp circuit" edge case: an isolated dark pole with live children is physically impossible as a line fault and means the sensor is actively lying. 
**What I Chose:** 
1. **Lying Sensors:** I updated the Implied State resolver so that even if a node *explicitly* sends a `power_lost` payload, if any of its children are live, the engine forcefully overrides the sensor and marks the node back to `Live`. We do not trust lying sensors.
2. **DT/Feeder Faults:** I updated the `localize_faults` boundary detector. Before flagging individual spans, it checks group hierarchies. If *all* DTs on a feeder are dark, it flags a `feeder_fault` and ignores the spans below. If *all* immediate children of a DT are dark, it flags a `dt_fault` and ignores the spans below. 
3. **Out-of-Order Packets:** To solve the +/- 90s clock skew constraint, I added a strict sequence check (`event.seq <= current_seq`) to the FastAPI endpoint. Older packets that arrive late are dropped, ensuring the graph is never overwritten with stale data.
**Why I Chose It:** This completely fulfills the physical constraints of the grid, ensuring our Control Room operators aren't misled by dead hardware and correctly identify the scale of the blackout.

---

### Decision: Handling Silent Sensor Failures (The "Implied State" Rule)
**Date:** 2026-07-31
**Context:** When a wire breaks, all downstream poles lose power. However, if a pole's sensor is broken (e.g., dead battery or v1.2 firmware), it will not send a `power_lost` event, appearing "live" in the database. This could trick the algorithm into thinking the fault is further downstream than it actually is.
**What I Chose:** I implemented a strict mathematical "Implied State" check in the traversal algorithm. The rule is: If a node is silent (no telemetry), we check its children. If **ANY** child is live, it mathematically proves power is flowing through the silent node, so the silent node is **Implied Live**. If **ALL** children are dark, it strongly suggests the silent node is also dark, and we push the suspected fault boundary higher up the tree.
**Why I Chose It:** This prevents dead sensors from creating false positives, allowing the algorithm to correctly identify the true span break even when intermediate devices fail to report their state.

---

### Decision: Backend Architecture (Separation of Concerns)
**Date:** 2026-07-31
**Context:** When building the FastAPI backend for ingestion and fault localization, I needed to decide how to structure the code to keep it maintainable, readable, and professional.
**What I Chose:** I split the backend into three distinct files: `models.py` (for data validation), `graph_engine.py` (for the heavy mathematical graph processing and MST imputation), and `main.py` (for the web server and API routes).
**Why I Chose It:** This enforces the "Separation of Concerns" design pattern. If I put everything in one file, it would become an unreadable monolith. By separating the web server logic from the mathematical graph logic, the system is much easier to debug and scale. 

---

### Decision: Handling 60% Missing Topology (Spatial Imputation)
**Date:** 2026-07-31
**Context:** The assignment explicitly states that ~60% of the transformers lack pole ordering (topology) data. The system must still be able to localize faults on these transformers. While brainstorming this problem, I realized that although the wiring is unknown, the physical GPS coordinates (`lat`, `lon`) of every pole are known and guaranteed.
**What I Chose:** I decided to use a **Geometric Minimum Spanning Tree (MST)** to mathematically infer the missing wiring. When the backend boots up, it will connect missing poles to their closest geographic neighbor to form a radial tree. 
**Why I Chose It:** In the real world, utilities string copper wire to the closest possible pole to save money. Therefore, geographic proximity is the most accurate heuristic for physical wiring. Furthermore, I decided to flag any fault occurring on these inferred trees with a "⚠️ Low Confidence" warning in the UI, ensuring the Control Room engineers know the system is relying on an educated guess.

---

### Decision: The Simulator's "Ground Truth" File
**Date:** 2026-07-31
**Context:** The assignment demands that 60% of the grid must have missing topology data. However, I am also required to build a Simulator that *acts* like the real physical world (snapping wires and cascading power loss). 
**What I Chose:** I decided the data generator must export *two* files: `poles.csv` (which has 60% missing data and is given to the Control Room) and `ground_truth_poles.csv` (which has 100% perfect wiring data).
**Why I Chose It:** The Simulator plays "God". It cannot simulate a blackout if it doesn't know how the wires are connected. By separating the datasets, the Simulator can perfectly calculate the physics of a blackout using the Ground Truth file, while our detection algorithm is still correctly forced to solve the assignment's missing data constraint using only `poles.csv`. 

---

### Decision: Building for Resilience (Unseen Topology & Bad Payloads)
**Date:** 2026-07-31
**Context:** I was brainstorming how the system would behave in the real world if it encounters data it has never seen before, or a physical grid structure that breaks the rules (like a loop instead of a tree).
**What I Chose:** 
1. **Topology Protection:** I decided to build infinite-loop protection into the graph traversal algorithm. The algorithm will maintain a `visited_nodes` set. If it encounters a pole it has already visited (indicating an illegal loop in the grid), it will halt traversal for that branch rather than crashing the server.
2. **Payload Protection:** I decided to use Pydantic in the FastAPI ingestion layer to strictly validate all incoming JSON telemetry.
**Why I Chose It:** A control room system cannot crash because a single device sends garbage data or a CSV export contains a wiring error. The system must degrade gracefully. This ensures the ingestion pipeline stays up even when individual messages are corrupt.

---

### Decision: Scale of Synthetic Data Generation
**Date:** 2026-07-31
**Context:** The brief mentions the real division has 38,400 poles. I had to decide whether to generate all 38,400 for the simulation, or a smaller subset. The data is not provided; I must write a script to generate it.
**What I Chose:** I decided to generate a synthetic grid of approximately 3,000 poles across a few dozen Distribution Transformers.
**What I Rejected:** Generating the full 38,400 poles. 
**Why I Chose It:** The FAQ explicitly states that a few thousand poles is plenty. More importantly, rendering 38,000 DOM elements on a web map at once will cause significant browser lag. 3,000 poles is the sweet spot: it is large enough to mathematically prove the graph algorithms work at scale, but small enough to ensure the operator console UI remains lightning fast during the demo.
