# app.py - Render uchun moslashtirilgan kino bot
import os
import threading
import re
import telebot
from telebot import types
from flask import Flask
from config import BOT_TOKEN, ADMIN_IDS, PERSONAL_CHANNEL_ID
import database as db

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
db.init_db()

# Admin uchun vaqtinchalik holatlarni saqlash
admin_state = {}
user_pending_code = {}
pending_channel_posts = {}

LINK_RE = re.compile(r"t\.me/(c/)?([A-Za-z0-9_]+)/(\d+)")

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# ==================== KLAVIATURALAR ====================

def admin_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        types.KeyboardButton("➕ Kino qo'shish"),
        types.KeyboardButton("🗑 Kino o'chirish"),
    )
    kb.add(
        types.KeyboardButton("📊 Statistika"),
    )
    kb.add(
        types.KeyboardButton("➕ Majburiy kanal qo'shish"),
        types.KeyboardButton("➖ Majburiy kanal o'chirish"),
    )
    kb.add(
        types.KeyboardButton("📃 Kanallar ro'yxati"),
        types.KeyboardButton("❌ Admin panelni yopish"),
    )
    return kb

def user_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton("🎬 Kino qidirish"))
    return kb

def subscribe_keyboard(channels):
    kb = types.InlineKeyboardMarkup()
    for ch in channels:
        link = ch["username"]
        if link.startswith("@"):
            link = f"https://t.me/{link[1:]}"
        kb.add(types.InlineKeyboardButton(text=f"➕ {ch['title']}", url=link))
    kb.add(types.InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_sub"))
    return kb

# ==================== YORDAMCHI FUNKSIYALAR ====================

def check_subscription(user_id: int):
    channels = db.get_channels()
    not_subscribed = []
    for ch in channels:
        try:
            member = bot.get_chat_member(ch["channel_id"], user_id)
            if member.status in ("left", "kicked"):
                not_subscribed.append(ch)
        except Exception:
            not_subscribed.append(ch)
    return (len(not_subscribed) == 0), not_subscribed

def send_movie_to_user(chat_id: int, code: str):
    movie = db.get_movie(code)
    if not movie:
        bot.send_message(chat_id, "❌ Bunday kodli kino topilmadi.")
        return

    title = movie["title"] or "Nomsiz"
    description = movie["description"] or ""
    caption = f"🎬 <b>{title}</b>"
    if description:
        caption += f"\n\n{description}"
    caption += f"\n\n🔑 Kod: <code>{code}</code>"

    try:
        bot.copy_message(
            chat_id,
            movie["channel_id"],
            movie["message_id"],
            caption=caption,
            parse_mode="HTML",
        )
        db.increment_views(code)
    except Exception as e:
        bot.send_message(
            chat_id,
            "⚠️ Kino yuborishda xatolik yuz berdi. Iltimos, admin bilan bog'laning.",
        )
        print("Xatolik (send_movie_to_user):", e)

# ==================== /start ====================

@bot.message_handler(commands=["start"])
def cmd_start(message):
    user_id = message.from_user.id
    db.add_user(user_id, message.from_user.username or "")
    admin_state.pop(user_id, None)

    if is_admin(user_id):
        bot.send_message(
            message.chat.id,
            "Assalomu alaykum, Admin!\nKerakli bo'limni tanlang yoki /admin buyrug'ini yuboring.",
            reply_markup=user_menu(),
        )
    else:
        bot.send_message(
            message.chat.id,
            "🎬 Assalomu alaykum!\n\n"
            "Kino kodini yuboring, men sizga kinoni topib beraman.\n"
            "Masalan: 001",
            reply_markup=user_menu(),
        )

# ==================== ADMIN PANEL ====================

@bot.message_handler(commands=["admin"])
def cmd_admin(message):
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "❌ Sizda bu buyruqdan foydalanish huquqi yo'q.")
        return
    bot.send_message(message.chat.id, "🔐 Admin panelga xush kelibsiz.", reply_markup=admin_menu())

@bot.message_handler(func=lambda m: m.text == "❌ Admin panelni yopish")
def close_admin_panel(message):
    if not is_admin(message.from_user.id):
        return
    admin_state.pop(message.from_user.id, None)
    bot.send_message(message.chat.id, "Admin panel yopildi.", reply_markup=user_menu())

@bot.message_handler(func=lambda m: m.text == "📊 Statistika")
def show_stats(message):
    if not is_admin(message.from_user.id):
        return
    total_users = db.users_count()
    total_movies = db.movies_count()
    top = db.top_movies(10)

    text = f"📊 <b>Statistika</b>\n\n"
    text += f"👤 Foydalanuvchilar soni: <b>{total_users}</b>\n"
    text += f"🎬 Kinolar soni: <b>{total_movies}</b>\n\n"
    text += "🔥 <b>Eng ko'p ko'rilgan kinolar:</b>\n"

    if not top:
        text += "Hozircha kino qo'shilmagan."
    else:
        for i, m in enumerate(top, start=1):
            title = m["title"] or "Nomsiz"
            text += f"{i}. {title} (kod: {m['code']}) — {m['views']} marta ko'rilgan\n"

    bot.send_message(message.chat.id, text, parse_mode="HTML")

# ---------- Kino qo'shish ----------

@bot.message_handler(func=lambda m: m.text == "➕ Kino qo'shish")
def start_add_movie(message):
    if not is_admin(message.from_user.id):
        return
    admin_state[message.from_user.id] = {"action": "waiting_movie_source"}
    bot.send_message(
        message.chat.id,
        "🎬 Kino qo'shish uchun quyidagilardan birini bajaring:\n\n"
        "1️⃣ Kanalga video joylang — bot avtomatik aniqlab, sizga xabar yuboradi;\n"
        "2️⃣ Kanaldagi postni botga <b>forward</b> qiling (agar forward ishlasa);\n"
        "3️⃣ Yoki postning havolasini yuboring, masalan:\n"
        "<code>https://t.me/kanalingiz/123</code>\n"
        "(bu ayniqsa boshqa manbadan olingan, forward qilinmaydigan videolar uchun ishlaydi)",
        parse_mode="HTML",
    )

# ---------- Kino o'chirish ----------

@bot.message_handler(func=lambda m: m.text == "🗑 Kino o'chirish")
def start_delete_movie(message):
    if not is_admin(message.from_user.id):
        return
    admin_state[message.from_user.id] = {"action": "waiting_delete_code"}
    bot.send_message(message.chat.id, "🗑 O'chirmoqchi bo'lgan kinoning kodini yuboring:")

# ---------- Majburiy kanal qo'shish ----------

@bot.message_handler(func=lambda m: m.text == "➕ Majburiy kanal qo'shish")
def start_add_channel(message):
    if not is_admin(message.from_user.id):
        return
    admin_state[message.from_user.id] = {"action": "waiting_channel_forward"}
    bot.send_message(
        message.chat.id,
        "📢 Majburiy obuna qilinishi kerak bo'lgan kanaldan istalgan postni "
        "botga <b>forward</b> qiling.\n(Bot kanalda admin bo'lishi shart)",
        parse_mode="HTML",
    )

# ---------- Majburiy kanal o'chirish ----------

@bot.message_handler(func=lambda m: m.text == "➖ Majburiy kanal o'chirish")
def start_remove_channel(message):
    if not is_admin(message.from_user.id):
        return
    channels = db.get_channels()
    if not channels:
        bot.send_message(message.chat.id, "Hozircha majburiy kanallar qo'shilmagan.")
        return
    kb = types.InlineKeyboardMarkup()
    for ch in channels:
        kb.add(
            types.InlineKeyboardButton(
                text=f"🗑 {ch['title']}", callback_data=f"delch:{ch['channel_id']}"
            )
        )
    bot.send_message(message.chat.id, "O'chirmoqchi bo'lgan kanalni tanlang:", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "📃 Kanallar ro'yxati")
def list_channels(message):
    if not is_admin(message.from_user.id):
        return
    channels = db.get_channels()
    if not channels:
        bot.send_message(message.chat.id, "Hozircha majburiy kanallar qo'shilmagan.")
        return
    text = "📃 <b>Majburiy obuna kanallari:</b>\n\n"
    for ch in channels:
        text += f"• {ch['title']} ({ch['username']})\n"
    bot.send_message(message.chat.id, text, parse_mode="HTML")

# ==================== FORWARD QILINGAN XABARLAR ====================

@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.forward_from_chat is not None,
                      content_types=["text", "photo", "video", "document", "audio", "animation"])
def handle_forward(message):
    state = admin_state.get(message.from_user.id, {})
    action = state.get("action")
    fwd_chat = message.forward_from_chat

    if action == "waiting_movie_source":
        admin_state[message.from_user.id] = {
            "action": "waiting_movie_code",
            "channel_id": fwd_chat.id,
            "message_id": message.forward_from_message_id,
        }
        bot.send_message(
            message.chat.id,
            "✅ Kino qabul qilindi.\nEndi ushbu kino uchun <b>kod</b> yuboring (masalan: 001):",
            parse_mode="HTML",
        )
        return

    if action == "waiting_channel_forward":
        username = fwd_chat.username
        if username:
            admin_state.pop(message.from_user.id, None)
            db.add_channel(fwd_chat.id, f"@{username}", fwd_chat.title or "Kanal")
            bot.send_message(
                message.chat.id,
                f"✅ Kanal majburiy obuna ro'yxatiga qo'shildi: {fwd_chat.title}",
                reply_markup=admin_menu(),
            )
        else:
            admin_state[message.from_user.id] = {
                "action": "waiting_channel_link",
                "channel_id": fwd_chat.id,
                "title": fwd_chat.title or "Kanal",
            }
            bot.send_message(
                message.chat.id,
                "Bu yopiq kanal ekan, username topilmadi.\n"
                "Iltimos, kanalning taklif havolasini (invite link) yuboring:",
            )
        return

    bot.send_message(
        message.chat.id,
        "Avval admin paneldan '➕ Kino qo'shish' yoki '➕ Majburiy kanal qo'shish' tugmasini bosing.",
    )

# ==================== KANALGA AVTOMATIK ULANISH ====================

@bot.channel_post_handler(content_types=["video", "document", "animation"])
def on_new_channel_video(message):
    if message.chat.id != PERSONAL_CHANNEL_ID:
        return

    pending_channel_posts[message.message_id] = {
        "channel_id": message.chat.id,
        "message_id": message.message_id,
    }

    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton(
            "➕ Botga qo'shish", callback_data=f"addmovie:{message.message_id}"
        )
    )

    for admin_id in ADMIN_IDS:
        try:
            bot.send_message(
                admin_id,
                "🎬 Kanalga yangi video joylandi.\n"
                "Uni botga qo'shish uchun tugmani bosing:",
                reply_markup=kb,
            )
        except Exception as e:
            print("Admin xabar yuborishda xatolik:", e)

@bot.callback_query_handler(func=lambda c: c.data.startswith("addmovie:"))
def callback_add_movie(call):
    if not is_admin(call.from_user.id):
        return
    msg_id = int(call.data.split(":")[1])
    info = pending_channel_posts.get(msg_id)
    if not info:
        bot.answer_callback_query(call.id, "❌ Ma'lumot topilmadi yoki eskirgan.", show_alert=True)
        return

    admin_state[call.from_user.id] = {
        "action": "waiting_movie_code",
        "channel_id": info["channel_id"],
        "message_id": info["message_id"],
    }
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "🔢 Ushbu kino uchun kod kiriting (masalan: 001):")

# ==================== ADMIN MATNLI JAVOBLARI ====================

@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.from_user.id in admin_state)
def handle_admin_state_text(message):
    state = admin_state.get(message.from_user.id, {})
    action = state.get("action")
    text = message.text.strip() if message.text else ""

    if action == "waiting_movie_source":
        match = LINK_RE.search(text)
        if not match:
            bot.send_message(
                message.chat.id,
                "❌ Havola noto'g'ri formatda.\n"
                "Namuna: https://t.me/kanalingiz/123 yoki kinoni forward qiling.",
            )
            return

        is_private, chat_ref, msg_id = match.groups()
        msg_id = int(msg_id)

        if is_private:
            channel_id = int("-100" + chat_ref)
        else:
            try:
                chat = bot.get_chat(f"@{chat_ref}")
                channel_id = chat.id
            except Exception as e:
                bot.send_message(
                    message.chat.id,
                    "❌ Kanalni topib bo'lmadi. Bot shu kanalda admin ekanligiga ishonch hosil qiling.",
                )
                print("Xatolik (get_chat):", e)
                return

        admin_state[message.from_user.id] = {
            "action": "waiting_movie_code",
            "channel_id": channel_id,
            "message_id": msg_id,
        }
        bot.send_message(
            message.chat.id,
            "✅ Post qabul qilindi.\nEndi ushbu kino uchun <b>kod</b> yuboring (masalan: 001):",
            parse_mode="HTML",
        )
        return

    if action == "waiting_movie_code":
        code = text
        if not code:
            bot.send_message(message.chat.id, "Iltimos, to'g'ri kod kiriting.")
            return
        if db.get_movie(code):
            bot.send_message(
                message.chat.id,
                "⚠️ Bu kod band. Boshqa kod kiriting yoki avval eskisini o'chiring.",
            )
            return
        state["code"] = code
        state["action"] = "waiting_movie_title"
        admin_state[message.from_user.id] = state
        bot.send_message(message.chat.id, "📝 Endi kino <b>nomini</b> yuboring:", parse_mode="HTML")
        return

    if action == "waiting_movie_title":
        title = text
        if not title:
            bot.send_message(message.chat.id, "Iltimos, kino nomini kiriting.")
            return
        state["title"] = title
        state["action"] = "waiting_movie_description"
        admin_state[message.from_user.id] = state
        bot.send_message(
            message.chat.id,
            "🗒 Endi kino haqida qisqacha <b>ma'lumot</b> (janr, yil, tavsif va h.k.) yuboring.\n"
            "Agar kerak bo'lmasa, \"-\" belgisini yuboring.",
            parse_mode="HTML",
        )
        return

    if action == "waiting_movie_description":
        description = "" if text == "-" else text
        db.add_movie(
            state["code"],
            state["channel_id"],
            state["message_id"],
            state["title"],
            description,
        )
        admin_state.pop(message.from_user.id, None)
        pending_channel_posts.pop(state["message_id"], None)
        bot.send_message(
            message.chat.id,
            f"✅ Kino saqlandi!\n\n🔑 Kod: <b>{state['code']}</b>\n🎬 Nomi: {state['title']}",
            parse_mode="HTML",
            reply_markup=admin_menu(),
        )
        return

    if action == "waiting_delete_code":
        code = text
        if db.delete_movie(code):
            bot.send_message(message.chat.id, f"🗑 '{code}' kodli kino o'chirildi.", reply_markup=admin_menu())
        else:
            bot.send_message(message.chat.id, "❌ Bunday kodli kino topilmadi.")
        admin_state.pop(message.from_user.id, None)
        return

    if action == "waiting_channel_link":
        link = text
        if not link:
            bot.send_message(message.chat.id, "Iltimos, to'g'ri havola kiriting.")
            return
        db.add_channel(state["channel_id"], link, state["title"])
        admin_state.pop(message.from_user.id, None)
        bot.send_message(
            message.chat.id,
            f"✅ Kanal majburiy obuna ro'yxatiga qo'shildi: {state['title']}",
            reply_markup=admin_menu(),
        )
        return

    admin_state.pop(message.from_user.id, None)

# ==================== INLINE CALLBACKLAR ====================

@bot.callback_query_handler(func=lambda c: c.data == "check_sub")
def callback_check_sub(call):
    user_id = call.from_user.id
    ok, not_subscribed = check_subscription(user_id)

    if ok:
        bot.answer_callback_query(call.id, "✅ Obuna tasdiqlandi!")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        code = user_pending_code.pop(user_id, None)
        if code:
            send_movie_to_user(call.message.chat.id, code)
        else:
            bot.send_message(call.message.chat.id, "Endi kino kodini yuborishingiz mumkin.")
    else:
        bot.answer_callback_query(call.id, "❌ Hali barcha kanallarga obuna bo'lmagansiz!", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("delch:"))
def callback_delete_channel(call):
    if not is_admin(call.from_user.id):
        return
    channel_id = int(call.data.split(":")[1])
    db.remove_channel(channel_id)
    bot.answer_callback_query(call.id, "Kanal o'chirildi.")
    bot.edit_message_text(
        "✅ Kanal majburiy obuna ro'yxatidan o'chirildi.",
        call.message.chat.id,
        call.message.message_id,
    )

# ==================== ODDIY FOYDALANUVCHI: KINO KODI ====================

@bot.message_handler(func=lambda m: m.text == "🎬 Kino qidirish")
def ask_for_code(message):
    bot.send_message(message.chat.id, "Kino kodini yuboring:")

@bot.message_handler(content_types=["text"])
def handle_text(message):
    user_id = message.from_user.id
    db.add_user(user_id, message.from_user.username or "")

    code = message.text.strip()
    if not code:
        return

    ok, not_subscribed = check_subscription(user_id)
    if not ok:
        user_pending_code[user_id] = code
        bot.send_message(
            message.chat.id,
            "⚠️ Kinodan foydalanish uchun quyidagi kanal(lar)ga obuna bo'ling, "
            "so'ng '✅ Obunani tekshirish' tugmasini bosing:",
            reply_markup=subscribe_keyboard(not_subscribed),
        )
        return

    send_movie_to_user(message.chat.id, code)

# ==================== BOTNI ISHGA TUSHIRISH (RENDER UCHUN) ====================

def run_bot():
    """Botni alohida threadda ishga tushiradi"""
    print("Bot ishga tushmoqda...")
    try:
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"Bot xatosi: {e}")

if __name__ == "__main__":
    # Botni alohida threadda ishga tushirish
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Flask serverni ishga tushirish
    port = int(os.environ.get('PORT', 5000))
    print(f"Flask server {port} portda ishga tushmoqda...")
    app.run(host='0.0.0.0', port=port, debug=False)
