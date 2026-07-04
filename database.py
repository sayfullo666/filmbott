import os
import psycopg2
import psycopg2.extras

DATABASE_URL = os.environ.get("DATABASE_URL")


def get_connection():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
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
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            id SERIAL PRIMARY KEY,
            channel_id TEXT UNIQUE NOT NULL,
            channel_title TEXT,
            channel_link TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    cur.close()
    conn.close()


# ---------------- MOVIES ----------------

def add_movie(code: str, title: str, description: str, file_id: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO movies (code, title, description, file_id) VALUES (%s, %s, %s, %s)",
            (code, title, description, file_id),
        )
        conn.commit()
        return True
    except psycopg2.IntegrityError:
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()


def get_movie(code: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM movies WHERE code = %s", (code,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return dict(row) if row else None


def delete_movie(code: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM movies WHERE code = %s", (code,))
    exists = cur.fetchone() is not None
    if exists:
        cur.execute("DELETE FROM movies WHERE code = %s", (code,))
        conn.commit()
    cur.close()
    conn.close()
    return exists


def movies_count() -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM movies")
    count = cur.fetchone()["c"]
    cur.close()
    conn.close()
    return count


def get_all_movies():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM movies ORDER BY added_at DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]


# ---------------- CHANNELS ----------------

def add_channel(channel_id: str, channel_title: str, channel_link: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO channels (channel_id, channel_title, channel_link) VALUES (%s, %s, %s)",
            (channel_id, channel_title, channel_link),
        )
        conn.commit()
        return True
    except psycopg2.IntegrityError:
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()


def remove_channel(channel_id: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM channels WHERE channel_id = %s", (channel_id,))
    exists = cur.fetchone() is not None
    if exists:
        cur.execute("DELETE FROM channels WHERE channel_id = %s", (channel_id,))
        conn.commit()
    cur.close()
    conn.close()
    return exists


def get_channels():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM channels")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]


# ---------------- USERS ----------------

def add_user(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (user_id) VALUES (%s) ON CONFLICT (user_id) DO NOTHING",
        (user_id,),
    )
    conn.commit()
    cur.close()
    conn.close()


def users_count() -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM users")
    count = cur.fetchone()["c"]
    cur.close()
    conn.close()
    return count
