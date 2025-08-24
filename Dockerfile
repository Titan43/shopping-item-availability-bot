FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SUBSCRIPTIONS_PATH=/app/data/subscriptions.json

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget gnupg unzip \
    chromium \
    chromium-driver \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY app ./app

RUN useradd -ms /bin/bash appuser && \
    mkdir -p /app/data && chown -R appuser:appuser /app/data

USER appuser

VOLUME /app/data

CMD ["python", "-m", "app"]
