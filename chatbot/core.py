# core.py - Raw wrapper for chatbot
# Provides raw input/output functions for cybersecurity chatbot

import os
import re
import numpy as np
import faiss
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer, util
import groq
from tavily import TavilyClient

# Get the directory where this file is located
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Configuration
_PDF_FILES = [
    os.path.join(_CURRENT_DIR, "CyberCrime Manual.pdf"),
    os.path.join(_CURRENT_DIR, "Indore Cybercrime Details and Actions_.pdf"),
    os.path.join(_CURRENT_DIR, "it_act_2000_updated.pdf"),
]
_MODEL_NAME = 'all-mpnet-base-v2'
_LLM_NAME = 'openai/gpt-oss-120b'

# API keys from environment variables
_GROQ_API_KEY_FALLBACK = os.environ.get("GROQ_API_KEY")
_TAVILY_API_KEY_FALLBACK = os.environ.get("TAVILY_API_KEY")


class ChatbotEngine:
    """
    RAG-based cybersecurity chatbot engine.
    Uses local PDF documents with web search fallback.
    """
    
    def __init__(self, pdf_files: list = None):
        """
        Initialize the chatbot engine.
        
        Args:
            pdf_files: Optional list of PDF file paths. Defaults to built-in PDFs.
        """
        self.pdf_files = pdf_files or _PDF_FILES
        self.embedding_model = None
        self.groq_client = None
        self.tavily_client = None
        self.vector_index = None
        self.chunks = []
        self._initialized = False
    
    def initialize(self) -> dict:
        """
        Initialize all components (models, clients, index).
        Call this before querying.
        
        Returns:
            dict with status and any errors
        """
        errors = []
        
        # Initialize Groq client
        try:
            api_key = os.environ.get("GROQ_API_KEY") or _GROQ_API_KEY_FALLBACK
            self.groq_client = groq.Groq(api_key=api_key)
        except Exception as e:
            errors.append(f"Groq client error: {e}")
        
        # Initialize Tavily client
        try:
            tavily_key = os.environ.get("TAVILY_API_KEY") or _TAVILY_API_KEY_FALLBACK
            self.tavily_client = TavilyClient(api_key=tavily_key)
        except Exception as e:
            errors.append(f"Tavily client error: {e}")
        
        # Load embedding model
        try:
            self.embedding_model = SentenceTransformer(_MODEL_NAME)
        except Exception as e:
            errors.append(f"Embedding model error: {e}")
            return {"status": "error", "errors": errors}
        
        # Load and index documents
        try:
            documents = self._load_pdfs()
            if documents:
                self.chunks = self._chunk_documents(documents)
                self.vector_index = self._create_index(self.chunks)
        except Exception as e:
            errors.append(f"Document indexing error: {e}")
        
        self._initialized = True
        
        return {
            "status": "success" if not errors else "partial",
            "documents_loaded": len(self.chunks),
            "errors": errors
        }
    
    def _load_pdfs(self) -> list:
        """Load text from PDF files."""
        documents = []
        for file_path in self.pdf_files:
            if not os.path.exists(file_path):
                continue
            try:
                reader = PdfReader(file_path)
                full_text = ""
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"
                documents.append({
                    "content": full_text,
                    "source": os.path.basename(file_path)
                })
            except Exception:
                continue
        return documents
    
    def _chunk_documents(self, documents: list, chunk_size: int = 1000, overlap: int = 200) -> list:
        """Split documents into overlapping chunks."""
        chunks = []
        for doc in documents:
            text = re.sub(r'\s+', ' ', doc['content']).strip()
            if not text:
                continue
            
            start = 0
            while start < len(text):
                end = start + chunk_size
                chunk_content = text[start:end]
                chunks.append({
                    "content": chunk_content,
                    "source": doc['source']
                })
                start += chunk_size - overlap
        
        return chunks
    
    def _create_index(self, chunks: list) -> faiss.IndexFlatIP:
        """Create FAISS vector index from chunks."""
        chunk_texts = [c['content'] for c in chunks]
        embeddings = self.embedding_model.encode(chunk_texts, convert_to_numpy=True)
        faiss.normalize_L2(embeddings)
        
        d = embeddings.shape[1]
        index = faiss.IndexFlatIP(d)
        index.add(embeddings)
        
        return index
    
    def _search_index(self, query: str, k: int = 5) -> list:
        """Search the vector index."""
        if not self.vector_index or not self.chunks:
            return []
        
        query_vector = self.embedding_model.encode([query])
        faiss.normalize_L2(query_vector)
        distances, indices = self.vector_index.search(query_vector, k)
        
        results = []
        for i in range(len(indices[0])):
            idx = indices[0][i]
            if idx < len(self.chunks):
                results.append({
                    "score": float(distances[0][i]),
                    "content": self.chunks[idx]['content'],
                    "source": self.chunks[idx]['source']
                })
        return results
    
    def _search_web(self, query: str) -> str:
        """Search the web using Tavily."""
        if not self.tavily_client:
            return None
        
        try:
            response = self.tavily_client.search(query=query, search_depth="basic")
            if response.get("answer"):
                return response["answer"]
            return "\n\n".join([r["content"] for r in response.get("results", [])])
        except Exception:
            return None
    
    def _synthesize_answer(self, query: str, context: str, source_type: str, sources: set) -> str:
        """Generate answer using LLM."""
        system_prompt = """
        You are an expert assistant. Your task is to synthesize information from the provided context to answer the user's query.
        1. Carefully read the User's Query and the provided CONTEXT.
        2. Synthesize the information into a single, coherent, and practical answer.
        3. If the context provides a sequence of actions or steps, present them as a clear, numbered list.
        4. Begin your response with a direct answer to the query. Do NOT say "Based on the context provided...".
        """
        
        user_prompt = f"""
        User's Query: "{query}"

        CONTEXT:
        {context}
        ---
        
        Synthesized Answer:
        """
        
        try:
            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=_LLM_NAME,
                temperature=0.2,
                max_tokens=1024
            )
            answer = chat_completion.choices[0].message.content
        except Exception as e:
            answer = f"An error occurred: {e}"
        
        # Add citation
        if source_type == "local" and sources:
            answer += f"\n\n*Source: {', '.join(sorted(sources))}*"
        elif source_type == "web":
            answer += "\n\n*Source: Web search*"
        
        return answer
    
    def query(self, question: str) -> dict:
        """
        Query the chatbot with a question.
        
        Args:
            question: The user's question
            
        Returns:
            dict with:
                - answer: str (the generated answer)
                - source_type: str ("local" or "web")
                - sources: list of source document names
                - error: str (only if error occurred)
        """
        if not self._initialized:
            init_result = self.initialize()
            if init_result["status"] == "error":
                return {"answer": "", "error": "Failed to initialize chatbot", "sources": []}
        
        # Search local documents
        search_results = self._search_index(question)
        
        # Filter relevant chunks
        query_emb = self.embedding_model.encode(question, convert_to_tensor=True)
        relevant_chunks = []
        sources = set()
        
        for result in search_results:
            chunk_emb = self.embedding_model.encode(result['content'], convert_to_tensor=True)
            similarity = util.cos_sim(query_emb, chunk_emb).item()
            if similarity > 0.5:
                relevant_chunks.append(result['content'])
                sources.add(result['source'])
        
        # Use local or web context
        if relevant_chunks:
            context = "\n\n---\n\n".join(list(dict.fromkeys(relevant_chunks)))
            source_type = "local"
        else:
            context = self._search_web(question)
            source_type = "web"
            sources = set()
            
            if not context:
                return {
                    "answer": "I could not find a relevant answer in the documents or online. Please try rephrasing your query.",
                    "source_type": "none",
                    "sources": []
                }
        
        # Generate answer
        answer = self._synthesize_answer(question, context, source_type, sources)
        
        return {
            "answer": answer,
            "source_type": source_type,
            "sources": list(sources)
        }


# Global instance for convenience
_chatbot_instance = None


def get_chatbot() -> ChatbotEngine:
    """Get or create the global chatbot instance."""
    global _chatbot_instance
    if _chatbot_instance is None:
        _chatbot_instance = ChatbotEngine()
        _chatbot_instance.initialize()
    return _chatbot_instance


def query_chatbot(question: str) -> dict:
    """
    Convenience function to query the chatbot.
    
    Args:
        question: The user's question
        
    Returns:
        dict with answer, source_type, sources
    """
    chatbot = get_chatbot()
    return chatbot.query(question)


# Test function
if __name__ == "__main__":
    import json
    
    print("Initializing chatbot...")
    chatbot = ChatbotEngine()
    init_result = chatbot.initialize()
    print(f"Init result: {json.dumps(init_result, indent=2)}")
    
    if init_result["status"] != "error":
        test_question = "What are the steps to file a cybercrime complaint?"
        print(f"\nQuery: {test_question}")
        result = chatbot.query(test_question)
        print(f"\nAnswer: {result['answer']}")
        print(f"Source: {result['source_type']}")
