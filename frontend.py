# import streamlit as st
# if "messages" not in st.session_state:
#     st.session_state.messages=[]
# for role, msg in st.session_state.messages:
#     with st.chat_message(role):
#         st.write(msg)
# user=st.chat_input(" ")
# if user:
#     st.session_state.messages.append(("user", user))
#     with st.chat_message("user"):
#         st.write(user)
#     bot_reply="Hello"+user
#     st.session_state.messages.append(("bot_reply", bot_reply))
#     with st.chat_message("bot_reply"):
#         st.write(bot_reply)
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from sentence_transformers import SentenceTransformer
import chromadb
from dotenv import load_dotenv

load_dotenv()

# LLM
client = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash"
)

# Embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Persistent ChromaDB
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="emails")

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display old messages
for role, msg in st.session_state.messages:
    with st.chat_message(role):
        st.write(msg)

# User input
user = st.chat_input("Ask about your emails")

if user:

    st.session_state.messages.append(("user", user))

    with st.chat_message("user"):
        st.write(user)

    # Convert query to embedding
    query_embedding = model.encode(user).tolist()

    # Semantic search
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3
    )

    docs = results.get("documents", [[]])[0]

    if len(docs) == 0:
        context = "No relevant emails found."
    else:
        context = "\n".join(docs)

    # Prompt
    prompt = f"""
You are an assistant that answers questions using the user's emails.

Emails:
{context}

Question:
{user}
"""

    # LLM response
    response = client.invoke(prompt)
    bot_reply = response.content

    st.session_state.messages.append(("assistant", bot_reply))

    with st.chat_message("assistant"):
        st.write(bot_reply)