# Decision Log

This document records the meaningful architectural and product decisions made while building this system, sorted newest first. 

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
