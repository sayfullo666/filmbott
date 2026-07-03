import sqlite3

DB_NAME = "bot_database.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            code TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            file_id TEXT NOT NULL,
            added_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id TEXT UNIQUE NOT NULL,
            channel_title TEXT,
            channel_link TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            joined_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# ---------------- MOVIES ----------------

def add_movie(code: str, title: str, description: str, file_id: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO movies (code, title, description, file_id) VALUES (?, ?, ?, ?)",
            (code, title, description, file_id),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_movie(code: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM movies WHERE code = ?", (code,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def delete_movie(code: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM movies WHERE code = ?", (code,))
    exists = cur.fetchone() is not None
    if exists:
        cur.execute("DELETE FROM movies WHERE code = ?", (code,))
        conn.commit()
    conn.close()
    return exists


def movies_count() -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM movies")
    count = cur.fetchone()["c"]
    conn.close()
    return count


# ---------------- CHANNELS ----------------

def add_channel(channel_id: str, channel_title: str, channel_link: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO channels (channel_id, channel_title, channel_link) VALUES (?, ?, ?)",
            (channel_id, channel_title, channel_link),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def remove_channel(channel_id: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM channels WHERE channel_id = ?", (channel_id,))
    exists = cur.fetchone() is not None
    if exists:
        cur.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))
        conn.commit()
    conn.close()
    return exists


def get_channels():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM channels")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------- USERS ----------------

def add_user(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()


def users_count() -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM users")
    count = cur.fetchone()["c"]
    conn.close()
    return count
