import streamlit as st
if "messages" not in st.session_state:
    st.session_state.messages=[]
for role, msg in st.session_state.messages:
    with st.chat_message(role):
        st.write(msg)
user=st.chat_input(" ")
if user:
    st.session_state.messages.append(("user", user))
    with st.chat_message("user"):
        st.write(user)
    bot_reply="Hello"+user
    st.session_state.messages.append(("bot_reply", bot_reply))
    with st.chat_message("bot_reply"):
        st.write(bot_reply)