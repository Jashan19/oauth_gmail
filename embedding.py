from sentence_transformers import SentenceTransformer
import sqlite3
import chromadb

# Embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Persistent ChromaDB
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="emails")

# Connect SQLite
conn = sqlite3.connect("emails.db")
cursor = conn.cursor()

cursor.execute("SELECT message_id, subject, summary FROM emails")
rows = cursor.fetchall()

for message_id, subject, summary in rows:

    text = f"Subject: {subject}\nSummary: {summary}"

    embedding = model.encode(text).tolist()

    collection.add(
        ids=[str(message_id)],
        embeddings=[embedding],
        documents=[text]
    )

conn.close()

print("Embeddings stored successfully!")
print("Total stored:", collection.count())