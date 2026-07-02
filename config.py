import os  # ⬅️ BU QATORNI QO'SHING!

# Bot sozlamalari shu yerda saqlanadi
# @BotFather dan olingan bot tokeningizni shu yerga qo'ying
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Admin(Lar)ning Telegram user ID raqamlari (bir nechta bo'lishi mumkin)
# O'z ID raqamingizni bilish uchun @userinfobot ga /start yozing
ADMIN_IDS = [6756923304]  # shu yerga o'z ID raqamingizni yozing

# Kinolar joylashgan SHAXSIY KANALINGIZNING ID raqami.
# Bot shu kanalga admin qilish qo'shilgan bo'lishi SHART (post ko'rish huquqi bilan).
PERSONAL_CHANNEL_ID = -1003721029830  # shu yerga o'z kanalingiz ID sini yozing

DB_NAME = "movies.db"