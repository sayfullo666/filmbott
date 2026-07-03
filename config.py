import os

# Bot tokenini Render'ning "Environment" bo'limida BOT_TOKEN nomi bilan kiriting.
# Hech qachon tokenni to'g'ridan-to'g'ri kodga yozib qo'ymang.
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Admin(lar)ning Telegram user_id larini shu yerga yozing (bir nechta bo'lishi mumkin)
ADMIN_IDS = [
    int(x) for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip()
]

# Render'dagi xizmatingizning asosiy URL manzili (webhook uchun kerak)
# Masalan: https://filmbott-uvy4.onrender.com
BASE_URL = os.environ.get("BASE_URL", "https://filmbott-uvy4.onrender.com")
