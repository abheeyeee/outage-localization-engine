# System Architecture

This document outlines the architectural structure of the Grid Fault Localization System and how the backend components interact.

## The Backend (FastAPI)

The backend is built using FastAPI in Python. To ensure the codebase remains maintainable, scalable, and easy to debug, I implemented a strict **Separation of Concerns** by splitting the backend logic into three core files inside the `backend/app/` directory:

### 1. `main.py` (The API Gateway)
*   **What it does:** This is the "Mouth & Ears" of the system. It runs the web server.
*   **What is inside it:** It contains the FastAPI application instance and the routing endpoints (e.g., `@app.post("/telemetry")`). 
*   **Why we need it:** We need a high-throughput async server to accept the thousands of telemetry events coming from the simulator. This file handles the HTTP traffic and passes the raw data to the Graph Engine.

### 2. `models.py` (The Validation Layer)
*   **What it does:** This acts as the "Bouncer" for our system, ensuring we are protected from Network Garbage (corrupted payloads).
*   **What is inside it:** It contains `Pydantic` schemas (e.g., `TelemetryEvent`). These define the exact required shape, data types, and required fields for incoming JSON messages.
*   **Why we need it:** In the real world, IoT devices can short out and send garbage data (like a string where an integer should be). If this garbage reaches our core algorithm, the server crashes. `models.py` uses strict typing to instantly reject bad payloads before they ever touch our core logic.

### 3. `graph_engine.py` (The Brain)
*   **What it does:** This handles all physical state tracking and the heavy mathematical processing.
*   **What is inside it:** It uses the `networkx` library to build a Directed Acyclic Graph (DAG) representing the power grid in memory. It contains the logic to load the CSVs and the **Spatial Imputation Algorithm (MST)**.
*   **Why we need it:** We need a way to track which poles have power and which are dark. Furthermore, because the assignment forces us to work with 60% missing topology data, this file contains the crucial mathematical logic (`haversine_distance`) to guess the missing wires by drawing connections between the closest geographic neighbors.
