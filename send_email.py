# gmail_send.py
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from email.mime.text import MIMEText
from base64 import urlsafe_b64encode

# 🔐 Load your saved OAuth credentials
creds = Credentials.from_authorized_user_file("credentials.json")

# Gmail service
service = build("gmail", "v1", credentials=creds)


def send_reply(service, to, subject, reply_text, thread_id, message_id_header):
    message = MIMEText(reply_text)

    message['to'] = to
    message['subject'] = "Re: " + subject
    message['In-Reply-To'] = message_id_header
    message['References'] = message_id_header

    raw = urlsafe_b64encode(message.as_bytes()).decode()

    return service.users().messages().send(
        userId="me",
        body={
            "raw": raw,
            "threadId": thread_id
        }
    ).execute()