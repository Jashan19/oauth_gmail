import base64
import re
def extract_email(sender: str) -> str:
    """Extracts clean email address from 'Name <email>' format."""
    match = re.search(r"<(.+?)>", sender)
    return match.group(1) if match else sender.strip()
def send_email(service, reply_text: str, sender: str, subject: str) -> dict:
    """Sends an email reply via Gmail API."""
    to_email = extract_email(sender)

    message = f"To: {to_email}\nSubject: Re: {subject}\n\n{reply_text}"

    encoded_message = base64.urlsafe_b64encode(
        message.encode("utf-8")
    ).decode("utf-8")

    sent = service.users().messages().send(
        userId="me",
        body={"raw": encoded_message}
    ).execute()

    return sent