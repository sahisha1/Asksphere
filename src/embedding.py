"""
Embeddings - Converts text into numerical vectors
Why? Computers understand numbers better than words
We use sentence-transformers (free, runs locally)
"""

from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List  # ADD THIS IMPORT

class EmbeddingGenerator:
    """
    Creates vector embeddings from text
    Vector = list of numbers representing meaning
    Similar meaning = similar numbers
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        model_name: Which embedding model to use
        all-MiniLM-L6-v2 = Small, fast, free, runs on CPU
        Size: 384 dimensions (good balance of speed/accuracy)
        """
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        print("Model loaded!")
    
    def embed_text(self, text: str) -> List[float]:
        """
        Convert a single text to vector
        Input: "Hello world"
        Output: [0.123, -0.456, 0.789, ...] (384 numbers)
        """
        vector = self.model.encode(text)
        return vector.tolist()
    
    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """
        Convert multiple texts to vectors at once
        Faster than doing one by one
        """
        vectors = self.model.encode(documents)
        return vectors.tolist()
    
    def embed_chunks(self, chunks: List[str]) -> np.ndarray:
        """
        Embed document chunks for batch processing
        """
        return self.model.encode(chunks)

# Test the embeddings
if __name__ == "__main__":
    embedder = EmbeddingGenerator()
    
    # Test with similar sentences
    text1 = "The employee gets 20 vacation days"
    text2 = "Workers receive 20 days of paid time off"
    text3 = "The weather is nice today"
    
    vec1 = embedder.embed_text(text1)
    vec2 = embedder.embed_text(text2)
    vec3 = embedder.embed_text(text3)
    
    print(f"Vector dimension: {len(vec1)}")
    
    # Cosine similarity (higher = more similar)
    from sklearn.metrics.pairwise import cosine_similarity
    sim_1_2 = cosine_similarity([vec1], [vec2])[0][0]
    sim_1_3 = cosine_similarity([vec1], [vec3])[0][0]
    
    print(f"Similarity between similar texts: {sim_1_2:.3f}")  # Should be high (~0.8)
    print(f"Similarity between different texts: {sim_1_3:.3f}")  # Should be low (~0.2)