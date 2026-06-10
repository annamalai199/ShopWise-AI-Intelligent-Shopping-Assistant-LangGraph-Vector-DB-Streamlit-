import os
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

from dotenv import load_dotenv
from rag_chain import build_chain

load_dotenv()


def main():
    print("=" * 70)
    print("Telecom Customer Care Chatbot (Enhanced RAG)")
    print("=" * 70)
    print("Features:")
    print("  ✓ Source citations (FAQ #ID, Ticket #ID, Guide p.X)")
    print("  ✓ Confidence scoring with fallback logic")
    print("  ✓ Multi-source retrieval (FAQ + Tickets + Guides)")
    print("\nType your question and press Enter. Type 'quit' to exit.\n")
    
    chain = build_chain()
    
    while True:
        question = input("Customer: ").strip()
        if not question:
            continue
        if question.lower() in {"quit", "exit", "q"}:
            print("Goodbye!")
            break
        
        print("\nAssistant:")
        response = chain({"question": question})
        print(response)
        print("\n" + "-" * 70 + "\n")


if __name__ == "__main__":
    main()
