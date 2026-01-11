"""
Pydantic Schemas

Data models used across the application.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from enum import Enum
from datetime import datetime
import uuid


class ChunkType(str, Enum):
    """Types of content chunks."""
    DEFINITION = "definition"
    CONCEPT = "concept"
    ANSWER = "answer"
    MARKING_SCHEME = "marking_scheme"
    EXAMPLE = "example"
    FORMULA = "formula"


class SourceType(str, Enum):
    """Source document types."""
    NCERT_TEXTBOOK = "ncert_textbook"
    NCERT_EXEMPLAR = "ncert_exemplar"
    SAMPLE_PAPER = "sample_paper"
    PREVIOUS_YEAR = "previous_year"
    MARKING_SCHEME = "marking_scheme"


class ChunkMetadata(BaseModel):
    """Metadata associated with each chunk."""
    
    class_level: int = Field(9, ge=7, le=12, alias="class")
    subject: str = Field(..., description="Subject name")
    chapter: str = Field(..., description="Chapter name")
    chapter_number: Optional[int] = Field(None, description="Chapter number")
    topic: str = Field(..., description="Specific topic")
    chunk_type: ChunkType = Field(..., description="Type of content")
    source_type: SourceType = Field(..., description="Source document type")
    marks_relevance: List[int] = Field(
        default_factory=lambda: [1, 2, 3, 5],
        description="Mark values this chunk is relevant for"
    )
    page_number: Optional[int] = Field(None, description="Source page number")
    
    class Config:
        populate_by_name = True


class Chunk(BaseModel):
    """A processed content chunk ready for embedding."""
    
    chunk_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str = Field(..., min_length=10, description="Chunk text content")
    metadata: ChunkMetadata = Field(..., description="Chunk metadata")
    token_count: int = Field(..., ge=1, description="Token count")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ParsedPage(BaseModel):
    """A parsed PDF page."""
    
    source_file: str = Field(..., description="Source PDF filename")
    page_number: int = Field(..., ge=1, description="Page number")
    chapter: Optional[str] = Field(None, description="Detected chapter")
    raw_text: str = Field(..., description="Raw extracted text")
    elements: List[dict] = Field(
        default_factory=list,
        description="Structured elements (headings, paragraphs, etc.)"
    )


class EmbeddingResult(BaseModel):
    """Result of embedding generation."""
    
    chunk_id: str = Field(..., description="Associated chunk ID")
    embedding: List[float] = Field(..., description="Embedding vector")
    model: str = Field(..., description="Model used for embedding")
    dimensions: int = Field(..., description="Vector dimensions")


class RetrievalResult(BaseModel):
    """Result from vector similarity search."""
    
    chunk: Chunk = Field(..., description="Retrieved chunk")
    score: float = Field(..., ge=0, le=1, description="Similarity score")
    rank: int = Field(..., ge=1, description="Result rank")


class GenerationContext(BaseModel):
    """Context assembled for LLM generation."""
    
    question: str = Field(..., description="Original question")
    subject: str = Field(..., description="Subject")
    marks: int = Field(..., description="Target marks")
    chunks: List[RetrievalResult] = Field(..., description="Retrieved chunks")
    system_prompt: str = Field(..., description="System prompt for LLM")


class TuningExample(BaseModel):
    """A single tuning example for Gemini fine-tuning."""
    
    text_input: str = Field(..., description="Input question with context")
    output: str = Field(..., description="Expected CBSE-style answer")
    subject: Optional[str] = Field(None, description="Subject for categorization")
    marks: Optional[int] = Field(None, description="Mark value")
