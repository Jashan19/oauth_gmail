import base64
from langchain_google_genai import ChatGoogleGenerativeAI
from llm import llm
llm = llm
def extract_plain_text(payload):
    """Recursively extracts text/plain from Gmail payload (handles multipart)."""
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
    data = payload.get("body", {}).get("data")
    if data:
        try:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
        except Exception:
            return ""

    return ""


def get_email_content(service, message_id: str):
    """Fetches a Gmail message and returns (body_text, sender, subject)."""
    msg = service.users().messages().get(
        userId="me",
        id=message_id,
        format="full"
    ).execute()

    payload = msg.get("payload", {})
    headers = payload.get("headers", [])

    sender = ""
    subject = ""

    for header in headers:
        if header["name"] == "From":
            sender = header["value"]
        elif header["name"] == "Subject":
            subject = header["value"]

    body = extract_plain_text(payload)
    return body or "No content found.", sender, subject


def generate_reply(email_text: str) -> str:
    """Uses Gemini to generate a professional reply to the given email text."""
    prompt = f"""
You are a professional AI email assistant.
Write a clear, concise, and professional reply to the following email.
Do not add placeholder text like [Your Name] — just write the reply body.

Email:
{email_text}

Reply:
"""
    response = llm.invoke(prompt)
    return response.content


def create_draft(service, reply_text: str, to_email: str, subject: str):
    """Creates a Gmail draft for the given reply."""
    message = f"To: {to_email}\nSubject: Re: {subject}\n\n{reply_text}"
    encoded_message = base64.urlsafe_b64encode(
        message.encode("utf-8")
    ).decode("utf-8")

    draft = service.users().drafts().create(
        userId="me",
        body={"message": {"raw": encoded_message}}
    ).execute()

    return draft