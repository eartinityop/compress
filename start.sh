#!/bin/bash
set -e

# Start Telegram Bot API server on IPv4, local mode
telegram-bot-api --api-id ${TELEGRAM_API_ID} --api-hash ${TELEGRAM_API_HASH} \
    --http-port 8081 --http-ip-address "0.0.0.0" --dir /tmp/telegram-bot-api --local &
BOTAPI_PID=$!

# Wait until the server actually responds to a bot request
echo "Waiting for Bot API server to become ready..."
for i in $(seq 1 30); do
    if curl -s "http://127.0.0.1:8081/bot${TELEGRAM_BOT_TOKEN}/getMe" | grep -q '"ok":true'; then
        echo "Bot API server is ready."
        break
    fi
    sleep 1
done

# If server didn't start, exit
if ! kill -0 $BOTAPI_PID 2>/dev/null; then
    echo "Bot API server failed to start."
    exit 1
fi

# Start the Python bot
python bot.py

# When bot stops, shut down the API server
kill $BOTAPI_PID 2>/dev/null
