"""
Vector Database - Stores embeddings for fast retrieval
Think of it as a search engine for meaning
We use ChromaDB (free, local, persistent)
"""

import chromadb
from chromadb.utils import embedding_functions
import numpy as np
from typing import List, Dict, Any  # ADD THIS IMPORT
from .embedding import EmbeddingGenerator

class VectorStore:
    """
    Manages vector storage and similarity search
    """
    
    def __init__(self, collection_name: str = "company_knowledge"):
        """
        Initialize ChromaDB client and collection
        collection_name = name of our "table" of vectors
        """
        # Create persistent client (saves to disk)
        self.client = chromadb.PersistentClient(path="./chroma_db")
        
        # Delete existing collection if it exists (for clean start)
        try:
            self.client.delete_collection(collection_name)
        except:
            pass
        
        # Create new collection
        self.collection = self.client.create_collection(
            name=collection_name,
            # Use our custom embedding function
            embedding_function=self._get_embedding_function()
        )
        
        self.embedder = EmbeddingGenerator()
        print(f"Vector store ready! Collection: {collection_name}")
    
    def _get_embedding_function(self):
        """
        ChromaDB needs its own embedding function
        This wraps our embedder for ChromaDB
        """
        class CustomEmbeddingFunction:
            def __init__(self, embedder):
                self.embedder = embedder
            
            def __call__(self, texts):
                return self.embedder.embed_documents(texts)
        
        return CustomEmbeddingFunction(self.embedder)
    
    def add_documents(self, documents: List[Dict[str, Any]]):
        """
        Add documents to vector store
        Each document = {
            'text': "content",
            'metadata': {'source': 'file.txt', 'role': 'manager'},
            'id': "unique_id"
        }
        """
        if not documents:
            return
        
        # Extract components
        ids = [doc['id'] for doc in documents]
        texts = [doc['text'] for doc in documents]
        metadatas = [doc.get('metadata', {}) for doc in documents]
        
        # Add to ChromaDB
        self.collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas
        )
        
        print(f"Added {len(documents)} documents to vector store")
    
    def search(self, query: str, top_k: int = 5, filter_dict: Dict = None) -> List[Dict]:
        """
        Search for similar documents
        query: User's question
        top_k: Number of results to return
        filter_dict: Filter by metadata (for RBAC)
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=filter_dict  # For role-based filtering
        )
        
        # Format results nicely
        formatted_results = []
        if results['documents'][0]:
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if results['distances'] else None
                })
        
        return formatted_results
    
    def delete_all(self):
        """Clear the vector store"""
        # Get all IDs and delete them
        all_ids = self.collection.get()['ids']
        if all_ids:
            self.collection.delete(ids=all_ids)
        print("Cleared vector store")

# Test
if __name__ == "__main__":
    store = VectorStore()
    
    # Add a test document
    test_doc = [{
        'id': 'test_1',
        'text': 'Employees get 20 vacation days',
        'metadata': {'source': 'policy.txt', 'role': 'employee'}
    }]
    store.add_documents(test_doc)
    
    # Search
    results = store.search("How many vacation days?")
    for r in results:
        print(f"Found: {r['text']}")
        print(f"Metadata: {r['metadata']}")
