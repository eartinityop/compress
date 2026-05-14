import os, sys, logging, threading, requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

# Force immediate output to Render logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

print("===== Container started =====", flush=True)

# ========== CONFIG ==========
REPO = "eartinityop/compress"
WF_FILE = "compress.yml"
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
# =============================

SERVICE_URL = os.environ.get("RENDER_EXTERNAL_URL", "http://localhost:8000")
BASE_URL = f"{SERVICE_URL}/bot"
BOT_API_LOCAL = "http://localhost:8081"

# ---------- Proxy Server ----------
class ProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/bot") or self.path.startswith("/file"):
            self._proxy("GET")
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
    def do_POST(self):
        if self.path.startswith("/bot") or self.path.startswith("/file"):
            self._proxy("POST")
        else:
            self.send_response(404)
            self.end_headers()
    def _proxy(self, method):
        url = BOT_API_LOCAL + self.path
        body = self.rfile.read(int(self.headers.get('Content-Length', 0))) if self.headers.get('Content-Length') else None
        headers = {k:v for k,v in self.headers.items() if k.lower()!='host'}
        resp = requests.request(method, url, data=body, headers=headers)
        self.send_response(resp.status_code)
        for k,v in resp.headers.items():
            self.send_header(k,v)
        self.end_headers()
        self.wfile.write(resp.content)

def start_proxy():
    port = int(os.environ.get("PORT", 8000))
    HTTPServer(("0.0.0.0", port), ProxyHandler).serve_forever()
# -------------------------------

async def start(update, context):
    await update.message.reply_text("Bot ready! Send a video.")

async def video_handler(update, context):
    context.user_data["original_caption"] = update.message.caption or ""
    video = update.message.video
    if not video:
        await update.message.reply_text("Please send a video file.")
        return
    context.user_data["file_id"] = video.file_id
    context.user_data["user_id"] = update.message.chat_id
    context.user_data["original_msg_id"] = update.message.message_id
    keyboard = [[
        InlineKeyboardButton("Compress ✅", callback_data="compress"),
        InlineKeyboardButton("Cancel ❌", callback_data="cancel")
    ]]
    await update.message.reply_text("Video received.", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "cancel":
        await query.edit_message_text("❌ Cancelled.")
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
        await query.edit_message_text("Select quality:", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    if data.startswith("quality_"):
        quality = data.split("_")[1]
        f_id = context.user_data.get("file_id")
        u_id = context.user_data.get("user_id")
        orig_id = context.user_data.get("original_msg_id")
        if not all([f_id, u_id, orig_id]):
            await query.edit_message_text("Error: missing data.")
            return
        await query.edit_message_text("⏳ Triggering workflow...")
        mid = query.message.message_id
        payload = {
            "ref": "main",
            "inputs": {
                "file_id": f_id,
                "user_id": str(u_id),
                "quality": quality,
                "message_id": str(mid),
                "original_message_id": str(orig_id),
                "original_caption": context.user_data.get("original_caption", ""),
                "api_base_url": BASE_URL
            }
        }
        r = requests.post(f"https://api.github.com/repos/{REPO}/actions/workflows/{WF_FILE}/dispatches",
                          json=payload,
                          headers={"Authorization": f"token {GITHUB_TOKEN}",
                                   "Accept": "application/vnd.github+json"})
        if r.status_code != 204:
            await query.edit_message_text(f"❌ Trigger failed: {r.status_code}")
        return

async def post_init(app):
    await app.bot.delete_webhook(drop_pending_updates=True)
    me = await app.bot.get_me()
    logger.info(f"Bot @{me.username} is alive.")

def main():
    print("Building Application...", flush=True)
    app = Application.builder().token(os.environ["TELEGRAM_BOT_TOKEN"]).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO, video_handler))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("Starting polling...", flush=True)
    app.run_polling()

if __name__ == "__main__":
    print("Launching proxy thread...", flush=True)
    threading.Thread(target=start_proxy, daemon=True).start()
    main()
