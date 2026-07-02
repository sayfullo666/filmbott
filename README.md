# Kino Bot (Telegram)

Foydalanuvchi kod yuboradi → bot shaxsiy kanaldan kinoni topib beradi.
Majburiy obuna, statistika va to'liq admin panel bilan.

## 1. O'rnatish

```bash
pip install -r requirements.txt
```

## 2. Sozlash (`config.py`)

1. [@BotFather](https://t.me/BotFather) orqali yangi bot yarating va tokenni oling.
2. `config.py` faylida:
   ```python
   BOT_TOKEN = "SIZNING_TOKENINGIZ"
   ADMIN_IDS = [123456789]  # o'z ID raqamingiz
   ```
   O'z ID raqamingizni [@userinfobot](https://t.me/userinfobot) orqali bilib olishingiz mumkin.

## 3. Kanallarni tayyorlash

- **Kinolar saqlanadigan shaxsiy kanal**: botni shu kanalga **admin** qilib qo'shing (kino kanalini nashr qilish shart emas — bot faqat kinoni o'sha yerdan foydalanuvchiga forward/copy qiladi).
- **Majburiy obuna kanal(lar)i**: bot admin panel orqali qo'shiladi, lekin bot bu kanallarda ham **admin** bo'lishi shart (aks holda obunani tekshira olmaydi).

## 4. Ishga tushirish

```bash
python bot.py
```

## 5. Qanday ishlaydi

### Admin uchun
- `/admin` — admin panelni ochadi
- **➕ Kino qo'shish** → keyin kinoni shaxsiy kanalingizdan botga forward qiling → bot so'ragan kodni kiriting (masalan `001`)
- **🗑 Kino o'chirish** → kodni kiriting
- **📊 Statistika** → foydalanuvchilar soni, kinolar soni, eng ko'p ko'rilgan kinolar reytingi
- **➕ Majburiy kanal qo'shish** → kanaldan istalgan postni forward qiling (yopiq kanal bo'lsa, invite havolani so'raydi)
- **➖ Majburiy kanal o'chirish** → ro'yxatdan tanlab o'chirasiz
- **📃 Kanallar ro'yxati** — joriy majburiy kanallarni ko'rsatadi

### Oddiy foydalanuvchi uchun
1. Botga `/start` bosadi
2. Kino kodini yuboradi (masalan `001`)
3. Agar majburiy kanal(lar)ga obuna bo'lmagan bo'lsa — obuna bo'lish tugmalari va "✅ Obunani tekshirish" tugmasi chiqadi
4. Obuna tasdiqlangach, kino avtomatik yuboriladi va ko'rishlar soni +1 bo'ladi
5. Foydalanuvchi keyinchalik kanaldan chiqib ketsa, keyingi safar kod yuborganda bot yana obuna bo'lishni so'raydi (har safar tekshiriladi)

## Fayllar tuzilishi

```
kinobot/
├── bot.py           # asosiy bot logikasi
├── database.py      # SQLite bilan ishlash funksiyalari
├── config.py        # token va admin sozlamalari
├── requirements.txt
└── movies.db         # bot birinchi marta ishga tushganda avtomatik yaratiladi
```

## Eslatmalar

- Bot **polling** rejimida ishlaydi (`infinity_polling`) — serverda doimiy ishlab turishi uchun VPS yoki tunnel kerak bo'ladi (masalan `screen`/`systemd` orqali fon rejimida ishga tushiring).
- Ma'lumotlar bazasi oddiy SQLite fayl (`movies.db`) — katta hajmda foydalanuvchi bo'lsa PostgreSQL ga o'tish tavsiya etiladi.
- Kino fayllarining o'zi bot serverida saqlanmaydi — faqat `channel_id` va `message_id` saqlanadi, kino haqiqiy fayli doim sizning shaxsiy kanalingizda qoladi.
