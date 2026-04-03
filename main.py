from fastapi import FastAPI
from fastapi.responses import RedirectResponse, JSONResponse
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import base64
from db import create_table, email_exists, save_email, save_creds
from embedding import embed_new_emails

app = FastAPI()

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]

CLIENT_FILE = "credentials.json"
REDIRECT_URI = "http://localhost:8000/callback"


@app.on_event("startup")
def startup():
    create_table()

flow=None
@app.get("/")
def login():
    global flow
    flow = Flow.from_client_secrets_file(
        CLIENT_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    auth_url, _ = flow.authorization_url(prompt="consent")
    return RedirectResponse(auth_url)


def extract_plain_text(payload):
    """Recursively extracts text/plain content from a Gmail message payload."""
    if not payload:
        return ""

    mime_type = payload.get("mimeType", "")

    if mime_type == "text/plain":
        data = payload.get("body", {}).get("data")
        if data:
            try:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
            except Exception:
                return ""

    for part in payload.get("parts", []):
        text = extract_plain_text(part)
        if text:
            return text

    # Fallback: body directly in payload
    data = payload.get("body", {}).get("data")
    if data:
        try:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
        except Exception:
            return ""

    return ""


@app.get("/callback")
def callback(code: str):
    global flow
    # flow = Flow.from_client_secrets_file(
    #     CLIENT_FILE,
    #     scopes=SCOPES,
    #     redirect_uri=REDIRECT_URI
    # )
    flow.fetch_token(code=code)
    creds = flow.credentials

    # Save creds to DB — gmail_connect.py will read from here
    save_creds("me", creds.to_json())

    service = build("gmail", "v1", credentials=creds)

    all_results = []
    next_page_token = None

    while True:
        msgs = service.users().messages().list(
            userId="me",
            maxResults=100,
            pageToken=next_page_token
        ).execute()

        for m in msgs.get("messages", []):
            msg_id = m["id"]

            if email_exists(msg_id):
                continue

            message = service.users().messages().get(
                userId="me",
                id=msg_id,
                format="full"
            ).execute()

            payload = message.get("payload", {})
            headers = payload.get("headers", [])

            sender = subject = message_id_header = None

            for h in headers:
                name = h.get("name")
                value = h.get("value")
                if name == "From":
                    sender = value
                elif name == "Subject":
                    subject = value
                elif name == "Message-ID":
                    message_id_header = value

            body = extract_plain_text(payload)
            summary = body[:200] if body else ""
            thread_id = message.get("threadId", "")

            save_email(
                message_id=msg_id,
                thread_id=thread_id,
                sender=sender,
                subject=subject,
                summary=summary,
                message_id_header=message_id_header
            )

            all_results.append({
                "id": msg_id,
                "thread_id": thread_id,
                "sender": sender,
                "subject": subject,
                "summary": summary,
                "message_id": message_id_header
            })

        next_page_token = msgs.get("nextPageToken")
        if not next_page_token:
            break

    # Auto-embed new emails after sync
    embed_new_emails()

    return JSONResponse({"emails_synced": len(all_results), "status": "done"})