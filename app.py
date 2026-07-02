import os
import threading
from flask import Flask
import telebot  # ⬅️ BU: telebot (pyTelegramBotAPI)
from config import BOT_TOKEN, ADMIN_IDS, PERSONAL_CHANNEL_ID, DB_NAME

# Flask ilovasi
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

@app.route('/health')
def health():
    return "OK", 200

# Bot obyekti
bot = telebot.TeleBot(BOT_TOKEN)

# ============ BOT FUNKSIYALARI ============
# Sizning barcha @bot.message_handler() funksiyalaringiz shu yerga

# Masalan:
# @bot.message_handler(commands=['start'])
# def start(message):
#     bot.reply_to(message, "Salom! Men kino botman!")

def run_bot():
    """Botni ishga tushiradi"""
    print("Bot ishga tushmoqda...")
    bot.infinity_polling(skip_pending=True)

if __name__ == '__main__':
    # Botni alohida threadda ishga tushirish
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Flask serverni ishga tushirish
    port = int(os.environ.get('PORT', 5000))
    print(f"Flask server {port} portda ishga tushmoqda...")
    app.run(host='0.0.0.0', port=port, debug=False)
