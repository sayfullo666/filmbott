import os
import telebot
from telebot import types
from flask import Flask, request, abort
from config import BOT_TOKEN, ADMIN_IDS, BASE_URL
import database as db

app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN)
db.init_db()

# Adminning joriy holati: user_id -> {"step": "...", "data": {...}}
admin_state = {}

BTN_ADD_MOVIE = "➕ Kino qo'shish"
BTN_DEL_MOVIE = "🗑 Kino o'chirish"
BTN_MOVIE_LIST = "🎬 Kinolar ro'yxati"
BTN_STATS = "📊 Statistika"
BTN_ADD_CHANNEL = "➕ Majburiy kanal qo'shish"
BTN_DEL_CHANNEL = "➖ Majburiy kanal o'chirish"
BTN_CHANNEL_LIST = "📋 Kanallar ro'yxati"
BTN_CLOSE_PANEL = "❌ Admin panelni yopish"


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def admin_panel_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(BTN_ADD_MOVIE, BTN_DEL_MOVIE)
    markup.add(BTN_MOVIE_LIST)
    markup.add(BTN_STATS)
    markup.add(BTN_ADD_CHANNEL, BTN_DEL_CHANNEL)
    markup.add(BTN_CHANNEL_LIST)
    markup.add(BTN_CLOSE_PANEL)
    return markup


def reset_admin_state(user_id: int):
    admin_state.pop(user_id, None)


# ==================== OBUNA TEKSHIRISH ====================

def get_not_subscribed_channels(user_id: int):
    not_subscribed = []
    for ch in db.get_channels():
        try:
            member = bot.get_chat_member(ch["channel_id"], user_id)
            if member.status not in ("member", "administrator", "creator"):
                not_subscribed.append(ch)
        except Exception:
            # Bot kanalda admin bo'lmasa yoki kanal topilmasa ham xatolik bermasin
            not_subscribed.append(ch)
    return not_subscribed


def send_subscription_prompt(chat_id, not_subscribed):
    markup = types.InlineKeyboardMarkup()
    for ch in not_subscribed:
        link = ch["channel_link"] or f"https://t.me/{str(ch['channel_id']).lstrip('@')}"
        markup.add(types.InlineKeyboardButton(text=ch["channel_title"] or ch["channel_id"], url=link))
    markup.add(types.InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_subscription"))
    bot.send_message(
        chat_id,
        "Botdan foydalanish uchun quyidagi kanal(lar)ga a'zo bo'ling, so'ng \"✅ Tekshirish\" tugmasini bosing:",
        reply_markup=markup,
    )


# ==================== /start ====================

@bot.message_handler(commands=["start"])
def handle_start(message):
    db.add_user(message.from_user.id)
    not_subscribed = get_not_subscribed_channels(message.from_user.id)
    if not_subscribed:
        send_subscription_prompt(message.chat.id, not_subscribed)
        return
    bot.send_message(message.chat.id, "Salom! Kino kodini yuboring, men sizga videoni topib beraman 🎬")


@bot.message_handler(commands=["admin"])
def handle_admin(message):
    if not is_admin(message.from_user.id):
        return
    reset_admin_state(message.from_user.id)
    bot.send_message(message.chat.id, "Admin panel:", reply_markup=admin_panel_markup())


@bot.callback_query_handler(func=lambda c: c.data == "check_subscription")
def handle_check_subscription(call):
    not_subscribed = get_not_subscribed_channels(call.from_user.id)
    if not_subscribed:
        bot.answer_callback_query(call.id, "Siz hali barcha kanallarga a'zo bo'lmagansiz.", show_alert=True)
        return
    bot.answer_callback_query(call.id, "Rahmat! Endi botdan foydalanishingiz mumkin.")
    bot.send_message(call.message.chat.id, "Kino kodini yuboring, men sizga videoni topib beraman 🎬")


# ==================== ADMIN PANEL TUGMALARI ====================

@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == BTN_ADD_MOVIE)
def admin_add_movie_start(message):
    admin_state[message.from_user.id] = {"step": "add_code", "data": {}}
    bot.send_message(message.chat.id, "Kino uchun kod kiriting (masalan: 101):")


@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == BTN_DEL_MOVIE)
def admin_delete_movie_start(message):
    admin_state[message.from_user.id] = {"step": "delete_code", "data": {}}
    bot.send_message(message.chat.id, "O'chirmoqchi bo'lgan kino kodini kiriting:")


@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == BTN_STATS)
def admin_stats(message):
    text = (
        f"📊 Statistika\n\n"
        f"🎬 Kinolar soni: {db.movies_count()}\n"
        f"👥 Foydalanuvchilar soni: {db.users_count()}\n"
        f"📢 Majburiy kanallar soni: {len(db.get_channels())}"
    )
    bot.send_message(message.chat.id, text)


@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == BTN_MOVIE_LIST)
def admin_movie_list(message):
    movies = db.get_all_movies()
    if not movies:
        bot.send_message(message.chat.id, "Hozircha kinolar qo'shilmagan.")
        return

    header = f"🎬 Jami: {len(movies)} ta kino\n\n"
    lines = [f"• {m['code']} — {m['title']}" for m in movies]

    chunk = header
    for line in lines:
        if len(chunk) + len(line) + 1 > 3500:
            bot.send_message(message.chat.id, chunk)
            chunk = ""
        chunk += line + "\n"
    if chunk:
        bot.send_message(message.chat.id, chunk)


@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == BTN_ADD_CHANNEL)
def admin_add_channel_start(message):
    admin_state[message.from_user.id] = {"step": "add_channel", "data": {}}
    bot.send_message(
        message.chat.id,
        "Kanal username'ini yuboring (masalan: @mening_kanalim).\n"
        "Diqqat: bot o'sha kanalda admin bo'lishi shart!",
    )


@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == BTN_DEL_CHANNEL)
def admin_delete_channel_start(message):
    channels = db.get_channels()
    if not channels:
        bot.send_message(message.chat.id, "Hozircha majburiy kanallar qo'shilmagan.")
        return
    admin_state[message.from_user.id] = {"step": "delete_channel", "data": {}}
    lines = "\n".join(f"• {c['channel_id']} — {c['channel_title']}" for c in channels)
    bot.send_message(message.chat.id, f"O'chirish uchun kanal username'ini yuboring:\n\n{lines}")


@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == BTN_CHANNEL_LIST)
def admin_channel_list(message):
    channels = db.get_channels()
    if not channels:
        bot.send_message(message.chat.id, "Hozircha majburiy kanallar qo'shilmagan.")
        return
    lines = "\n".join(f"• {c['channel_id']} — {c['channel_title']}" for c in channels)
    bot.send_message(message.chat.id, f"📋 Majburiy kanallar ro'yxati:\n\n{lines}")


@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == BTN_CLOSE_PANEL)
def admin_close_panel(message):
    reset_admin_state(message.from_user.id)
    bot.send_message(message.chat.id, "Admin panel yopildi.", reply_markup=types.ReplyKeyboardRemove())


# ==================== ADMIN HOLAT MASHINASI (matnli qadamlar) ====================

@bot.message_handler(
    func=lambda m: is_admin(m.from_user.id) and m.from_user.id in admin_state and m.content_type == "text"
)
def admin_state_text_handler(message):
    state = admin_state.get(message.from_user.id)
    if not state:
        return
    step = state["step"]
    text = message.text.strip()

    if step == "add_code":
        if db.get_movie(text):
            bot.send_message(message.chat.id, "Bu kod band. Boshqa kod kiriting:")
            return
        state["data"]["code"] = text
        state["step"] = "add_title"
        bot.send_message(message.chat.id, "Kino nomini kiriting:")

    elif step == "add_title":
        state["data"]["title"] = text
        state["step"] = "add_description"
        bot.send_message(message.chat.id, "Kino haqida qisqacha tavsif kiriting:")

    elif step == "add_description":
        state["data"]["description"] = text
        state["step"] = "add_video"
        bot.send_message(message.chat.id, "Endi kino videosini yuboring:")

    elif step == "delete_code":
        deleted = db.delete_movie(text)
        reset_admin_state(message.from_user.id)
        if deleted:
            bot.send_message(message.chat.id, f"✅ {text} kodli kino o'chirildi.", reply_markup=admin_panel_markup())
        else:
            bot.send_message(message.chat.id, f"❌ {text} kodli kino topilmadi.", reply_markup=admin_panel_markup())

    elif step == "add_channel":
        channel_username = text if text.startswith("@") else f"@{text}"
        try:
            chat = bot.get_chat(channel_username)
            link = chat.invite_link or f"https://t.me/{channel_username.lstrip('@')}"
            added = db.add_channel(str(chat.id), chat.title, link)
            reset_admin_state(message.from_user.id)
            if added:
                bot.send_message(message.chat.id, f"✅ Kanal qo'shildi: {chat.title}", reply_markup=admin_panel_markup())
            else:
                bot.send_message(message.chat.id, "Bu kanal allaqachon qo'shilgan.", reply_markup=admin_panel_markup())
        except Exception:
            reset_admin_state(message.from_user.id)
            bot.send_message(
                message.chat.id,
                "❌ Kanal topilmadi yoki bot u yerda admin emas. Qaytadan urinib ko'ring.",
                reply_markup=admin_panel_markup(),
            )

    elif step == "delete_channel":
        channel_username = text if text.startswith("@") else f"@{text}"
        removed = db.remove_channel(channel_username)
        if not removed:
            # foydalanuvchi channel_id (raqamli) yuborgan bo'lishi ham mumkin
            removed = db.remove_channel(text)
        reset_admin_state(message.from_user.id)
        if removed:
            bot.send_message(message.chat.id, "✅ Kanal o'chirildi.", reply_markup=admin_panel_markup())
        else:
            bot.send_message(message.chat.id, "❌ Bunday kanal topilmadi.", reply_markup=admin_panel_markup())


@bot.message_handler(
    func=lambda m: is_admin(m.from_user.id)
    and admin_state.get(m.from_user.id, {}).get("step") == "add_video",
    content_types=["video"],
)
def admin_add_movie_video(message):
    state = admin_state.get(message.from_user.id)
    file_id = message.video.file_id
    data = state["data"]
    ok = db.add_movie(data["code"], data["title"], data["description"], file_id)
    reset_admin_state(message.from_user.id)
    if ok:
        bot.send_message(
            message.chat.id,
            f"✅ Kino qo'shildi!\nKod: {data['code']}\nNomi: {data['title']}",
            reply_markup=admin_panel_markup(),
        )
    else:
        bot.send_message(message.chat.id, "❌ Xatolik: bu kod allaqachon mavjud.", reply_markup=admin_panel_markup())


# ==================== ODDIY FOYDALANUVCHI: KINO QIDIRISH ====================

@bot.message_handler(func=lambda m: m.content_type == "text" and m.text.isdigit())
def handle_movie_code(message):
    db.add_user(message.from_user.id)
    not_subscribed = get_not_subscribed_channels(message.from_user.id)
    if not_subscribed:
        send_subscription_prompt(message.chat.id, not_subscribed)
        return

    movie = db.get_movie(message.text.strip())
    if not movie:
        bot.send_message(message.chat.id, "❌ Bunday kodli kino topilmadi.")
        return

    caption = f"🎬 {movie['title']}\n\n{movie['description']}"
    bot.send_video(message.chat.id, movie["file_id"], caption=caption)


@bot.message_handler(func=lambda m: m.content_type == "text")
def handle_other_text(message):
    if is_admin(message.from_user.id):
        return
    bot.send_message(message.chat.id, "Iltimos, kino kodini raqam ko'rinishida yuboring (masalan: 101)")


# ==================== WEBHOOK ====================

@app.route("/" + BOT_TOKEN, methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        json_string = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "OK", 200
    abort(403)


@app.route("/")
def home():
    return "Bot is running!"


@app.route("/health")
def health():
    return "OK", 200


@app.route("/set_webhook", methods=["GET", "POST"])
def set_webhook():
    webhook_url = f"{BASE_URL}/{BOT_TOKEN}"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    return f"Webhook set to {webhook_url}", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Flask server {port} portda ishga tushmoqda...")
    app.run(host="0.0.0.0", port=port, debug=False)
