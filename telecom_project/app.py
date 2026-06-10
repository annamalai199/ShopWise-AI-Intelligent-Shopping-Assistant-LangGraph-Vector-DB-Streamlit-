import os
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

import streamlit as st
from dotenv import load_dotenv
from rag_chain import build_chain

load_dotenv()

SAMPLE_QUESTIONS = [
    "Why is my mobile internet so slow?",
    "My calls keep dropping — what should I do?",
    "How do I activate international roaming?",
    "Why is my bill higher than usual this month?",
    "My phone shows SIM not detected after a restart",
    "How do I enable Wi-Fi calling?",
    "I was charged for roaming but had a bundle active",
    "How do I unlock my phone for another network?",
]

st.set_page_config(
    page_title="Telecom Support Chat",
    page_icon="📡",
    layout="centered",
)

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
[data-testid="stSidebar"] {
    background: rgba(255, 255, 255, 0.95);
}
[data-testid="stChatMessage"] {
    background: rgba(255, 255, 255, 0.95) !important;
    border-radius: 12px !important;
    padding: 1rem !important;
    margin: 0.5rem 0 !important;
}
[data-testid="stChatMessageContent"] {
    color: #1f2937 !important;
}
[data-testid="stChatMessageContent"] p {
    color: #1f2937 !important;
}
[data-testid="stMarkdownContainer"] p {
    color: #1f2937 !important;
}
.citation-badge {
    display: inline-block;
    background: #4CAF50;
    color: white;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: bold;
    margin: 0 4px;
}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_chain():
    return build_chain()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

with st.sidebar:
    st.title("📡 Telecom Support")
    st.caption("🚀 Enhanced RAG with Citations")
    
    st.markdown("**✨ Features:**")
    st.markdown("- 📌 Source Citations")
    st.markdown("- 🎯 Confidence Scoring")
    st.markdown("- 🔄 Fallback Logic")
    st.markdown("- 📚 Multi-Source Retrieval")
    
    st.divider()
    
    st.markdown("**💬 Sample Questions**")
    st.caption("Click to send instantly")
    for q in SAMPLE_QUESTIONS:
        if st.button(q, use_container_width=True, key=f"btn_{q[:20]}"):
            st.session_state.pending_question = q
    
    st.divider()
    
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    st.caption("Powered by Qwen3-32B on Groq")

st.title("🎯 Customer Care Assistant")
st.caption("Ask anything about mobile service — connectivity, billing, SIM, roaming & more")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

question = st.chat_input("Describe your issue…")
if st.session_state.pending_question:
    question = st.session_state.pending_question
    st.session_state.pending_question = None

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    
    with st.chat_message("assistant"):
        with st.spinner("🔍 Searching knowledge base..."):
            chain = get_chain()
            response = chain({"question": question})
        st.markdown(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
