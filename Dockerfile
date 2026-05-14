# ---- Stage 1: Build ----
FROM debian:bookworm-slim AS builder

# Install build tools + dependencies + certificates
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    make \
    cmake \
    g++ \
    libssl-dev \
    zlib1g-dev \
    libc-ares-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Clone the Bot API server source (shallow clone)
RUN git clone --depth 1 https://github.com/tdlib/telegram-bot-api.git /tmp/telegram-bot-api

# Out‑of‑source build: create a separate build directory
RUN cmake -S /tmp/telegram-bot-api -B /tmp/build -DCMAKE_BUILD_TYPE=Release \
    && cmake --build /tmp/build --target telegram-bot-api -j$(nproc) \
    && cp /tmp/build/telegram-bot-api /usr/local/bin/telegram-bot-api \
    && rm -rf /tmp/telegram-bot-api /tmp/build

# ---- Stage 2: Runtime ----
FROM python:3.11-slim

# Install only runtime libraries + ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libssl-dev \
    zlib1g-dev \
    libc-ares-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the compiled binary from builder
COPY --from=builder /usr/local/bin/telegram-bot-api /usr/local/bin/telegram-bot-api

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy bot code
COPY . .

# Make start.sh executable
RUN chmod +x start.sh

# Start both services
CMD ["bash", "start.sh"]
