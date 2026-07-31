FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend codebase
COPY backend /app/backend

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["python3", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
