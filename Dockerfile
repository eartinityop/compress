FROM aiogram/telegram-bot-api:latest

# Install Python, ffmpeg, and pip (Alpine packages)
RUN apk add --no-cache \
    python3 \
    py3-pip \
    ffmpeg

# Install Python dependencies (allow system packages for Alpine)
COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Copy your bot code
COPY . .

# Make start.sh executable
RUN chmod +x start.sh

# Expose the port Render uses (bot proxy runs on 8000)
EXPOSE 8000

# Start both services
CMD ["bash", "start.sh"]
