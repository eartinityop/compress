import os, logging, sys
from telegram.ext import Application, CommandHandler

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

async def start_cmd(update, context):
    await update.message.reply_text("Bot is alive! 🎉")

if __name__ == "__main__":
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not set")
        sys.exit(1)

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start_cmd))
    logger.info("Starting polling...")
    app.run_polling()
