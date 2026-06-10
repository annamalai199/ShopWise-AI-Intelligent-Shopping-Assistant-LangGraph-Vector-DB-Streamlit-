import os
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

import sqlite3
import pandas as pd
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


CHROMA_DIR = "chroma_store"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

FAQ_COLLECTION = "faq"
GUIDES_COLLECTION = "guides"
TICKETS_COLLECTION = "tickets"

CSV_PATH = os.path.join("data", "faq.csv")
PDF_PATH = os.path.join("data", "telecom_guide.pdf")
DB_PATH = os.path.join("data", "tickets.db")

CHUNK_SIZE = 600
CHUNK_OVERLAP = 100


def load_faq_documents(csv_path):
    df = pd.read_csv(csv_path)
    docs = []
    for _, row in df.iterrows():
        content = f"Q: {row['question']}\nA: {row['answer']}"
        docs.append(Document(
            page_content=content,
            metadata={
                "source": "faq",
                "category": row["category"],
                "faq_id": str(row["id"])
            }
        ))
    return docs


def load_pdf_documents(pdf_path):
    loader = PyPDFLoader(pdf_path)
    pages = loader.load()
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " "]
    )
    chunks = splitter.split_documents(pages)
    
    for i, chunk in enumerate(chunks):
        chunk.metadata["source"] = "guide"
        chunk.metadata["chunk_index"] = i
    
    return pages, chunks


def load_ticket_documents(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM tickets WHERE status = 'resolved'").fetchall()
    conn.close()
    
    docs = []
    for row in rows:
        content = (
            f"Issue: {row['issue_type']}\n"
            f"Description: {row['description']}\n"
            f"Resolution: {row['resolution']}"
        )
        docs.append(Document(
            page_content=content,
            metadata={
                "source": "ticket",
                "ticket_id": row["ticket_id"],
                "category": row["category"],
                "status": row["status"]
            }
        ))
    return docs


def ingest_faqs():
    print("Loading FAQ documents...")
    docs = load_faq_documents(CSV_PATH)
    print(f"  {len(docs)} FAQ entries loaded.")
    
    print("Initialising embedding model...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    
    print(f"Embedding and storing in Chroma collection '{FAQ_COLLECTION}'...")
    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name=FAQ_COLLECTION,
        persist_directory=CHROMA_DIR
    )
    print(f"  Done. {vectorstore._collection.count()} vectors stored.")


def ingest_pdf():
    print("Loading PDF...")
    pages, chunks = load_pdf_documents(PDF_PATH)
    print(f"  {len(pages)} pages loaded.")
    print(f"  {len(chunks)} chunks produced.")
    
    print("Initialising embedding model...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    
    print(f"Embedding and storing in Chroma collection '{GUIDES_COLLECTION}'...")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=GUIDES_COLLECTION,
        persist_directory=CHROMA_DIR
    )
    print(f"  Done. {vectorstore._collection.count()} vectors stored.")


def ingest_tickets():
    print("Loading ticket documents from SQLite...")
    docs = load_ticket_documents(DB_PATH)
    print(f"  {len(docs)} resolved tickets loaded.")
    
    print("Initialising embedding model...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    
    print(f"Embedding and storing in Chroma collection '{TICKETS_COLLECTION}'...")
    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name=TICKETS_COLLECTION,
        persist_directory=CHROMA_DIR
    )
    print(f"  Done. {vectorstore._collection.count()} vectors stored.")


def main():
    print("=" * 70)
    print("Telecom Chatbot Data Ingestion")
    print("=" * 70)
    print()
    
    print("Step 1: Ingesting FAQs from CSV")
    ingest_faqs()
    print()
    
    print("Step 2: Ingesting Telecom Guide from PDF")
    ingest_pdf()
    print()
    
    print("Step 3: Ingesting Resolved Tickets from Database")
    ingest_tickets()
    print()
    
    print("=" * 70)
    print("All data ingested successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
