"""
Intelligent Chunking Module

Creates semantic chunks from parsed content.
CRITICAL: This is where CBSE accuracy begins.
"""

import tiktoken
from typing import List, Optional, Dict, Any
import re
import uuid
import logging
from datetime import datetime

from app.models.schemas import Chunk, ChunkMetadata, ParsedPage, ChunkType, SourceType
from app.config import settings

logger = logging.getLogger(__name__)


class IntelligentChunker:
    """
    Creates semantic chunks optimized for CBSE content.
    
    Key principles:
    1. One idea per chunk (semantic boundaries, not arbitrary splits)
    2. Preserve complete definitions
    3. Keep answer points together
    4. Maintain context overlap for retrieval quality
    """
    
    def __init__(
        self,
        target_size: int = None,
        overlap: int = None
    ):
        """
        Initialize chunker.
        
        Args:
            target_size: Target chunk size in tokens (300-500 recommended)
            overlap: Overlap between chunks in tokens
        """
        self.target_size = target_size or settings.chunk_size
        self.overlap = overlap or settings.chunk_overlap
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.tokenizer.encode(text))
    
    def chunk_pages(
        self,
        pages: List[ParsedPage],
        subject: str,
        source_type: SourceType = SourceType.NCERT_TEXTBOOK,
        class_level: int = 9
    ) -> List[Chunk]:
        """
        Chunk multiple parsed pages.
        
        Args:
            pages: List of parsed pages
            subject: Subject name
            source_type: Type of source document
            class_level: Class level
            
        Returns:
            List[Chunk]: All chunks from the pages
        """
        all_chunks = []
        current_chapter = None
        current_topic = None
        
        for page in pages:
            if page.chapter:
                current_chapter = page.chapter
            
            # Chunk based on element types
            for element in page.elements:
                chunks = self._chunk_element(
                    element=element,
                    chapter=current_chapter or "Unknown",
                    topic=current_topic or current_chapter or "General",
                    subject=subject,
                    source_type=source_type,
                    class_level=class_level,
                    page_number=page.page_number
                )
                all_chunks.extend(chunks)
                
                # Update topic if we found a heading
                if element.get("type") == "heading":
                    current_topic = element.get("text", "")[:100]
        
        logger.info(f"Created {len(all_chunks)} chunks from {len(pages)} pages")
        return all_chunks
    
    def _chunk_element(
        self,
        element: Dict[str, Any],
        chapter: str,
        topic: str,
        subject: str,
        source_type: SourceType,
        class_level: int,
        page_number: int
    ) -> List[Chunk]:
        """Chunk a single element based on its type."""
        element_type = element.get("type", "paragraph")
        
        if element_type == "definition":
            return self._chunk_definition(
                element, chapter, topic, subject, source_type, class_level, page_number
            )
        elif element_type == "list_item":
            return self._chunk_list_item(
                element, chapter, topic, subject, source_type, class_level, page_number
            )
        elif element_type == "heading":
            return []  # Headings are used for metadata, not chunked
        else:
            return self._chunk_paragraph(
                element, chapter, topic, subject, source_type, class_level, page_number
            )
    
    def _chunk_definition(
        self,
        element: Dict[str, Any],
        chapter: str,
        topic: str,
        subject: str,
        source_type: SourceType,
        class_level: int,
        page_number: int
    ) -> List[Chunk]:
        """
        Chunk a definition - keeps it as one chunk.
        
        Definitions are high-value for CBSE answers.
        """
        text = element.get("definition", "")
        term = element.get("term", "Unknown")
        
        if not text or self.count_tokens(text) < 10:
            return []
        
        # Use the term as topic if available
        chunk_topic = term if term != "Unknown" else topic
        
        metadata = ChunkMetadata(
            class_level=class_level,
            subject=subject,
            chapter=chapter,
            topic=chunk_topic,
            chunk_type=ChunkType.DEFINITION,
            source_type=source_type,
            marks_relevance=[1, 2, 3, 5],  # Definitions useful for all marks
            page_number=page_number
        )
        
        chunk = Chunk(
            chunk_id=str(uuid.uuid4()),
            text=f"{term}: {text}" if term != "Unknown" else text,
            metadata=metadata,
            token_count=self.count_tokens(text),
            created_at=datetime.utcnow()
        )
        
        return [chunk]
    
    def _chunk_paragraph(
        self,
        element: Dict[str, Any],
        chapter: str,
        topic: str,
        subject: str,
        source_type: SourceType,
        class_level: int,
        page_number: int
    ) -> List[Chunk]:
        """
        Chunk a paragraph with semantic awareness.
        
        Splits at sentence boundaries, not mid-sentence.
        """
        text = element.get("text", "")
        
        if not text or self.count_tokens(text) < 20:
            return []
        
        chunks = []
        
        # If within target size, keep as one chunk
        if self.count_tokens(text) <= self.target_size:
            metadata = ChunkMetadata(
                class_level=class_level,
                subject=subject,
                chapter=chapter,
                topic=topic,
                chunk_type=ChunkType.CONCEPT,
                source_type=source_type,
                marks_relevance=self._determine_marks_relevance(text),
                page_number=page_number
            )
            
            chunk = Chunk(
                chunk_id=str(uuid.uuid4()),
                text=text,
                metadata=metadata,
                token_count=self.count_tokens(text),
                created_at=datetime.utcnow()
            )
            chunks.append(chunk)
        else:
            # Split at sentence boundaries
            sentences = self._split_sentences(text)
            current_chunk_text = ""
            
            for sentence in sentences:
                potential_text = current_chunk_text + " " + sentence if current_chunk_text else sentence
                
                if self.count_tokens(potential_text) <= self.target_size:
                    current_chunk_text = potential_text
                else:
                    # Save current chunk if substantial
                    if current_chunk_text and self.count_tokens(current_chunk_text) >= 50:
                        metadata = ChunkMetadata(
                            class_level=class_level,
                            subject=subject,
                            chapter=chapter,
                            topic=topic,
                            chunk_type=ChunkType.CONCEPT,
                            source_type=source_type,
                            marks_relevance=self._determine_marks_relevance(current_chunk_text),
                            page_number=page_number
                        )
                        
                        chunk = Chunk(
                            chunk_id=str(uuid.uuid4()),
                            text=current_chunk_text.strip(),
                            metadata=metadata,
                            token_count=self.count_tokens(current_chunk_text),
                            created_at=datetime.utcnow()
                        )
                        chunks.append(chunk)
                    
                    # Start new chunk with overlap
                    overlap_text = self._get_overlap(current_chunk_text)
                    current_chunk_text = overlap_text + " " + sentence if overlap_text else sentence
            
            # Don't forget the last chunk
            if current_chunk_text and self.count_tokens(current_chunk_text) >= 50:
                metadata = ChunkMetadata(
                    class_level=class_level,
                    subject=subject,
                    chapter=chapter,
                    topic=topic,
                    chunk_type=ChunkType.CONCEPT,
                    source_type=source_type,
                    marks_relevance=self._determine_marks_relevance(current_chunk_text),
                    page_number=page_number
                )
                
                chunk = Chunk(
                    chunk_id=str(uuid.uuid4()),
                    text=current_chunk_text.strip(),
                    metadata=metadata,
                    token_count=self.count_tokens(current_chunk_text),
                    created_at=datetime.utcnow()
                )
                chunks.append(chunk)
        
        return chunks
    
    def _chunk_list_item(
        self,
        element: Dict[str, Any],
        chapter: str,
        topic: str,
        subject: str,
        source_type: SourceType,
        class_level: int,
        page_number: int
    ) -> List[Chunk]:
        """Chunk a list item - typically kept as single chunk."""
        text = element.get("text", "")
        
        if not text or self.count_tokens(text) < 10:
            return []
        
        metadata = ChunkMetadata(
            class_level=class_level,
            subject=subject,
            chapter=chapter,
            topic=topic,
            chunk_type=ChunkType.ANSWER,  # List items often form answer points
            source_type=source_type,
            marks_relevance=[1, 2, 3],  # Good for short answers
            page_number=page_number
        )
        
        chunk = Chunk(
            chunk_id=str(uuid.uuid4()),
            text=f"• {text}",
            metadata=metadata,
            token_count=self.count_tokens(text),
            created_at=datetime.utcnow()
        )
        
        return [chunk]
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Handle common abbreviations
        text = re.sub(r"([A-Z])\.", r"\1_DOT_", text)  # Abbreviations
        text = re.sub(r"(\d)\.", r"\1_DOT_", text)  # Numbers with periods
        
        # Split on sentence boundaries
        sentences = re.split(r"(?<=[.!?])\s+", text)
        
        # Restore dots
        sentences = [s.replace("_DOT_", ".") for s in sentences]
        
        return [s.strip() for s in sentences if s.strip()]
    
    def _get_overlap(self, text: str) -> str:
        """Get the last few tokens for overlap."""
        if not text:
            return ""
        
        sentences = self._split_sentences(text)
        if not sentences:
            return ""
        
        # Take last 1-2 sentences as overlap
        overlap_sentences = sentences[-2:] if len(sentences) >= 2 else sentences
        overlap = " ".join(overlap_sentences)
        
        # Ensure it's not too long
        while self.count_tokens(overlap) > self.overlap and overlap_sentences:
            overlap_sentences = overlap_sentences[1:]
            overlap = " ".join(overlap_sentences)
        
        return overlap
    
    def _determine_marks_relevance(self, text: str) -> List[int]:
        """Determine which mark values this chunk is relevant for."""
        token_count = self.count_tokens(text)
        
        if token_count < 50:
            return [1, 2]  # Short answers
        elif token_count < 150:
            return [2, 3]  # Medium answers
        elif token_count < 300:
            return [3, 5]  # Detailed answers
        else:
            return [5]  # Long form only


def chunk_text_simple(
    text: str,
    subject: str,
    chapter: str,
    topic: str,
    chunk_type: ChunkType = ChunkType.CONCEPT,
    source_type: SourceType = SourceType.NCERT_TEXTBOOK,
    class_level: int = 9
) -> List[Chunk]:
    """
    Simple text chunking utility.
    
    Use this for quick chunking of plain text without PDF parsing.
    """
    chunker = IntelligentChunker()
    
    element = {"type": "paragraph", "text": text}
    
    return chunker._chunk_paragraph(
        element=element,
        chapter=chapter,
        topic=topic,
        subject=subject,
        source_type=source_type,
        class_level=class_level,
        page_number=0
    )
