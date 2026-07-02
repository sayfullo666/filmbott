# database.py
# SQLite ma'lumotlar bazasi bilan ishlash uchun barcha funksiyalar

import sqlite3
from config import DB_NAME


def get_conn():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            joined_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            code TEXT PRIMARY KEY,
            channel_id INTEGER NOT NULL,
            message_id INTEGER NOT NULL,
            title TEXT,
            description TEXT,
            views INTEGER DEFAULT 0,
            added_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Eski bazalarda "description" ustuni bo'lmasligi mumkin - shuni qo'shib qo'yamiz
    try:
        cur.execute("ALTER TABLE movies ADD COLUMN description TEXT")
    except sqlite3.OperationalError:
        pass  # ustun allaqachon mavjud

    cur.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            channel_id INTEGER PRIMARY KEY,
            username TEXT,
            title TEXT
        )
    """)

    conn.commit()
    conn.close()


# ---------------- USERS ----------------

def add_user(user_id: int, username: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
        (user_id, username),
    )
    conn.commit()
    conn.close()


def users_count() -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as cnt FROM users")
    row = cur.fetchone()
    conn.close()
    return row["cnt"]


# ---------------- MOVIES ----------------

def add_movie(code: str, channel_id: int, message_id: int, title: str, description: str = ""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO movies (code, channel_id, message_id, title, description, views) "
        "VALUES (?, ?, ?, ?, ?, COALESCE((SELECT views FROM movies WHERE code=?), 0))",
        (code, channel_id, message_id, title, description, code),
    )
    conn.commit()
    conn.close()


def get_movie(code: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM movies WHERE code = ?", (code,))
    row = cur.fetchone()
    conn.close()
    return row


def delete_movie(code: str) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM movies WHERE code = ?", (code,))
    changed = cur.rowcount > 0
    conn.commit()
    conn.close()
    return changed


def increment_views(code: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE movies SET views = views + 1 WHERE code = ?", (code,))
    conn.commit()
    conn.close()


def movies_count() -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as cnt FROM movies")
    row = cur.fetchone()
    conn.close()
    return row["cnt"]


def top_movies(limit: int = 10):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT code, title, views FROM movies ORDER BY views DESC LIMIT ?",
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


# ---------------- CHANNELS (majburiy obuna) ----------------

def add_channel(channel_id: int, username: str, title: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO channels (channel_id, username, title) VALUES (?, ?, ?)",
        (channel_id, username, title),
    )
    conn.commit()
    conn.close()


def remove_channel(channel_id: int) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))
    changed = cur.rowcount > 0
    conn.commit()
    conn.close()
    return changed


def get_channels():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM channels")
    rows = cur.fetchall()
    conn.close()
    return rows