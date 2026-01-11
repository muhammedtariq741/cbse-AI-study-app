"""
FAISS Vector Store

Local vector database implementation using FAISS for similarity search.
"""

import faiss
import numpy as np
import json
import os
from typing import List, Optional, Dict, Any
from pathlib import Path
import logging

from app.config import settings
from app.models.schemas import Chunk, ChunkMetadata, RetrievalResult

logger = logging.getLogger(__name__)


class FAISSVectorStore:
    """
    FAISS-based vector store with metadata filtering.
    
    Stores embeddings in FAISS index and metadata in JSON for filtering.
    """
    
    def __init__(
        self,
        index_path: Optional[str] = None,
        dimension: int = 768
    ):
        """
        Initialize the vector store.
        
        Args:
            index_path: Path to store/load the index
            dimension: Embedding dimension (768 for text-embedding-004)
        """
        self.dimension = dimension
        self.index_path = Path(index_path or settings.vector_store_path)
        self.index_name = settings.faiss_index_name
        
        # FAISS index
        self.index: Optional[faiss.Index] = None
        
        # Metadata storage (chunk_id -> metadata)
        self.metadata: Dict[str, Dict[str, Any]] = {}
        
        # Chunk storage (chunk_id -> full chunk)
        self.chunks: Dict[str, Chunk] = {}
        
        # ID mapping (faiss_id -> chunk_id)
        self.id_mapping: List[str] = []
        
        # Ensure directory exists
        self.index_path.mkdir(parents=True, exist_ok=True)
    
    def _get_index_file(self) -> Path:
        return self.index_path / f"{self.index_name}.index"
    
    def _get_metadata_file(self) -> Path:
        return self.index_path / f"{self.index_name}_metadata.json"
    
    def _get_chunks_file(self) -> Path:
        return self.index_path / f"{self.index_name}_chunks.json"
    
    def create_index(self):
        """Create a new FAISS index."""
        # Using IndexFlatIP for inner product (cosine similarity with normalized vectors)
        self.index = faiss.IndexFlatIP(self.dimension)
        self.metadata = {}
        self.chunks = {}
        self.id_mapping = []
        logger.info(f"Created new FAISS index with dimension {self.dimension}")
    
    def load(self) -> bool:
        """
        Load existing index from disk.
        
        Returns:
            bool: True if loaded successfully
        """
        index_file = self._get_index_file()
        metadata_file = self._get_metadata_file()
        chunks_file = self._get_chunks_file()
        
        if not index_file.exists():
            logger.warning(f"Index file not found: {index_file}")
            return False
        
        try:
            # Load FAISS index
            self.index = faiss.read_index(str(index_file))
            
            # Load metadata
            if metadata_file.exists():
                with open(metadata_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.metadata = data.get("metadata", {})
                    self.id_mapping = data.get("id_mapping", [])
            
            # Load chunks
            if chunks_file.exists():
                with open(chunks_file, "r", encoding="utf-8") as f:
                    chunks_data = json.load(f)
                    self.chunks = {
                        k: Chunk(**v) for k, v in chunks_data.items()
                    }
            
            logger.info(f"Loaded index with {self.index.ntotal} vectors")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            return False
    
    def save(self):
        """Save index and metadata to disk."""
        index_file = self._get_index_file()
        metadata_file = self._get_metadata_file()
        chunks_file = self._get_chunks_file()
        
        # Save FAISS index
        faiss.write_index(self.index, str(index_file))
        
        # Save metadata and ID mapping
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump({
                "metadata": self.metadata,
                "id_mapping": self.id_mapping
            }, f, ensure_ascii=False, indent=2)
        
        # Save chunks
        with open(chunks_file, "w", encoding="utf-8") as f:
            chunks_data = {k: v.model_dump(mode="json") for k, v in self.chunks.items()}
            json.dump(chunks_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved index with {self.index.ntotal} vectors to {self.index_path}")
    
    def add(
        self,
        chunks: List[Chunk],
        embeddings: List[List[float]]
    ):
        """
        Add chunks and their embeddings to the index.
        
        Args:
            chunks: List of chunks to add
            embeddings: Corresponding embeddings
        """
        if self.index is None:
            self.create_index()
        
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks must match number of embeddings")
        
        # Normalize embeddings for cosine similarity
        embeddings_array = np.array(embeddings, dtype=np.float32)
        faiss.normalize_L2(embeddings_array)
        
        # Add to FAISS
        self.index.add(embeddings_array)
        
        # Store metadata and chunks
        for chunk in chunks:
            self.id_mapping.append(chunk.chunk_id)
            self.metadata[chunk.chunk_id] = chunk.metadata.model_dump(mode="json")
            self.chunks[chunk.chunk_id] = chunk
        
        logger.info(f"Added {len(chunks)} chunks to index (total: {self.index.ntotal})")
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalResult]:
        """
        Search for similar chunks.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            filters: Metadata filters (e.g., {"subject": "Science", "class": 9})
            
        Returns:
            List[RetrievalResult]: Ranked search results
        """
        if self.index is None or self.index.ntotal == 0:
            logger.warning("Index is empty")
            return []
        
        # Normalize query embedding
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search with extra results for filtering
        search_k = min(top_k * 3, self.index.ntotal)
        distances, indices = self.index.search(query_array, search_k)
        
        results = []
        for rank, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx == -1:  # FAISS returns -1 for missing results
                continue
            
            chunk_id = self.id_mapping[idx]
            chunk = self.chunks.get(chunk_id)
            
            if chunk is None:
                continue
            
            # Apply filters
            if filters:
                metadata = self.metadata.get(chunk_id, {})
                if not self._matches_filters(metadata, filters):
                    continue
            
            results.append(RetrievalResult(
                chunk=chunk,
                score=float(distance),  # Cosine similarity (0-1)
                rank=len(results) + 1
            ))
            
            if len(results) >= top_k:
                break
        
        return results
    
    def _matches_filters(
        self,
        metadata: Dict[str, Any],
        filters: Dict[str, Any]
    ) -> bool:
        """Check if metadata matches all filters."""
        for key, value in filters.items():
            if key not in metadata:
                return False
            
            # Handle list values (e.g., marks_relevance)
            if isinstance(metadata[key], list):
                if value not in metadata[key]:
                    return False
            elif metadata[key] != value:
                return False
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        return {
            "total_vectors": self.index.ntotal if self.index else 0,
            "dimension": self.dimension,
            "index_path": str(self.index_path),
            "subjects": self._count_by_field("subject"),
            "chapters": self._count_by_field("chapter")
        }
    
    def _count_by_field(self, field: str) -> Dict[str, int]:
        """Count chunks by a metadata field."""
        counts = {}
        for chunk_id, meta in self.metadata.items():
            value = meta.get(field, "unknown")
            counts[value] = counts.get(value, 0) + 1
        return counts


# Singleton instance
_vector_store: Optional[FAISSVectorStore] = None


def get_vector_store() -> FAISSVectorStore:
    """Get or create the vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = FAISSVectorStore()
        _vector_store.load()  # Try to load existing index
    return _vector_store
