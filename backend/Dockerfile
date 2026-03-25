FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

# Use slim requirements (no torch/sentence-transformers ~2GB)
COPY requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt

COPY . .

RUN mkdir -p /app/cache_data /app/logs

# Disable local embedding model in production (uses OpenAI embeddings)
ENV LOCAL_EMBED_ENABLED=false

EXPOSE 8000

CMD ["python", "semantic_cache_server.py"]
