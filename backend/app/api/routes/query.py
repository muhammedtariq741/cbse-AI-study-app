"""
Query Endpoint

Main endpoint for student questions. Orchestrates the full RAG pipeline:
1. Query processing (extract metadata)
2. Retrieval (fetch relevant chunks)
3. Prompt assembly (build examiner-style prompt)
4. LLM call (generate answer)
5. Response formatting (board-style output)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class Subject(str, Enum):
    """CBSE Class 9 subjects."""
    SCIENCE = "Science"
    MATHS = "Mathematics"
    SOCIAL_SCIENCE = "Social Science"
    ENGLISH = "English"


class ChatMessage(BaseModel):
    """A single message in the chat history."""
    role: str = Field(..., description="Role: 'user' or 'model'")
    content: str = Field(..., description="Message content")


class QueryRequest(BaseModel):
    """Request model for student queries."""
    
    question: str = Field(
        ...,
        min_length=1,  # Allow shorter follow-ups
        max_length=500,
        description="The student's question",
        examples=["Explain this further"]
    )
    subject: Optional[Subject] = Field(
        None,
        description="Subject (auto-detected if not provided)"
    )
    marks: Optional[int] = Field(
        None,
        ge=1,
        le=5,
        description="Expected marks (1, 2, 3, or 5)"
    )
    chapter: Optional[str] = Field(
        None,
        description="Specific chapter to focus on"
    )
    history: List[ChatMessage] = Field(
        default_factory=list,
        description="Previous chat messages for context"
    )


class SourceChunk(BaseModel):
    """A source chunk used to generate the answer."""
    
    text: str = Field(..., description="Chunk text content")
    chapter: str = Field(..., description="Source chapter")
    topic: str = Field(..., description="Topic within chapter")
    source_type: str = Field(..., description="ncert/sample_paper/marking_scheme")
    relevance_score: float = Field(..., description="Similarity score")


class QueryResponse(BaseModel):
    """Response model for student queries."""
    
    answer: str = Field(..., description="The generated answer")
    marks: int = Field(..., description="Answer formatted for these marks")
    subject: str = Field(..., description="Detected/provided subject")
    chapter: Optional[str] = Field(None, description="Related chapter")
    sources: List[SourceChunk] = Field(
        default_factory=list,
        description="Source chunks used for answer"
    )
    keywords: List[str] = Field(
        default_factory=list,
        description="Key terms in the answer (for exam prep)"
    )


from app.core.retriever import retrieve_context
from app.core.llm import generate_answer
from app.models.schemas import Chunk



@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a student's question and return a CBSE-style answer.
    """
    logger.info(f"Processing query: {request.question[:50]}... (History: {len(request.history)} msgs)")
    
    # Step 1: Query Processing
    detected_subject = request.subject or Subject.SCIENCE
    detected_marks = request.marks or 3
    
    # Auto-upgrade marks for elaboration requests to ensure detailed answers and more context
    if any(keyword in request.question.lower() for keyword in ["elaborate", "explain", "detail", "more", "expand"]):
        logger.info("Upgrading marks to 5 for elaboration request")
        detected_marks = 5
    
    # Step 2: Retrieval
    # Search for relevant content in vector store
    search_query = request.question
    
    # Improve context for short follow-up questions
    if request.history and len(request.question.split()) < 7:
        # Get last 2 user messages to ensure we capture the original topic
        # even if the immediate previous message was also a follow-up
        user_msgs = [m.content for m in request.history if m.role == 'user']
        if user_msgs:
             context_str = " ".join(user_msgs[-2:]) # Last 2 messages
             logger.info(f"Augmenting query with history: {context_str[:50]}...")
             search_query = f"{context_str} {request.question}"

    retrieved_results = await retrieve_context(
        query=search_query,
        subject=detected_subject.value,
        limit=5 if detected_marks <= 3 else 8  # More context for long answers
    )
    
    # Filter results by relevance score (Cosine Similarity)
    # Lowered to 0.42 for Social Science flexibility
    RELEVANCE_THRESHOLD = 0.42

    retrieved_results = [r for r in retrieved_results if r.score >= RELEVANCE_THRESHOLD]
    
    # Extract text content for the LLM
    context_chunks = [result.chunk.text for result in retrieved_results]
    
    # Step 3 & 4: Prompt Assembly & LLM Generation
    # Note: Even if no NEW context is found, we might still want to answer if it's a follow-up 
    # (chat history + logic). But for now let's keep the hard stop lenient.
    
    answer_text = await generate_answer(
        question=request.question,
        context_chunks=context_chunks,
        marks=detected_marks,
        subject=detected_subject.value,
        chapter=request.chapter,
        history=[{"role": m.role, "content": m.content} for m in request.history]
    )
    
    # Step 5: Response Formatting
    # Map retrieved chunks to response source format
    sources = []
    for result in retrieved_results:
        # Avoid duplicates
        if any(s.text == result.chunk.text for s in sources):
            continue
            
        sources.append(SourceChunk(
            text=result.chunk.text[:200] + "...",  # Preview only
            chapter=result.chunk.metadata.chapter or "Unknown",
            topic=result.chunk.metadata.topic or "General",
            source_type=result.chunk.metadata.source_type.value,
            relevance_score=result.score
        ))
    
    # Extract keywords (simple heuristic for now, LLM can also do this)
    # Ideally, we ask the LLM to output JSON with keywords, but for now we extract from bold text
    import re
    keywords = re.findall(r"\*\*(.*?)\*\*", answer_text)
    
    return QueryResponse(
        answer=answer_text,
        marks=detected_marks,
        subject=detected_subject.value,
        chapter=request.chapter,
        sources=sources[:3],  # Return top 3 sources
        keywords=keywords[:5]  # Top 5 keywords
    )


@router.get("/subjects")
async def list_subjects():
    """
    List available subjects.
    
    Returns:
        dict: List of available subjects for Class 9
    """
    return {
        "class": 9,
        "subjects": [
            {"id": "science", "name": "Science", "chapters": 15},
            {"id": "maths", "name": "Mathematics", "chapters": 15},
            {"id": "social_science", "name": "Social Science", "chapters": 20},
            {"id": "english", "name": "English", "chapters": 10},
        ]
    }
