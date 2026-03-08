from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import base64

app = FastAPI()

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CLIENT_FILE = "credentials.json"
REDIRECT_URI = "http://localhost:8000/callback"

flow = None

@app.get("/")
def login():
    global flow
    flow = Flow.from_client_secrets_file(
        CLIENT_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI
    )
    auth_url, _ = flow.authorization_url()
    return RedirectResponse(auth_url)


@app.get("/callback")
def callback(code: str):
    global flow
    flow.fetch_token(code=code)
    creds = flow.credentials
    service = build("gmail", "v1", credentials=creds)

    all_results = []
    next_page_token = None

    while True:
        msgs = service.users().messages().list(
            userId="me", maxResults=100, pageToken=next_page_token
        ).execute()

        for m in msgs.get("messages", []):
            msg_id = m["id"]
            message = service.users().messages().get(userId="me", id=msg_id).execute()

            payload = message["payload"]
            headers = payload.get("headers", [])
            
            sender = None
            date = None
            for h in headers:
                if h["name"] == "From":
                    sender = h["value"]
                if h["name"] == "Date":
                    date = h["value"]

            body = ""
            if "parts" in payload:
                for part in payload["parts"]:
                    if part["mimeType"] == "text/plain":
                        data = part["body"]["data"]
                        body = base64.urlsafe_b64decode(data).decode()
            else:
                data = payload["body"].get("data")
                if data:
                    body = base64.urlsafe_b64decode(data).decode()

            all_results.append({
                "threadId": message["threadId"],
                "sender": sender,
                "time": date,
                "snippet": message["snippet"],
                "body": body
            })

        next_page_token = msgs.get("nextPageToken")
        if not next_page_token:
            break

    return {"emails": all_results}
