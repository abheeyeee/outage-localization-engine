FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend codebase
COPY backend /app/backend

ENV PYTHONPATH=/app

EXPOSE 8000

# Set entrypoint
RUN chmod +x /app/backend/entrypoint.sh
CMD ["/app/backend/entrypoint.sh"]
