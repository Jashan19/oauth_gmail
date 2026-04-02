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
        thread_id TEXT,
        sender TEXT,
        subject TEXT,
        summary TEXT,
        message_id_header TEXT
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


def save_email(message_id, thread_id, sender, subject, summary, message_id_header):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """INSERT OR IGNORE INTO emails 
        (message_id, thread_id, sender, subject, summary, message_id_header) 
        VALUES (?, ?, ?, ?, ?, ?)""",
        (message_id, thread_id, sender, subject, summary, message_id_header)
    )

    conn.commit()
    conn.close()
def get_email_for_reply(message_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT thread_id, sender, subject, message_id_header
    FROM emails
    WHERE message_id = ?
    """, (message_id,))

    result = cursor.fetchone()
    conn.close()

    return result
def save_creds(user_id, creds_json):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR REPLACE INTO users (user_id, creds_json)
    VALUES (?, ?)
    """, (user_id, creds_json))

    conn.commit()
    conn.close()


def get_creds(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT creds_json FROM users WHERE user_id = ?
    """, (user_id,))

    result = cursor.fetchone()
    conn.close()

    return result[0] if result else None