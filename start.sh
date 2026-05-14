#!/bin/bash

echo "Starting local Bot API server..."
telegram-bot-api --api-id ${TELEGRAM_API_ID} --api-hash ${TELEGRAM_API_HASH} \
    --http-port 8081 --http-ip-address "0.0.0.0" --dir /tmp/telegram-bot-api --local &
BOTAPI_PID=$!

# Wait a bit for the server to start, but don't block forever
echo "Waiting up to 10 seconds for local API server..."
for i in $(seq 1 10); do
    if curl -s http://127.0.0.1:8081/getMe | grep -q '"ok":true'; then
        echo "Local Bot API server is ready."
        break
    fi
    sleep 1
done

# Even if the local server isn't ready, we still start the bot
echo "Starting Python bot..."
python bot.py

# If the bot exits, stop the local API server (if it's running)
kill $BOTAPI_PID 2>/dev/null
