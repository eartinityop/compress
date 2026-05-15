#!/bin/bash

# Download pre-compiled telegram-bot-api binary if not present
if [ ! -f ./telegram-bot-api ]; then
    echo "Downloading telegram-bot-api binary..."
    wget -q -O telegram-bot-api "https://github.com/jakbin/telegram-bot-api-binary/releases/download/2026-03-19glibc236/telegram-bot-api"
    chmod +x telegram-bot-api
fi

# Start the local API server in background
./telegram-bot-api --api-id ${TELEGRAM_API_ID} --api-hash ${TELEGRAM_API_HASH} \
    --http-port 8081 --http-ip-address "0.0.0.0" --dir /tmp/telegram-bot-api --local &
BOTAPI_PID=$!

# Wait briefly for it to start
sleep 3

# Start the Python bot
python bot.py

# When bot stops, terminate the API server
kill $BOTAPI_PID 2>/dev/null
