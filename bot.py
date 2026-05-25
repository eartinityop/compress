import os, requests, threading, sys, logging, asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

REPO = "eartinityop/compress"
WF_FILE = "compress.yml"
FRONTEND_TOKEN = os.environ["FRONTEND_TOKEN"]               # GitHub PAT
GROUP_CHAT_ID = int(os.environ["GROUP_CHAT_ID"])            # your group’s numeric ID
COMPRESS_CHANNEL_ID = int(os.environ["COMPRESS_CHANNEL_ID"])  # private channel ID (negative)

# ---------- Health server for Render ----------
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def start_health_server():
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
# -----------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.id != GROUP_CHAT_ID:
        return
    await update.message.reply_text("👋 Send me a video to compress. I'll ask for quality and a custom name.")

async def video_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.id != GROUP_CHAT_ID:
        return
    video = update.message.video
    if not video:
        await update.message.reply_text("Please send a video file.")
        return

    # Forward the video to the private channel (both bots are admins there)
    forwarded = await update.message.forward(chat_id=COMPRESS_CHANNEL_ID)
    context.user_data["channel_msg_id"] = forwarded.message_id

    # Store original group info for the reply later
    context.user_data["original_msg_id"] = update.message.message_id
    context.user_data["chat_id"] = update.message.chat.id
    context.user_data["original_caption"] = update.message.caption or ""

    keyboard = [
        [InlineKeyboardButton("Compress ✅", callback_data="compress")],
        [InlineKeyboardButton("Cancel ❌", callback_data="cancel")]
    ]
    await update.message.reply_text("Video received. What would you like to do?", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("cancel_run_"):
        run_id = data.split("_", 2)[2]
        url = f"https://api.github.com/repos/{REPO}/actions/runs/{run_id}/cancel"
        headers = {"Authorization": f"token {FRONTEND_TOKEN}", "Accept": "application/vnd.github+json"}
        resp = requests.post(url, headers=headers)
        if resp.status_code == 202:
            await query.edit_message_text("❌ Process cancelled by user.")
        else:
            await query.edit_message_text(f"❌ Cancellation failed: {resp.json().get('message')}")
        return

    if data == "cancel":
        await query.edit_message_text("❌ Process cancelled.")
        context.user_data.clear()
        return

    if data == "compress":
        keyboard = [
            [InlineKeyboardButton("240p", callback_data="quality_240"),
             InlineKeyboardButton("360p", callback_data="quality_360")],
            [InlineKeyboardButton("480p", callback_data="quality_480"),
             InlineKeyboardButton("720p", callback_data="quality_720")],
            [InlineKeyboardButton("1080p", callback_data="quality_1080")],
            [InlineKeyboardButton("Cancel ❌", callback_data="cancel_q")]
        ]
        await query.edit_message_text("Select the desired quality:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data.startswith("quality_"):
        quality = data.split("_")[1]
        context.user_data["quality"] = quality
        context.user_data["prompt_msg_id"] = query.message.message_id
        await query.edit_message_text("📝 Send a name for the compressed file (or type `skip`):")
        return

    if data == "cancel_q":
        await query.edit_message_text("❌ Compression cancelled.")
        context.user_data.clear()
        return

async def custom_name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.id != GROUP_CHAT_ID:
        return
    if "quality" not in context.user_data or "prompt_msg_id" not in context.user_data:
        return

    text = update.message.text.strip()
    if text.lower() == "cancel":
        await update.message.reply_text("❌ Process cancelled.")
        context.user_data.clear()
        return

    custom_name = text if text.lower() != "skip" else "video"
    await update.message.delete()        # delete user’s name message

    quality = context.user_data["quality"]
    original_msg_id = context.user_data["original_msg_id"]
    chat_id = context.user_data["chat_id"]
    original_caption = context.user_data.get("original_caption", "")
    prompt_msg_id = context.user_data["prompt_msg_id"]
    channel_msg_id = context.user_data["channel_msg_id"]

    # Edit prompt to “Workflow triggered…”
    await context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=prompt_msg_id,
        text="⏳ Workflow triggered. The worker bot will update you."
    )

    # Trigger the GitHub workflow
    url = f"https://api.github.com/repos/{REPO}/actions/workflows/{WF_FILE}/dispatches"
    headers = {"Authorization": f"token {FRONTEND_TOKEN}", "Accept": "application/vnd.github+json"}
    payload = {
        "ref": "main",
        "inputs": {
            "chat_id": str(chat_id),
            "original_message_id": str(original_msg_id),
            "channel_msg_id": str(channel_msg_id),
            "channel_id": str(COMPRESS_CHANNEL_ID),       # channel’s numeric ID
            "quality": quality,
            "custom_name": custom_name,
            "original_caption": original_caption
        }
    }
    resp = requests.post(url, json=payload, headers=headers)
    if resp.status_code != 204:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=prompt_msg_id,
            text=f"❌ Workflow trigger failed: {resp.status_code} {resp.text}"
        )
        return

    # Delete the prompt after 5 seconds
    await asyncio.sleep(5)
    await context.bot.delete_message(chat_id=chat_id, message_id=prompt_msg_id)
    context.user_data.clear()

async def post_init(application: Application):
    me = await application.bot.get_me()
    print(f"Frontend bot @{me.username} ready.")

def main():
    app = Application.builder().token(os.environ["TELEGRAM_BOT_TOKEN"]).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO, video_handler))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, custom_name_handler))
    app.run_polling()

if __name__ == "__main__":
    start_health_server()
    main()
