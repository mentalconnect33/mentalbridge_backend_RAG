import openai
import numpy as np
from typing import List
from app.config import settings

openai.api_key = settings.OPENAI_API_KEY

def get_embedding(text: str) -> List[float]:
    """Generate an embedding for the given text."""
    if not text:
        return [0] * settings.EMBEDDING_DIM
    
    text = text.replace("\n", " ")
    if len(text) > 2000:
        text = text[:2000]
    
    try:
        response = openai.Embedding.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response["data"][0]["embedding"]
    except Exception as e:
        print(f"Error getting embedding: {str(e)}")
        # Return zero vector as fallback
        return [0] * settings.EMBEDDING_DIM

def format_embedding_for_postgres(embedding: List[float]) -> str:
    """Format a list of floats as a Postgres array string."""
    return str(embedding).replace('[', '{').replace(']', '}')

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    a = np.array(vec1)
    b = np.array(vec2)
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0 
    
    return dot_product / (norm_a * norm_b)
