import sqlite3

DB_NAME = "emails.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def create_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS emails (
        message_id TEXT PRIMARY KEY,
        subject TEXT,
        summary TEXT
    )
    """)

    conn.commit()
    conn.close()


def email_exists(message_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT 1 FROM emails WHERE message_id = ?",
        (message_id,)
    )

    result = cursor.fetchone()
    conn.close()

    return result is not None


def save_email(message_id, subject, summary):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT OR IGNORE INTO emails (message_id, subject, summary) VALUES (?, ?, ?)",
        (message_id, subject, summary)
    )

    conn.commit()
    conn.close()