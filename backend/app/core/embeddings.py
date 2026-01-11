"""
Embedding Generation Module

Generates embeddings using Google's text-embedding-004 model.
"""

from google import genai
from typing import List, Optional
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

logger = logging.getLogger(__name__)

# Initialize Gemini client
_client: Optional[genai.Client] = None


def get_client() -> genai.Client:
    """Get or create the Gemini client."""
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding for a single text.
    
    Args:
        text: Text to embed
        
    Returns:
        List[float]: Embedding vector
    """
    client = get_client()
    
    result = client.models.embed_content(
        model=settings.embedding_model,
        contents=text
    )
    
    return result.embeddings[0].values


async def generate_embeddings_batch(
    texts: List[str],
    batch_size: int = 100
) -> List[List[float]]:
    """
    Generate embeddings for multiple texts in batches.
    
    Args:
        texts: List of texts to embed
        batch_size: Number of texts per batch
        
    Returns:
        List[List[float]]: List of embedding vectors
    """
    client = get_client()
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        logger.info(f"Embedding batch {i // batch_size + 1}/{(len(texts) - 1) // batch_size + 1}")
        
        result = client.models.embed_content(
            model=settings.embedding_model,
            contents=batch
        )
        
        batch_embeddings = [emb.values for emb in result.embeddings]
        all_embeddings.extend(batch_embeddings)
    
    return all_embeddings


async def embed_query(query: str) -> List[float]:
    """
    Generate embedding for a search query.
    
    Uses the same model but can apply query-specific preprocessing.
    
    Args:
        query: Search query text
        
    Returns:
        List[float]: Query embedding vector
    """
    # For retrieval, we can optionally prefix the query
    # to improve search relevance
    processed_query = f"search_query: {query}"
    return await generate_embedding(processed_query)


def get_embedding_dimensions() -> int:
    """Get the embedding dimensions for the current model."""
    # text-embedding-004 produces 768-dimensional vectors
    return 768
