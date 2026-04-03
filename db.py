import sqlite3
from typing import Optional, Dict, Any

DB_NAME = "emails.db"


def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        creds_json TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS embedded_emails (
        message_id TEXT PRIMARY KEY
    )
    """)

    conn.commit()
    conn.close()


def email_exists(message_id: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM emails WHERE message_id = ?", (message_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


def embedding_exists(message_id: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM embedded_emails WHERE message_id = ?", (message_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


def mark_embedded(message_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO embedded_emails (message_id) VALUES (?)", (message_id,))
    conn.commit()
    conn.close()


def save_email(
    message_id: str,
    thread_id: str,
    sender: Optional[str],
    subject: Optional[str],
    summary: Optional[str],
    message_id_header: Optional[str]
):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR IGNORE INTO emails
        (message_id, thread_id, sender, subject, summary, message_id_header)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (message_id, thread_id, sender, subject, summary, message_id_header)
    )
    conn.commit()
    conn.close()


def get_email_for_reply(message_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT thread_id, sender, subject, message_id_header
    FROM emails WHERE message_id = ?
    """, (message_id,))
    result = cursor.fetchone()
    conn.close()
    if not result:
        return None
    return {
        "thread_id": result[0],
        "sender": result[1],
        "subject": result[2],
        "message_id_header": result[3],
    }


def save_creds(user_id: str, creds_json: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO users (user_id, creds_json)
    VALUES (?, ?)
    """, (user_id, creds_json))
    conn.commit()
    conn.close()


def get_creds(user_id: str) -> Optional[str]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT creds_json FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None