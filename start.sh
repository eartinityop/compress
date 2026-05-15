#!/bin/bash

# Download the binary from your own release (only if not present)
if [ ! -f ./telegram-bot-api ]; then
    echo "Downloading telegram-bot-api..."
    wget -q -O telegram-bot-api "https://github.com/eartinityop/compress/releases/download/botapi-binary/telegram-bot-api-linux-amd64"
    chmod +x telegram-bot-api
fi

# Start local API server
./telegram-bot-api --api-id ${TELEGRAM_API_ID} --api-hash ${TELEGRAM_API_HASH} \
    --http-port 8081 --http-ip-address "0.0.0.0" --dir /tmp/telegram-bot-api --local \
    > /tmp/telegram-api.log 2>&1 &
BOTAPI_PID=$!

# Wait for readiness
echo "Waiting for local API server..."
for i in $(seq 1 30); do
    if curl -s "http://127.0.0.1:8081/bot${TELEGRAM_BOT_TOKEN}/getMe" | grep -q '"ok":true'; then
        echo "Local API server ready."
        break
    fi
    sleep 1
done

# Start bot (always works with public API)
python bot.py

# Cleanup
kill $BOTAPI_PID 2>/dev/null
