import re
import streamlit as st
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from sentence_transformers import SentenceTransformer
import chromadb
from draft_reply import get_email_content, generate_reply
from send_email import send_email
from gmail_connect import get_gmail_service
from llm import llm
load_dotenv()
st.set_page_config(page_title="AI Email Assistant", page_icon="📧", layout="wide")
llm = llm
embed_model = SentenceTransformer("all-MiniLM-L6-v2")
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="emails")
@st.cache_resource(show_spinner=False)
def load_service():
    return get_gmail_service()
service = load_service()
def extract_email(sender: str) -> str:
    match = re.search(r"<(.+?)>", sender)
    return match.group(1) if match else sender.strip()
def build_context_from_rag(query: str, top_k: int = 3) -> str:
    try:
        query_embedding = embed_model.encode(query).tolist()
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        docs = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        if not docs:
            return "No relevant emails found."
        parts = []
        for doc, meta in zip(docs, metadatas):
            parts.append(
                f"From: {meta.get('sender', 'Unknown')}\n"
                f"Subject: {meta.get('subject', 'No Subject')}\n\n{doc}"
            )
        return "\n\n---\n\n".join(parts)

    except Exception as e:
        return f"RAG error: {str(e)}"


def answer_question_about_emails(user_question: str) -> str:
    context = build_context_from_rag(user_question, top_k=3)
    prompt = f"""
You are a strict AI email assistant.

Rules:
- Use ONLY the provided emails.
- If the answer is not clearly in the emails, say: "Not found in emails."
- Do NOT guess or make up information.

Emails:
{context}

Question:
{user_question}

Answer:
"""
    response = llm.invoke(prompt)
    return response.content


@st.cache_data(show_spinner=False, ttl=60)
def list_recent_emails(max_results: int = 10):
    try:
        results = service.users().messages().list(
            userId="me",
            labelIds=["INBOX"],
            maxResults=max_results
        ).execute()

        messages = results.get("messages", [])
        options = []

        for msg in messages:
            meta = service.users().messages().get(
                userId="me",
                id=msg["id"],
                format="metadata",
                metadataHeaders=["From", "Subject"]
            ).execute()

            headers = meta.get("payload", {}).get("headers", [])
            sender = subject = ""

            for header in headers:
                if header["name"] == "From":
                    sender = header["value"]
                elif header["name"] == "Subject":
                    subject = header["value"]

            options.append({
                "id": msg["id"],
                "sender": sender,
                "subject": subject,
                "snippet": meta.get("snippet", "")
            })

        return options

    except Exception as e:
        st.error(f"Failed to load inbox: {str(e)}")
        return []
for key, default in {
    "messages": [],
    "selected_email": None,
    "generated_reply": "",
    "reply_target_email": "",
    "reply_subject": "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


st.title("📧 AI Email Assistant")
tab1, tab2 = st.tabs(["💬 Ask About Emails", "✉️ Reply to an Email"])

with tab1:
    st.subheader("Search your emails with natural language")

    for role, msg in st.session_state.messages:
        with st.chat_message(role):
            st.write(msg)

    user_input = st.chat_input("Ask about your emails...")

    if user_input:
        st.session_state.messages.append(("user", user_input))
        with st.chat_message("user"):
            st.write(user_input)

        with st.spinner("Thinking..."):
            try:
                bot_reply = answer_question_about_emails(user_input)
            except Exception as e:
                bot_reply = f"Error: {str(e)}"

        st.session_state.messages.append(("assistant", bot_reply))
        with st.chat_message("assistant"):
            st.write(bot_reply)
with tab2:
    st.subheader("Generate and send a reply")

    col1, col2 = st.columns([2, 1])

    with col1:
        recent_emails = list_recent_emails(max_results=10)

        if not recent_emails:
            st.info("No recent emails found.")
        else:
            email_options = {
                f'{item["subject"] or "No Subject"}  |  {extract_email(item["sender"]) or "Unknown"}': item["id"]
                for item in recent_emails
            }

            selected_label = st.selectbox("Choose an email", list(email_options.keys()))
            selected_message_id = email_options[selected_label]

            if st.button(" Load Email"):
                try:
                    email_text, sender, subject = get_email_content(service, selected_message_id)
                    st.session_state.selected_email = {
                        "message_id": selected_message_id,
                        "email_text": email_text,
                        "sender": extract_email(sender),
                        "subject": subject
                    }
                    st.session_state.reply_target_email = extract_email(sender)
                    st.session_state.reply_subject = subject
                    st.session_state.generated_reply = ""
                    st.success("Email loaded.")
                except Exception as e:
                    st.error(f"Could not load email: {str(e)}")

    with col2:
        st.caption("Replies are generated as drafts. Review before sending.")

    if st.session_state.selected_email:
        email_data = st.session_state.selected_email

        st.markdown("---")
        st.markdown("###  Selected Email")
        st.write(f"**From:** {email_data['sender']}")
        st.write(f"**Subject:** {email_data['subject']}")
        st.text_area("Email preview", email_data["email_text"], height=200, disabled=True)

        if st.button(" Generate Reply"):
            with st.spinner("Generating reply..."):
                try:
                    reply = generate_reply(email_data["email_text"])
                    st.session_state.generated_reply = reply
                except Exception as e:
                    st.error(f"Reply generation failed: {str(e)}")

        if st.session_state.generated_reply:
            st.markdown("###  Edit Reply")
            edited_reply = st.text_area(
                "Edit before sending",
                value=st.session_state.generated_reply,
                height=200,
                key="editable_reply"
            )

            confirm_send = st.checkbox("✅ I reviewed this reply and want to send it")

            if st.button("📤 Send Email"):
                if not confirm_send:
                    st.warning("Please check the confirmation box before sending.")
                else:
                    try:
                        sent = send_email(
                            service,
                            st.session_state.get("editable_reply", st.session_state.generated_reply),
                            st.session_state.reply_target_email,
                            st.session_state.reply_subject
                        )
                        st.success(f"Email sent! Message ID: {sent['id']}")
                        st.session_state.generated_reply = ""
                        st.session_state.selected_email = None
                    except Exception as e:
                        st.error(f"Send failed: {str(e)}")