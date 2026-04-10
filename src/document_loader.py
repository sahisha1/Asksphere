"""
Document Loader - Reads different file types
This handles PDFs, text files, Word docs, and more
"""

# Fix for latest LangChain version
try:
    # Try new import path (LangChain >= 0.3)
    from langchain_core.documents import Document
    from langchain_community.document_loaders import PyPDFLoader, TextLoader
except ImportError:
    # Fall back to old import path
    from langchain.schema import Document
    from langchain_community.document_loaders import PyPDFLoader, TextLoader

import os
from typing import List

class DocumentLoader:
    """
    Loads documents from various sources
    Currently supports: .txt, .pdf
    Can easily add: .docx, .md, Slack, GitHub
    """
    
    def __init__(self, data_path: str = "data"):
        self.data_path = data_path
        self.supported_extensions = {
            '.txt': self._load_text,
            '.pdf': self._load_pdf,
            # Add more loaders here
        }
    
    def _load_text(self, file_path: str) -> List[Document]:
        """Load text files"""
        loader = TextLoader(file_path, encoding='utf-8')
        return loader.load()
    
    def _load_pdf(self, file_path: str) -> List[Document]:
        """Load PDF files"""
        loader = PyPDFLoader(file_path)
        return loader.load()
    
    def load_all_documents(self) -> List[Document]:
        """
        Load all documents from the data folder
        Returns: List of LangChain Document objects
        """
        all_documents = []
        
        # Create data folder if it doesn't exist
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)
            print(f"Created {self.data_path} folder. Please add documents there.")
            return []
        
        # Loop through all files in data folder
        for filename in os.listdir(self.data_path):
            file_path = os.path.join(self.data_path, filename)
            
            # Skip directories
            if os.path.isdir(file_path):
                continue
                
            # Get file extension
            _, ext = os.path.splitext(filename)
            ext = ext.lower()
            
            # Load based on extension
            if ext in self.supported_extensions:
                print(f"Loading: {filename}")
                try:
                    documents = self.supported_extensions[ext](file_path)
                    
                    # Add metadata (important for RBAC!)
                    for doc in documents:
                        doc.metadata['source'] = filename
                        doc.metadata['file_type'] = ext
                    
                    all_documents.extend(documents)
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
            else:
                print(f"Skipping unsupported file: {filename}")
        
        print(f"Loaded {len(all_documents)} document chunks")
        return all_documents

# Quick test
if __name__ == "__main__":
    loader = DocumentLoader()
    docs = loader.load_all_documents()
    for doc in docs[:2]:  # Show first 2
        print(f"Content: {doc.page_content[:100]}...")
        print(f"Metadata: {doc.metadata}")