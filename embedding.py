# from sentence_transformers import SentenceTransformer
# import chromadb
# import sqlite3

# model = SentenceTransformer("all-MiniLM-L6-v2")

# chroma_client = chromadb.PersistentClient(path="./chroma_db")
# collection = chroma_client.get_or_create_collection("emails")

# conn = sqlite3.connect("emails.db")
# cursor = conn.cursor()

# cursor.execute("""
# SELECT message_id, sender, subject, summary 
# FROM emails
# """)

# rows = cursor.fetchall()

# texts, ids, metadatas = [], [], []

# for message_id, sender, subject, summary in rows:
#     text = f"""
#     From: {sender}
#     Subject: {subject}
#     Summary: {summary}
#     """
#     texts.append(text)
#     ids.append(str(message_id))
#     metadatas.append({
#         "sender": sender,
#         "subject": subject
#     })

# embeddings = model.encode(texts).tolist()

# collection.add(
#     ids=ids,
#     embeddings=embeddings,
#     documents=texts,
#     metadatas=metadatas
# )

# conn.close()
from sentence_transformers import SentenceTransformer
import chromadb
import sqlite3
from db import embedding_exists, mark_embedded

model = SentenceTransformer("all-MiniLM-L6-v2")

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection("emails")


def embed_new_emails():
    """
    Reads emails from SQLite and embeds only the ones not yet in ChromaDB.
    Safe to call multiple times — skips already-embedded emails.
    """
    conn = sqlite3.connect("emails.db")
    cursor = conn.cursor()

    cursor.execute("SELECT message_id, sender, subject, summary FROM emails")
    rows = cursor.fetchall()
    conn.close()

    texts, ids, metadatas = [], [], []

    for message_id, sender, subject, summary in rows:
        if embedding_exists(message_id):
            continue  # Skip already embedded

        text = f"From: {sender}\nSubject: {subject}\nSummary: {summary}"
        texts.append(text)
        ids.append(str(message_id))
        metadatas.append({
            "sender": sender or "",
            "subject": subject or ""
        })

    if not texts:
        print("No new emails to embed.")
        return

    print(f"Embedding {len(texts)} new emails...")
    embeddings = model.encode(texts).tolist()

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas
    )

    for msg_id in ids:
        mark_embedded(msg_id)

    print(f"Done. {len(ids)} emails embedded.")


if __name__ == "__main__":
    embed_new_emails()