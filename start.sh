#!/bin/bash
set -e

# Start Telegram Bot API server (local) in background
telegram-bot-api --api-id ${TELEGRAM_API_ID} --api-hash ${TELEGRAM_API_HASH} \
    --http-port 8081 --http-ip-address "0.0.0.0" --dir /tmp/telegram-bot-api --local &
BOTAPI_PID=$!

# Wait for local server
echo "Waiting for local Bot API server..."
for i in $(seq 1 30); do
    if curl -s http://127.0.0.1:8081/getMe | grep -q '"ok":true'; then
        echo "Local API server ready."
        break
    fi
    sleep 1
done

# --- Test the bot token via Telegram's public API ---
echo "Testing bot token with Telegram public API..."
TOKEN_TEST=$(curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe")
if echo "$TOKEN_TEST" | grep -q '"ok":true'; then
    BOT_USERNAME=$(echo "$TOKEN_TEST" | jq -r '.result.username')
    echo "Bot token is valid (bot: @${BOT_USERNAME})."
else
    echo "=============================================="
    echo "❌ BOT TOKEN FAILED! Telegram says:"
    echo "$TOKEN_TEST"
    echo "=============================================="
    echo "Check your TELEGRAM_BOT_TOKEN environment variable on Render."
    exit 1
fi

# Delete any lingering webhook so polling works
curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/deleteWebhook" > /dev/null

# Now start the bot
python bot.py

# If bot exits, stop local API server
kill $BOTAPI_PID 2>/dev/null
