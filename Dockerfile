FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv .venv
COPY requirements.txt ./
# Install CPU-only PyTorch first (pocket-tts dependency) to avoid pulling
# the massive CUDA-enabled build (~2GB). CPU-only is ~200MB instead.
RUN .venv/bin/pip install --upgrade pip && \
    .venv/bin/pip install torch --index-url https://download.pytorch.org/whl/cpu && \
    .venv/bin/pip install -r requirements.txt

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

# System dependencies for TTS providers:
# - espeak-ng: PyTTS backend
# - ffmpeg: Audio format conversion (pydub)
RUN apt-get update && apt-get install -y --no-install-recommends \
    espeak-ng \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /app/.venv .venv/
COPY . .
CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
