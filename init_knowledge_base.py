"""
One-time script to index all documents
Run this after adding new documents
"""

from src.document_loader import DocumentLoader
from src.rag_pipeline import RAGPipeline
from src.vector_store import VectorStore

def main():
    print("📚 Initializing Knowledge Base...")
    
    # Load documents
    loader = DocumentLoader()
    documents = loader.load_all_documents()
    
    # Initialize RAG pipeline
    rag = RAGPipeline()
    
    # Add each document
    for doc in documents:
        # Set sensitivity based on source
        sensitivity = 1  # Default
        if 'salary' in doc.metadata.get('source', '').lower():
            sensitivity = 4
        elif 'confidential' in doc.metadata.get('source', '').lower():
            sensitivity = 5
        
        doc.metadata['sensitivity'] = sensitivity
        
        # Add to knowledge base
        rag.add_document(
            text=doc.page_content,
            metadata=doc.metadata
        )
    
    print("✅ Knowledge base ready!")

if __name__ == "__main__":
    main()