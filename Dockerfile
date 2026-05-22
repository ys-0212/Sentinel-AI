# =============================================================================
# CyberSafe Backend Dockerfile
# Single-stage Dockerfile for FastAPI + ML modules
# =============================================================================
# Build:   docker build -t cybersafe-backend .
# Run:     docker run -p 8000:8000 --env-file .env cybersafe-backend
# =============================================================================

FROM python:3.10-slim

# Prevent Python from buffering stdout/stderr (better for Docker logs)
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
# - tesseract-ocr: for OCR (pytesseract)
# - ffmpeg: for audio/video processing (pydub)
# - libsndfile1: for audio file support
# - poppler-utils: for PDF processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    ffmpeg \
    libsndfile1 \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
# This is crucial - uvicorn api.main:app expects this structure
WORKDIR /app

# Copy requirements first (better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (excluding items in .dockerignore)
# NOTE: ML models, PDFs, uploads, and database are volume-mounted at runtime
COPY api/ ./api/
COPY IAP_AI_Malicious_Detector/*.py ./IAP_AI_Malicious_Detector/
COPY TypingIPVPNDetector/*.py ./TypingIPVPNDetector/
COPY summarizer/*.py ./summarizer/
COPY call_scam_detector/*.py ./call_scam_detector/
COPY chatbot/*.py ./chatbot/

# Create directories for volume mounts
RUN mkdir -p api/uploads \
    && mkdir -p call_scam_detector/model-en \
    && mkdir -p call_scam_detector/model-hi

# Expose the FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

# Run the FastAPI application
# Using the same command that works locally
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
