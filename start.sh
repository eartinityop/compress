#!/bin/bash

# Download the pre-compiled binary if needed
if [ ! -f ./telegram-bot-api ]; then
    echo "Downloading telegram-bot-api binary..."
    wget -q -O telegram-bot-api "https://github.com/jakbin/telegram-bot-api-binary/releases/download/2026-03-19glibc236/telegram-bot-api"
    chmod +x telegram-bot-api
fi

# Start the local API server, redirect output to a log file
./telegram-bot-api --api-id ${TELEGRAM_API_ID} --api-hash ${TELEGRAM_API_HASH} \
    --http-port 8081 --http-ip-address "0.0.0.0" --dir /tmp/telegram-bot-api --local \
    > /tmp/telegram-api.log 2>&1 &
BOTAPI_PID=$!

# Wait until the server can respond to a bot request (use the actual bot token)
echo "Waiting for local API server to become ready..."
for i in $(seq 1 30); do
    if curl -s "http://127.0.0.1:8081/bot${TELEGRAM_BOT_TOKEN}/getMe" | grep -q '"ok":true'; then
        echo "Local API server ready."
        break
    fi
    sleep 1
done

# If the server still isn't responding, print the last few lines of its log
if ! curl -s "http://127.0.0.1:8081/bot${TELEGRAM_BOT_TOKEN}/getMe" | grep -q '"ok":true'; then
    echo "⚠️ Local API server did NOT become ready. Logs:"
    tail -n 20 /tmp/telegram-api.log
fi

# Start the bot (it will still work even if local server fails, using public API only)
python bot.py

# When bot stops, kill the API server
kill $BOTAPI_PID 2>/dev/null
