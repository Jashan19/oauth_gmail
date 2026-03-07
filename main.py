from fastapi import FastAPI, Response
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
app=FastAPI()
SCOPES=["https://www.googleapis.com/auth/gmail.readonly"]
CLIENT_FILE="credentials.json"
REDIRECT_URI="http://localhost:8000/callback"
@app.get("/")
def home():
    flow=Flow.from_client_secrets_file(
        "credentials.json",
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    auth_url, state=flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true"
    )
    return RedirectResponse(auth_url)
# @app.get("/login")
# def login():
#     flow=Flow.from_client_secrets_file(
#         CLIENT_FILE,
#         scopes=SCOPES,
#         redirect_uri=REDIRECT_URI
#     )
#     auth_url, state=flow.authorization_url(
#         access_type="offline",
#         include_granted_scopes="true"
#     )
#     return RedirectResponse(auth_url)
@app.get("/callback")
def callback(code: str):
    flow=Flow.from_client_secrets_file(
        CLIENT_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    flow.fetch_token(code=code)
    creds=flow.credentials
    service=build("gmail","v1",credentials=creds)
    messages=service.users().messages().list(
        userId="me",
        maxResults=5
    ).execute()
    return messages
