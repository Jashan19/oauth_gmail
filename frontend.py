import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
load_dotenv()
client = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash"
)
if "messages" not in st.session_state:
    st.session_state.messages = []
for role, msg in st.session_state.messages:
    with st.chat_message(role):
        st.write(msg)
user = st.chat_input("Ask something")
if user:
    st.session_state.messages.append(("user", user))
    with st.chat_message("user"):
        st.write(user)
    response = client.invoke(user)
    bot_reply = response.content
    st.session_state.messages.append(("assistant", bot_reply))
    with st.chat_message("assistant"):
        st.write(bot_reply)