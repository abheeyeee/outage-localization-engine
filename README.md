# Grid Fault Localization Engine

This repository contains the Grid Fault Localization System. The system ingests noisy, lossy "dying gasp" telemetry from grid IoT devices, spatially imputes missing topology data, and uses a Topological Graph Engine to precisely localize span and equipment faults while aggressively preventing ticket storms via Hierarchical Aggregation.

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
- **Frontend URL:** [PLACEHOLDER_FOR_FRONTEND_URL]
- **Backend API URL:** [PLACEHOLDER_FOR_BACKEND_URL]
- **Demo Video (5-min):** [PLACEHOLDER_FOR_LOOM_OR_YOUTUBE_LINK]

*(Note to Reviewer: The live demo is hosted on a free tier. Please allow 30-60 seconds for the containers to cold-start when you first open the URL before assuming the system is broken.)*

## Documentation Map

For grading and review, please refer to the following documents in this repository:

1. **[ARCHITECTURE.md](./ARCHITECTURE.md)**: Details the Topological Graph Engine, spatial imputation algorithm, the two-pass Implied State resolver for quiet failures, and the backend data model.
2. **[AI-WORKFLOW.md](./AI-WORKFLOW.md)**: Concrete examples of how LLMs failed, hallucinated, and were corrected during the engineering of this system.
3. **[DECISIONS.md](./DECISIONS.md)**: A log of key technical tradeoffs made, including our strategy for preventing ticket storms and what we know is currently fragile.
4. **[DEPLOYMENT.md](./DEPLOYMENT.md)**: Troubleshooting guide for Docker, CORS, and port conflicts.
