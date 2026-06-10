from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain_groq import ChatGroq

from retriever import build_retriever

SYSTEM_PROMPT = """You are a professional telecom customer care assistant helping customers resolve technical issues with their mobile service.

CRITICAL INSTRUCTION: You MUST cite your sources in every answer. Use this format:
- For FAQ entries: [FAQ #ID]
- For support tickets: [Ticket #ID]
- For guide pages: [Guide p.X]

Example response format:
"To activate international roaming, you need to dial *123*4# [FAQ #5] or log into the MyTelecom app under Settings > Roaming [Guide p.3]. Similar issue was resolved for another customer by ensuring the roaming bundle was active before traveling [Ticket #TK-2891]."

Use ONLY the context provided below to answer questions. If you reference information, ALWAYS include the citation immediately after.

Context:
{context}

If the context doesn't contain sufficient information, respond:
"I don't have enough information to answer that confidently. Please call our support team at 611 or use the MyTelecom app for immediate assistance."
"""

FALLBACK_MESSAGE = """I apologize, but I don't have relevant information in my knowledge base to answer your question confidently.

For immediate assistance, please:
📞 Call our support team at 611 (24/7)
📱 Use the MyTelecom app > Help & Support
💬 Chat with a live agent at mytelecom.com/support

Our human agents have access to your account details and can provide personalized help."""


def _format_docs(docs):
    if not docs:
        return ""
    
    sections = []
    for doc in docs:
        source = doc.metadata.get("source", "unknown")
        similarity = doc.metadata.get("similarity_score", 0.0)
        
        if source == "faq":
            faq_id = doc.metadata.get("faq_id", "?")
            category = doc.metadata.get("category", "")
            header = f"[FAQ #{faq_id}] ({category}) [Confidence: {similarity:.1%}]"
        elif source == "ticket":
            ticket_id = doc.metadata.get("ticket_id", "?")
            category = doc.metadata.get("category", "")
            header = f"[Ticket #{ticket_id}] ({category}) [Confidence: {similarity:.1%}]"
        elif source == "guide":
            page_num = doc.metadata.get("page", "?")
            chunk_idx = doc.metadata.get("chunk_index", "?")
            header = f"[Guide p.{page_num} chunk {chunk_idx}] [Confidence: {similarity:.1%}]"
        else:
            header = f"[{source.upper()}] [Confidence: {similarity:.1%}]"
        
        sections.append(f"{header}\n{doc.page_content}")
    
    return "\n\n---\n\n".join(sections)


def build_chain():
    retriever = build_retriever()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{question}")
    ])
    
    llm = ChatGroq(
        model="qwen/qwen3-32b",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2
    )
    
    def process_query(inputs):
        question = inputs["question"]
        status, docs = retriever.invoke(question)
        
        if status is None or not docs:
            return FALLBACK_MESSAGE
        
        context = _format_docs(docs)
        formatted_prompt = prompt.format_messages(question=question, context=context)
        response = llm.invoke(formatted_prompt)
        return response.content
    
    return process_query
