import os
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

from dotenv import load_dotenv
from retriever import build_retriever
from colorama import init, Fore, Style

init(autoreset=True)
load_dotenv()


TEST_CASES = [
    {
        "question": "My internet is very slow even with full signal bars",
        "expected_source": "ticket",
        "expected_id": "TK-1001",
        "category": "connectivity"
    },
    {
        "question": "Calls are dropping frequently in my area",
        "expected_source": "ticket",
        "expected_id": "TK-1002",
        "category": "connectivity"
    },
    {
        "question": "How do I enable international roaming?",
        "expected_source": "faq",
        "expected_id": "5",
        "category": "roaming"
    },
    {
        "question": "My SIM card is not being detected by the phone",
        "expected_source": "ticket",
        "expected_id": "TK-1005",
        "category": "technical"
    },
    {
        "question": "I was charged for international calls but I have a roaming package",
        "expected_source": "ticket",
        "expected_id": "TK-1007",
        "category": "billing"
    },
    {
        "question": "What is the cancellation policy for my plan?",
        "expected_source": "faq",
        "expected_id": "8",
        "category": "billing"
    },
    {
        "question": "How do I check my data balance?",
        "expected_source": "faq",
        "expected_id": "2",
        "category": "account"
    },
    {
        "question": "My voicemail is not working properly",
        "expected_source": "ticket",
        "expected_id": "TK-1004",
        "category": "technical"
    },
    {
        "question": "Can I unlock my phone to use with another carrier?",
        "expected_source": "faq",
        "expected_id": "7",
        "category": "technical"
    },
    {
        "question": "Why is my bill higher than usual this month?",
        "expected_source": "ticket",
        "expected_id": "TK-1006",
        "category": "billing"
    }
]


def evaluate_retrieval(top_k=3):
    retriever = build_retriever()
    
    results = {
        "total": len(TEST_CASES),
        "top1_hits": 0,
        "top3_hits": 0,
        "top5_hits": 0,
        "no_results": 0,
        "details": []
    }
    
    print("=" * 80)
    print(f"{Fore.CYAN}TELECOM RAG RETRIEVAL EVALUATION{Style.RESET_ALL}")
    print("=" * 80)
    print(f"\nEvaluating {len(TEST_CASES)} test cases with top-{top_k} retrieval...\n")
    
    for i, test in enumerate(TEST_CASES, 1):
        question = test["question"]
        expected_source = test["expected_source"]
        expected_id = test["expected_id"]
        
        print(f"{Fore.YELLOW}[{i}/{len(TEST_CASES)}]{Style.RESET_ALL} {question[:60]}...")
        
        status, docs = retriever.invoke(question)
        
        if status is None or not docs:
            results["no_results"] += 1
            print(f"  {Fore.RED}✗ No results above threshold{Style.RESET_ALL}\n")
            results["details"].append({
                "question": question,
                "expected": f"{expected_source}:{expected_id}",
                "found_position": None,
                "success": False
            })
            continue
        
        found_position = None
        retrieved_ids = []
        
        for idx, doc in enumerate(docs[:5], 1):
            source = doc.metadata.get("source", "")
            doc_id = None
            
            if source == "faq":
                doc_id = doc.metadata.get("faq_id", "")
            elif source == "ticket":
                doc_id = doc.metadata.get("ticket_id", "")
            
            retrieved_ids.append(f"{source}:{doc_id}")
            
            if source == expected_source and doc_id == expected_id:
                found_position = idx
                break
        
        if found_position:
            if found_position == 1:
                results["top1_hits"] += 1
                results["top3_hits"] += 1
                results["top5_hits"] += 1
                print(f"  {Fore.GREEN}✓ Found at position {found_position} (TOP-1 HIT){Style.RESET_ALL}")
            elif found_position <= 3:
                results["top3_hits"] += 1
                results["top5_hits"] += 1
                print(f"  {Fore.GREEN}✓ Found at position {found_position} (TOP-3 HIT){Style.RESET_ALL}")
            elif found_position <= 5:
                results["top5_hits"] += 1
                print(f"  {Fore.YELLOW}○ Found at position {found_position} (TOP-5 HIT){Style.RESET_ALL}")
            
            results["details"].append({
                "question": question,
                "expected": f"{expected_source}:{expected_id}",
                "found_position": found_position,
                "success": True
            })
        else:
            print(f"  {Fore.RED}✗ Not found in top 5 results{Style.RESET_ALL}")
            print(f"    Retrieved: {', '.join(retrieved_ids[:3])}")
            results["details"].append({
                "question": question,
                "expected": f"{expected_source}:{expected_id}",
                "found_position": None,
                "success": False
            })
        
        print()
    
    print("=" * 80)
    print(f"{Fore.CYAN}EVALUATION RESULTS{Style.RESET_ALL}")
    print("=" * 80)
    print(f"\nTotal test cases: {results['total']}")
    print(f"\n{Fore.GREEN}Top-1 Recall:{Style.RESET_ALL} {results['top1_hits']}/{results['total']} ({results['top1_hits']/results['total']*100:.1f}%)")
    print(f"{Fore.GREEN}Top-3 Recall:{Style.RESET_ALL} {results['top3_hits']}/{results['total']} ({results['top3_hits']/results['total']*100:.1f}%)")
    print(f"{Fore.GREEN}Top-5 Recall:{Style.RESET_ALL} {results['top5_hits']}/{results['total']} ({results['top5_hits']/results['total']*100:.1f}%)")
    print(f"{Fore.RED}No results:{Style.RESET_ALL} {results['no_results']}/{results['total']}")
    
    print("\n" + "=" * 80)
    
    failed_cases = [d for d in results["details"] if not d["success"]]
    if failed_cases:
        print(f"\n{Fore.RED}FAILED CASES:{Style.RESET_ALL}")
        for case in failed_cases:
            print(f"  • {case['question'][:60]}...")
            print(f"    Expected: {case['expected']}")
    
    print("\n" + "=" * 80)
    
    return results


if __name__ == "__main__":
    try:
        import colorama
    except ImportError:
        print("Installing colorama for better output...")
        os.system("pip install colorama")
        from colorama import init, Fore, Style
        init(autoreset=True)
    
    evaluate_retrieval(top_k=3)
