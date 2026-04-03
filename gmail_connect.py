import json
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from db import get_creds

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]


def get_gmail_service():
    """
    Loads Gmail credentials from the DB (saved during OAuth in main.py).
    Falls back to token.json if DB has no creds yet.
    """
    creds_json = get_creds("me")

    if creds_json:
        creds_data = json.loads(creds_json)
        creds = Credentials(
            token=creds_data.get("token"),
            refresh_token=creds_data.get("refresh_token"),
            token_uri=creds_data.get("token_uri"),
            client_id=creds_data.get("client_id"),
            client_secret=creds_data.get("client_secret"),
            scopes=creds_data.get("scopes", SCOPES),
        )
    else:
        # Fallback: token.json (for local dev before first OAuth)
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    service = build("gmail", "v1", credentials=creds)
    return service