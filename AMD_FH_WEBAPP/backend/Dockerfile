# ─── StayHeal Backend — Dockerfile ───────────────────────────────────────────
# Builds a slim production image for Cloud Run.

FROM python:3.11-slim

# Prevent .pyc files and enable unbuffered stdout (better Cloud Run logs)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install OS-level dependencies (needed by some Firebase/gRPC wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (layer-cached unless requirements change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Cloud Run injects PORT env var; our CMD uses 8080 as the default
EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]
