FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    SUBSCRIPTIONS_PATH=/app/data/subscriptions.json

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY app ./app

RUN useradd -ms /bin/bash appuser

RUN mkdir -p /app/data && chown -R appuser:appuser /app/data

USER appuser

VOLUME /app/data

CMD ["python", "-m", "app"]
