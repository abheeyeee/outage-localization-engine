# Deployment & Troubleshooting

This system is designed to be run via `docker compose`. Follow these steps if you encounter issues during deployment or evaluation.

## Prerequisites
- Docker Engine and Docker Compose (v2) installed.
- Ports `8000` and `5173` available on the host machine.

## Common Issues & Fixes

### 1. Port Conflicts (Address Already In Use)
**Symptom:** `Error starting userland proxy: listen tcp4 0.0.0.0:8000: bind: address already in use`
**Fix:** Another service is using the port. You can change the mapped port in `docker-compose.yml`:
```yaml
  backend:
    ports:
      - "8001:8000" # Maps host port 8001 to container port 8000
```
*Note:* If you change the backend port, you MUST update the frontend's environment variable:
```bash
VITE_API_BASE=http://localhost:8001 docker compose up --build
```

### 2. CORS Errors in the Browser
**Symptom:** The frontend loads but shows no data, and the browser console says "Cross-Origin Request Blocked".
**Fix:** The backend is configured to accept CORS from `*` in development, but if it's deployed to a public server, ensure the frontend is reaching the backend via the correct domain (not `localhost`). Verify your `VITE_API_BASE` points to the public backend IP/domain.

### 3. Missing Grid Data (Blank Map)
**Symptom:** The API returns `{"status":"healthy","poles_loaded":0,"dts_loaded":0}`.
**Fix:** The entrypoint script `entrypoint.sh` might have failed to run or the volume mount failed. 
1. Bring down the containers: `docker compose down -v`
2. Ensure `backend/scripts/data_generator.py` is executable.
3. Bring it back up: `docker compose up --build`

### 4. Telemetry Endpoint Failing (422 Unprocessable Entity)
**Symptom:** Simulating a fault returns an error in the frontend.
**Fix:** Ensure you are passing the correct JSON body. The API expects strict validation via Pydantic. Ensure `fault_type` is one of `span`, `dt`, `feeder`, or `scheduled`.
