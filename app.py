import os
import logging
from flask import Flask
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio
import threading

# Flask ilovasi
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

@app.route('/health')
def health():
    return "OK", 200

# ============ BOT KODINGIZNI SHU YERGA QO'YING ============
# Sizning barcha bot funksiyalaringiz (start, help, kinolar va h.k.)
# Masalan:
# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await update.message.reply_text("Salom! Men kino botman!")

def run_bot():
    """Botni alohida threadda ishga tushiradi"""
    from config import BOT_TOKEN, ADMIN_IDS, PERSONAL_CHANNEL_ID, DB_NAME
    
    # Botni sozlash
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Handlerlarni qo'shing (o'z kodlaringizni shu yerga yozing)
    # application.add_handler(CommandHandler("start", start))
    # application.add_handler(...)
    
    # Botni ishga tushirish
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    # Botni alohida threadda ishga tushirish
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Flask serverni ishga tushirish
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
