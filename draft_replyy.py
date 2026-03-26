from googleapiclient.discovery import build
import base64
from langchain_google_genai import ChatGoogleGenerativeAI
llm=ChatGoogleGenerativeAI(model="gemini-2.5-flash")
def get_email_content(service, message_id):
    msg=services.users().messages().get(userId="me", id=message_id).execute()
    payload=msg["payload"]
    parts=payload.get("parts", [])
    for part in parts:
        if part["mimeType"]=="text/plain":
            data=part["body"]["data"],
            decoded=base64.urlsafe_b64decode(data).decode("utf-8")
            return decoded
        return "no text content found"
def generate_reply(email_text):
    prompt = f"""
You are an AI email assistant.
Write a professional reply to the following email:

Email:
{email_text}

Reply:
"""

    response = llm.invoke(prompt)
    return response.content
def create_draft(service, reply_text):
    message=f"Subject: Re: \n\n{reply_text}"
    encoded_message=base64.urlsafe_base64encode(message.encode("utf-8")).decode("utf-8")
    draft={
        "messages":{
            "raw":encoded_message
        }
    }
    draft=service.users().draft().create(userId="me", body=draft).execute()
    return draft
def main(service, message_id):
    email_text=get_email_content(service, message_id)
    reply=generate_reply(email_text)
    draft=create_draft(service, reply)
    print("Draft created: ", draft["id"])