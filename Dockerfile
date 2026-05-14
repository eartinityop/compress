FROM python:3.11-slim

# Install runtime dependencies (OpenSSL, etc.) + ffmpeg + wget
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libssl-dev \
    zlib1g-dev \
    libc-ares-dev \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Download the official pre-compiled static binary
RUN wget -O /usr/local/bin/telegram-bot-api \
    "https://github.com/tdlib/telegram-bot-api/releases/latest/download/telegram-bot-api-linux-amd64" \
    && chmod +x /usr/local/bin/telegram-bot-api

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy bot code
COPY . .

# Make start.sh executable
RUN chmod +x start.sh

# Start both services
CMD ["bash", "start.sh"]
