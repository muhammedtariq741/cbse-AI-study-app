"""
Retriever Module

Handles the retrieval logic for finding relevant chunks.
"""

from typing import List, Optional, Dict, Any
import logging
import re

from app.storage.vector_store import get_vector_store, FAISSVectorStore
from app.core.embeddings import embed_query
from app.models.schemas import RetrievalResult, Chunk
from app.config import settings

logger = logging.getLogger(__name__)


class QueryProcessor:
    """
    Processes student queries to extract metadata.
    
    Uses rule-based extraction (no ML) for reliability.
    """
    
    # Subject detection patterns
    SUBJECT_PATTERNS = {
        "Science": [
            r"photosynthesis", r"cell", r"atom", r"molecule", r"chemical",
            r"physics", r"biology", r"chemistry", r"matter", r"force",
            r"energy", r"electric", r"magnetic", r"light", r"sound",
            r"tissue", r"organ", r"element", r"compound", r"reaction"
        ],
        "Mathematics": [
            r"equation", r"polynomial", r"quadratic", r"linear", r"triangle",
            r"circle", r"angle", r"theorem", r"proof", r"calculate",
            r"solve", r"graph", r"coordinate", r"algebra", r"geometry",
            r"number", r"ratio", r"percentage", r"probability", r"statistics"
        ],
        "Social Science": [
            r"history", r"geography", r"civics", r"economics", r"democracy",
            r"constitution", r"revolution", r"war", r"empire", r"colony",
            r"climate", r"population", r"agriculture", r"industry", r"poverty",
            r"government", r"parliament", r"election", r"rights", r"freedom"
        ],
        "English": [
            r"poem", r"poetry", r"story", r"character", r"theme",
            r"grammar", r"tense", r"voice", r"narration", r"letter",
            r"essay", r"summary", r"meaning", r"literary", r"author"
        ]
    }
    
    # Marks detection patterns
    MARKS_PATTERNS = [
        (r"(\d+)\s*marks?", 1),
        (r"for\s*(\d+)", 1),
        (r"(\d+)\s*point", 1),
    ]
    
    def extract_subject(self, query: str) -> Optional[str]:
        """Extract subject from query using keyword matching."""
        query_lower = query.lower()
        
        scores = {}
        for subject, patterns in self.SUBJECT_PATTERNS.items():
            score = sum(1 for p in patterns if re.search(p, query_lower))
            if score > 0:
                scores[subject] = score
        
        if scores:
            return max(scores, key=scores.get)
        return None
    
    def extract_marks(self, query: str) -> Optional[int]:
        """Extract expected marks from query."""
        for pattern, group in self.MARKS_PATTERNS:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                marks = int(match.group(group))
                if marks in [1, 2, 3, 5]:  # Valid CBSE mark values
                    return marks
        return None
    
    def extract_chapter(self, query: str) -> Optional[str]:
        """Extract chapter reference from query."""
        # Look for "chapter X" or "ch. X" patterns
        match = re.search(r"chapter\s*(\d+|[a-z]+)", query, re.IGNORECASE)
        if match:
            return match.group(1)
        return None
    
    def process(self, query: str) -> Dict[str, Any]:
        """
        Process query and extract all metadata.
        
        Args:
            query: Raw student query
            
        Returns:
            Dict with extracted metadata
        """
        return {
            "subject": self.extract_subject(query),
            "marks": self.extract_marks(query),
            "chapter": self.extract_chapter(query),
            "cleaned_query": self._clean_query(query)
        }
    
    def _clean_query(self, query: str) -> str:
        """Remove marks/metadata references for cleaner embedding."""
        # Remove "for X marks" type phrases
        cleaned = re.sub(r"for\s*\d+\s*marks?", "", query, flags=re.IGNORECASE)
        cleaned = re.sub(r"\(\d+\s*marks?\)", "", cleaned)
        return cleaned.strip()


class Retriever:
    """
    Retrieves relevant chunks for a query.
    
    Combines embedding search with metadata filtering.
    """
    
    def __init__(self, vector_store: Optional[FAISSVectorStore] = None):
        self.vector_store = vector_store or get_vector_store()
        self.query_processor = QueryProcessor()
    
    async def retrieve(
        self,
        query: str,
        subject: Optional[str] = None,
        marks: Optional[int] = None,
        chapter: Optional[str] = None,
        top_k: Optional[int] = None
    ) -> List[RetrievalResult]:
        """
        Retrieve relevant chunks for a query.
        
        Args:
            query: Student's question
            subject: Subject filter (auto-detected if None)
            marks: Marks filter (auto-detected if None)
            chapter: Chapter filter
            top_k: Number of results
            
        Returns:
            List[RetrievalResult]: Ranked results with chunks
        """
        # Process query
        extracted = self.query_processor.process(query)
        
        # Use provided values or fall back to extracted
        subject = subject or extracted["subject"]
        marks = marks or extracted["marks"] or 3  # Default to 3 marks
        
        # Build filters
        filters = {"class_level": 9}  # Always filter to Class 9
        if subject:
            filters["subject"] = subject
        if marks:
            # For marks filtering, we check if the chunk is relevant for this mark value
            # This is handled specially in the search
            pass
        
        logger.info(f"Retrieving for query: '{query[:50]}...' with filters: {filters}")
        
        # Generate query embedding
        query_embedding = await embed_query(extracted["cleaned_query"])
        
        # Search vector store
        results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k or settings.retrieval_top_k,
            filters=filters
        )
        
        # Sort results by type priority
        results = self._prioritize_results(results, marks)
        
        logger.info(f"Retrieved {len(results)} chunks")
        return results
    
    def _prioritize_results(
        self,
        results: List[RetrievalResult],
        marks: int
    ) -> List[RetrievalResult]:
        """
        Prioritize results based on chunk type and marks relevance.
        
        Order:
        1. NCERT definitions (always first)
        2. Board-style answers matching mark value
        3. Marking scheme bullets
        4. Concepts and examples
        """
        def priority_key(result: RetrievalResult):
            chunk_type = result.chunk.metadata.chunk_type.value
            type_priority = {
                "definition": 0,
                "answer": 1,
                "marking_scheme": 2,
                "concept": 3,
                "example": 4,
                "formula": 5
            }
            
            # Check if marks is in relevance list
            marks_match = marks in result.chunk.metadata.marks_relevance
            
            return (
                0 if marks_match else 1,  # Marks match first
                type_priority.get(chunk_type, 10),  # Then by type
                -result.score  # Then by similarity
            )
        
        return sorted(results, key=priority_key)


# Singleton instance
_retriever: Optional[Retriever] = None


def get_retriever() -> Retriever:
    """Get or create the retriever instance."""
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever


async def retrieve_context(
    query: str,
    subject: Optional[str] = None,
    limit: Optional[int] = None
) -> List[RetrievalResult]:
    """
    Convenience wrapper for retrieval.
    
    Args:
        query: Student's question
        subject: Subject filter
        limit: Max results
        
    Returns:
        List[RetrievalResult]: Ranked results
    """
    retriever = get_retriever()
    return await retriever.retrieve(query=query, subject=subject, top_k=limit)
