#!/bin/bash
set -e

# Generate data if it doesn't exist
if [ ! -f /app/backend/data/dts.csv ] || [ ! -f /app/backend/data/poles.csv ]; then
    echo "Generating grid topology data..."
    python3 /app/backend/scripts/data_generator.py
fi

# Start uvicorn
echo "Starting backend server..."
exec python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
