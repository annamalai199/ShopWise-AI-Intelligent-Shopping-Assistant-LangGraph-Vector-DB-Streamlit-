from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

CHROMA_DIR = "chroma_store"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
SIMILARITY_THRESHOLD = 0.3


class EnhancedRetriever:
    def __init__(self, k_faq=3, k_tickets=3, k_guides=3, threshold=SIMILARITY_THRESHOLD):
        self.k_faq = k_faq
        self.k_tickets = k_tickets
        self.k_guides = k_guides
        self.threshold = threshold
        
        embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
        
        self.faq_store = Chroma(
            collection_name="faq",
            embedding_function=embeddings,
            persist_directory=CHROMA_DIR
        )
        self.tickets_store = Chroma(
            collection_name="tickets",
            embedding_function=embeddings,
            persist_directory=CHROMA_DIR
        )
        self.guides_store = Chroma(
            collection_name="guides",
            embedding_function=embeddings,
            persist_directory=CHROMA_DIR
        )
    
    def retrieve_with_scores(self, query):
        faq_results = self.faq_store.similarity_search_with_score(query, k=self.k_faq)
        ticket_results = self.tickets_store.similarity_search_with_score(query, k=self.k_tickets)
        guide_results = self.guides_store.similarity_search_with_score(query, k=self.k_guides)
        
        all_results = []
        
        for doc, score in faq_results:
            similarity = 1 - score
            if similarity >= self.threshold:
                doc.metadata["similarity_score"] = round(similarity, 3)
                all_results.append((doc, similarity))
        
        for doc, score in ticket_results:
            similarity = 1 - score
            if similarity >= self.threshold:
                doc.metadata["similarity_score"] = round(similarity, 3)
                all_results.append((doc, similarity))
        
        for doc, score in guide_results:
            similarity = 1 - score
            if similarity >= self.threshold:
                doc.metadata["similarity_score"] = round(similarity, 3)
                all_results.append((doc, similarity))
        
        all_results.sort(key=lambda x: x[1], reverse=True)
        
        return all_results
    
    def invoke(self, query):
        results = self.retrieve_with_scores(query)
        
        if not results:
            return None, []
        
        return "retrieved", [doc for doc, score in results]


def build_retriever(k_faq=3, k_tickets=3, k_guides=3, threshold=SIMILARITY_THRESHOLD):
    return EnhancedRetriever(k_faq, k_tickets, k_guides, threshold)
