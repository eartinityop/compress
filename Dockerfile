FROM aiogram/telegram-bot-api:latest

RUN apk add --no-cache python3 py3-pip ffmpeg
COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt
COPY . .
RUN chmod +x start.sh
EXPOSE 8000
CMD ["bash", "start.sh"]
