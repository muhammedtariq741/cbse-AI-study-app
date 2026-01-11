"""
LLM Integration Module

Handles interaction with Google Gemini for answer generation.
"""

from google import genai
from google.genai import types
from typing import Optional, List
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.core.prompts import build_system_prompt, build_user_prompt, get_few_shot_example

logger = logging.getLogger(__name__)

# Client instance
_client: Optional[genai.Client] = None


def get_client() -> genai.Client:
    """Get or create the Gemini client."""
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def get_model_name() -> str:
    """
    Get the model name to use.
    
    Returns tuned model if configured, otherwise base model.
    """
    if settings.tuned_model_name:
        return settings.tuned_model_name
    return settings.llm_model


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def generate_answer(
    question: str,
    context_chunks: List[str],
    marks: int,
    subject: str,
    chapter: Optional[str] = None,
    use_few_shot: bool = True
) -> str:
    """
    Generate a CBSE-style answer using Gemini.
    
    Args:
        question: The student's question
        context_chunks: Retrieved context from vector store
        marks: Target marks (1, 2, 3, or 5)
        subject: Subject name
        chapter: Optional chapter name
        use_few_shot: Whether to include few-shot example
        
    Returns:
        str: Generated answer in CBSE board exam style
    """
    client = get_client()
    model = get_model_name()
    
    # Build prompts
    system_prompt = build_system_prompt(marks, subject)
    user_prompt = build_user_prompt(question, context_chunks, marks, chapter)
    
    # Optionally add few-shot example
    messages = []
    if use_few_shot:
        example = get_few_shot_example(marks)
        messages.append({
            "role": "user",
            "parts": [{"text": f"EXAMPLE QUESTION ({marks} mark): {example['question']}"}]
        })
        messages.append({
            "role": "model", 
            "parts": [{"text": example['answer']}]
        })
    
    # Add the actual question
    messages.append({
        "role": "user",
        "parts": [{"text": user_prompt}]
    })
    
    logger.info(f"Generating answer with {model} for {marks}-mark question")
    
    # Generate response
    response = client.models.generate_content(
        model=model,
        contents=messages,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.3,  # Low temperature for consistent, factual answers
            top_p=0.9,
            max_output_tokens=1024,
        )
    )
    
    return response.text


async def generate_answer_stream(
    question: str,
    context_chunks: List[str],
    marks: int,
    subject: str,
    chapter: Optional[str] = None
):
    """
    Generate answer with streaming for real-time display.
    
    Yields chunks of the answer as they're generated.
    """
    client = get_client()
    model = get_model_name()
    
    system_prompt = build_system_prompt(marks, subject)
    user_prompt = build_user_prompt(question, context_chunks, marks, chapter)
    
    response = client.models.generate_content_stream(
        model=model,
        contents=[{"role": "user", "parts": [{"text": user_prompt}]}],
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.3,
            top_p=0.9,
            max_output_tokens=1024,
        )
    )
    
    for chunk in response:
        if chunk.text:
            yield chunk.text


async def test_connection() -> bool:
    """
    Test the Gemini API connection.
    
    Returns:
        bool: True if connection successful
    """
    try:
        client = get_client()
        response = client.models.generate_content(
            model=settings.llm_model,
            contents="Say 'Connection successful' in exactly those words."
        )
        return "successful" in response.text.lower()
    except Exception as e:
        logger.error(f"Gemini connection test failed: {e}")
        return False
