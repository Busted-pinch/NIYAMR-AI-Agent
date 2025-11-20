# Dockerfile — Python environment for the NIYAMR-AI-Agent pipeline
FROM python:3.11-slim

# system deps for pdf processing and ffmpeg for video if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential poppler-utils tesseract-ocr ffmpeg \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency list and install
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip
RUN pip install -r /app/requirements.txt

# Copy project files
COPY . /app

# Default to an interactive shell; run python scripts manually or with docker compose run
CMD ["/bin/bash"]
