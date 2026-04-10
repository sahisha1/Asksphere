"""
RAG Pipeline - Retrieval Augmented Generation
This is the brain of our system!
Steps:
1. User asks question
2. Find relevant documents (Retrieval)
3. Send documents + question to LLM
4. LLM answers based ONLY on those documents
"""

from groq import Groq
from dotenv import load_dotenv
import os
from typing import List, Dict, Any  # ADD THIS IMPORT
from .vector_store import VectorStore
from .rbac import RoleBasedAccess

try:
    from langchain_core.documents import Document
except ImportError:
    from langchain.schema import Document

# Load API key
load_dotenv()

class RAGPipeline:
    """
    Main AI answering system


    """
    pass
    
    def __init__(self):
        """Initialize the pipeline"""
        # Initialize Groq client (free LLM)
        self.client = Groq(
            api_key=os.getenv('GROQ_API_KEY')
        )
        
        # Initialize vector store
        self.vector_store = VectorStore()
        
        # Initialize RBAC
        self.rbac = RoleBasedAccess()
        
        # Model selection (free tier)
        self.model = "llama3-8b-8192"  # 8B parameters, very fast
        # Alternative: "mixtral-8x7b-32768" (smarter, slower)
    
    def answer_question(self, question: str, user_role: str = "employee") -> dict:
        """
        Answer a question using RAG
        Returns: {
            'answer': str,
            'sources': list,
            'confidence': float
        }
        """
        
        # Step 1: Check if user has access to ask this
        if not self.rbac.can_query(user_role, question):
            return {
                'answer': "I'm sorry, you don't have permission to ask about this topic.",
                'sources': [],
                'confidence': 0
            }
        
        # Step 2: Retrieve relevant documents (with role filtering)
        filter_dict = self.rbac.get_filter(user_role)
        retrieved_docs = self.vector_store.search(
            query=question,
            top_k=5,
            filter_dict=filter_dict
        )
        
        if not retrieved_docs:
            return {
                'answer': "I couldn't find any relevant information in the company knowledge base.",
                'sources': [],
                'confidence': 0
            }
        
        # Step 3: Prepare context from retrieved documents
        context = "\n\n---\n\n".join([
            f"Source: {doc['metadata'].get('source', 'Unknown')}\nContent: {doc['text']}"
            for doc in retrieved_docs
        ])
        
        # Step 4: Create prompt for LLM
        prompt = f"""You are an AI assistant for a company. Answer the question based ONLY on the provided context.

Your role: {user_role}

Context from company documents:
{context}

Question: {question}

Instructions:
1. ONLY use information from the context above
2. If the answer isn't in the context, say "I don't have that information"
3. Be concise and professional
4. If mentioning numbers or policies, cite the source

Answer:"""
        
        # Step 5: Get LLM response
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful company assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower = more factual, less creative
                max_tokens=500
            )
            
            answer = response.choices[0].message.content
            
            # Calculate simple confidence score
            confidence = min(len(retrieved_docs) / 10, 1.0)
            
            return {
                'answer': answer,
                'sources': [doc['metadata'] for doc in retrieved_docs],
                'confidence': confidence
            }
            
        except Exception as e:
            return {
                'answer': f"Error: {str(e)}",
                'sources': [],
                'confidence': 0
            }
    
    def add_document(self, text: str, metadata: dict):
        """Add a document to the knowledge base"""
        # Chunk long documents
        chunks = self._chunk_text(text)
        
        documents = []
        for i, chunk in enumerate(chunks):
            documents.append({
                'id': f"{metadata.get('source', 'doc')}_{i}",
                'text': chunk,
                'metadata': metadata
            })
        
        self.vector_store.add_documents(documents)
        return len(documents)
    
    def _chunk_text(self, text: str, chunk_size: int = 500) -> List[str]:
        """Split long text into chunks for better retrieval"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size):
            chunk = ' '.join(words[i:i+chunk_size])
            chunks.append(chunk)
        
        return chunks

# Test
if __name__ == "__main__":
    rag = RAGPipeline()
    
    # Test with a question
    result = rag.answer_question(
        "How many vacation days do employees get?",
        user_role="employee"
    )
    
    print(f"Answer: {result['answer']}")
    print(f"\nSources: {result['sources']}")
    print(f"Confidence: {result['confidence']}")