# ═══════════════════════════════════════════════════════
# AgroGuard-AI — Banana Disease Detection
# Production Dockerfile  |  Python 3.11 slim
# ═══════════════════════════════════════════════════════

FROM python:3.11-slim

LABEL maintainer="AgroGuard-AI Team — Annamalai University"
LABEL description="AI-powered banana crop disease detection backend"
LABEL version="1.0.0"

# ── System dependencies ─────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ───────────────────────────────────
WORKDIR /app

# ── Python dependencies (cached layer) ─────────────────
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Application source ──────────────────────────────────
COPY . .

# ── Model directory ─────────────────────────────────────
# Mount your trained model at: /app/saved_models/agroguard_banana_resnet50.pth
# Or COPY it here during build:
#   COPY saved_models/agroguard_banana_resnet50.pth saved_models/
RUN mkdir -p saved_models

# ── Non-root user (security best practice) ─────────────
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# ── Expose port ─────────────────────────────────────────
EXPOSE 8000

# ── Health check ────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c \
    "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# ── Start server ─────────────────────────────────────────
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
