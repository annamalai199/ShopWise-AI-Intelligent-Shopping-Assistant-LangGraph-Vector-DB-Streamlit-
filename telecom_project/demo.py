import os
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

from dotenv import load_dotenv
from rag_chain import build_chain
from colorama import init, Fore, Style

init(autoreset=True)
load_dotenv()


DEMO_QUESTIONS = [
    "Why is my mobile internet so slow?",
    "How do I activate international roaming?",
    "My SIM card is not being detected",
    "Can you explain the quantum theory of relativity?",
]


def run_demo():
    print("=" * 80)
    print(f"{Fore.CYAN}TELECOM RAG CHATBOT - LIVE DEMO{Style.RESET_ALL}")
    print("=" * 80)
    print("\nDemonstrating key features:")
    print("  ✓ Multi-source retrieval (FAQ + Tickets + Guides)")
    print("  ✓ Source citations")
    print("  ✓ Confidence scoring")
    print("  ✓ Fallback logic\n")
    print("=" * 80)
    
    chain = build_chain()
    
    for i, question in enumerate(DEMO_QUESTIONS, 1):
        print(f"\n{Fore.YELLOW}[Question {i}/{len(DEMO_QUESTIONS)}]{Style.RESET_ALL}")
        print(f"{Fore.WHITE}{question}{Style.RESET_ALL}")
        print(f"\n{Fore.CYAN}Assistant:{Style.RESET_ALL}")
        
        response = chain({"question": question})
        
        if "[FAQ" in response or "[Ticket" in response or "[Guide" in response:
            print(f"{Fore.GREEN}{response}{Style.RESET_ALL}")
        elif "don't have" in response or "611" in response:
            print(f"{Fore.YELLOW}{response}{Style.RESET_ALL}")
        else:
            print(f"{Fore.WHITE}{response}{Style.RESET_ALL}")
        
        print("\n" + "-" * 80)
    
    print(f"\n{Fore.GREEN}Demo completed!{Style.RESET_ALL}")
    print("\nKey takeaways:")
    print("  • Questions 1-3: Retrieved from knowledge base with citations")
    print("  • Question 4: Outside domain → Fallback message triggered")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        import colorama
    except ImportError:
        print("Installing colorama...")
        os.system("pip install colorama")
        from colorama import init, Fore, Style
        init(autoreset=True)
    
    run_demo()
