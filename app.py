import os
import threading
from flask import Flask
import telebot
from config import BOT_TOKEN, ADMIN_IDS, PERSONAL_CHANNEL_ID, DB_NAME

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

@app.route('/health')
def health():
    return "OK", 200

bot = telebot.TeleBot(BOT_TOKEN)

# ===== BOT FUNKSIYALARI =====
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🎬 Salom! Men kino botman!\n\n/help - yordam olish")

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.reply_to(message, "📽️ Bot haqida:\n\n/start - boshlash\n/kino - kino qidirish")

# Kinoni qidirish uchun funksiya
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"📽️ Siz {message.text} haqida so'radingiz. Tez orada kinolar chiqariladi!")

def run_bot():
    print("Bot ishga tushmoqda...")
    try:
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"Bot xatosi: {e}")

if __name__ == '__main__':
    # Botni alohida threadda ishga tushirish
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Flask serverni ishga tushirish
    port = int(os.environ.get('PORT', 5000))
    print(f"Flask server {port} portda ishga tushmoqda...")
    app.run(host='0.0.0.0', port=port, debug=False)
