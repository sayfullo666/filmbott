import os
import re
import sqlite3
import telebot
from telebot import types
from flask import Flask, request, abort
from config import BOT_TOKEN, ADMIN_IDS, PERSONAL_CHANNEL_ID
import database as db

# Flask ilovasi
app = Flask(__name__)

# Bot obyekti
bot = telebot.TeleBot(BOT_TOKEN)
db.init_db()

# Admin holatlari va boshqa o'zgaruvchilar
admin_state = {}
user_pending_code = {}
pending_channel_posts = {}
LINK_RE = re.compile(r"t\.me/(c/)?([A-Za-z0-9_]+)/(\d+)")

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# ==================== BARCHA BOT FUNKSIYALARI ====================
# (Sizning barcha @bot.message_handler, @bot.callback_query_handler
# va boshqa funksiyalaringiz shu yerga, yuqoridagi kodga o'xshab yoziladi)

# ==================== WEBHOOK ====================
@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    else:
        abort(403)

@app.route('/')
def home():
    return "Bot is running!"

@app.route('/health')
def health():
    return "OK", 200

@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    # Webhook URL ni o'rnatish
    webhook_url = f"https://filmbott-uvy4.onrender.com/{BOT_TOKEN}"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    return f"Webhook set to {webhook_url}", 200

if __name__ == "__main__":
    # Flask serverni ishga tushirish
    port = int(os.environ.get('PORT', 5000))
    print(f"Flask server {port} portda ishga tushmoqda...")
    app.run(host='0.0.0.0', port=port, debug=False)
