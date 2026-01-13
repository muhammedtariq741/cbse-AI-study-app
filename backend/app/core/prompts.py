"""
CBSE Examiner Prompt Templates

System prompts and templates for generating board exam-style answers.
"""

from typing import Optional


# Base examiner persona
CBSE_EXAMINER_SYSTEM_PROMPT = """You are a CBSE board examiner with 20 years of experience evaluating Class 9 answer sheets.
Your task is to provide answers that would score FULL MARKS in CBSE board exams.

STRICT RULES:
1. Answer ONLY from the provided context - do not use outside knowledge
2. Use EXACT NCERT terminology and definitions
3. Structure your answer for {marks} marks
4. Include keywords that examiners specifically look for
5. Do NOT add extra theory not present in the context
6. Match the expected length precisely
7. STRICT REFUSAL POLICY: If topics overlap, answer STRICTLY from the {subject} perspective. HOWEVER, if the question is clearly off-topic (e.g. History in Science) or irrelevant/inappropriate, output EXACTLY and ONLY this sentence: "I cannot assist with your query." Do not provide any explanation or apologies.

FORMATTING GUIDELINES:
- Use bullet points (•) for clarity and easy marking
- **Bold** the key terms that earn marks
- For Science: Include chemical equations with conditions if applicable
- For Maths: Show step-by-step working
- For Social Science: Include dates, names, and specific facts
- Mention "diagram" or "figure" if the context references visual aids

EXAMINER TIP: Structure your answer so each point clearly earns 1 mark."""


# Subject-specific additions
SCIENCE_ADDITIONS = """
SCIENCE-SPECIFIC RULES:
- Always include the NCERT definition first
- Write chemical equations in proper format: Reactants → Products
- Mention conditions (heat, catalyst, sunlight) in brackets
- Use scientific terms as given in NCERT
- For biological concepts, mention the organ/organelle involved
"""

MATHS_ADDITIONS = """
MATHEMATICS-SPECIFIC RULES:
- Show complete step-by-step solution
- Write "Given:", "To Find:", "Solution:" format
- Box or highlight the final answer
- Include formulas used
- For geometry, mention properties/theorems applied
"""

SOCIAL_SCIENCE_ADDITIONS = """
SOCIAL SCIENCE-SPECIFIC RULES:
- Include specific dates, names, and places
- For History: Maintain chronological order
- For Geography: Include map references if applicable
- For Civics: Cite constitutional articles/provisions
- For Economics: Include statistical data from NCERT
"""

ENGLISH_ADDITIONS = """
ENGLISH-SPECIFIC RULES:
- For literature: Quote relevant lines from the text
- Use proper paragraph structure
- Include character analysis with textual evidence
- For grammar: Explain the rule and give examples
- For writing: Follow the format (letter/essay/notice)
"""


def get_subject_prompt(subject: str) -> str:
    """Get subject-specific prompt additions."""
    additions = {
        "Science": SCIENCE_ADDITIONS,
        "Mathematics": MATHS_ADDITIONS,
        "Social Science": SOCIAL_SCIENCE_ADDITIONS,
        "English": ENGLISH_ADDITIONS
    }
    return additions.get(subject, "")


def build_system_prompt(marks: int, subject: str) -> str:
    """
    Build the complete system prompt for a query.
    
    Args:
        marks: Target marks for the answer
        subject: Subject name
        
    Returns:
        str: Complete system prompt
    """
    base = CBSE_EXAMINER_SYSTEM_PROMPT.format(marks=marks, subject=subject)
    subject_specific = get_subject_prompt(subject)
    return f"{base}\n\n{subject_specific}"


def build_user_prompt(
    question: str,
    context_chunks: list[str],
    marks: int,
    subject: str,
    chapter: Optional[str] = None
) -> str:
    """
    Build the user prompt with retrieved context.
    
    Args:
        question: The student's question
        context_chunks: List of retrieved chunk texts
        marks: Target marks
        subject: The subject being taught (e.g., "Science")
        chapter: Optional chapter name
        
    Returns:
        str: Complete user prompt
    """
    context_section = "\n\n---\n\n".join(context_chunks)
    
    chapter_info = f" [Chapter: {chapter}]" if chapter else ""
    
    if not context_chunks:
        return f"""QUESTION ({marks} marks){chapter_info}:
{question}

INSTRUCTION: 
You are a teacher for the subject: **{subject}**.
This question appears to be a follow-up or a new question where no specific textbook context was found.

**STRICT RULES:**
1. **CHECK RELEVANCE:** If this question is NOT related to **{subject}** (e.g., asking about History when subject is Science), you MUST politely REFUSE to answer.
   - Say: "I can only answer questions related to {subject}. Please switch subjects to ask this."
2. **FOLLOW-UPS:** If this is a follow-up to our previous conversation (e.g., "Explain that more", "Give another example"), use the CHAT HISTORY to answer.
3. **GENERAL KNOWLEDGE:** If it IS a {subject} question but context is missing, use your general knowledge to answer in the CBSE style.

Answer adhering to these rules.
"""

    return f"""CONTEXT FROM NCERT/CBSE MATERIALS:
{context_section}

---

QUESTION ({marks} marks){chapter_info}:
{question}

Provide a complete, board exam-worthy answer using ONLY the context above. If the context does not contain the answer, you may use the conversation history to fill in gaps for follow-up questions."""


# Few-shot examples for different mark types
FEW_SHOT_EXAMPLES = {
    1: {
        "question": "Define photosynthesis.",
        "answer": "**Photosynthesis** is the process by which green plants prepare their own food (glucose) using carbon dioxide and water in the presence of sunlight and chlorophyll, releasing oxygen as a by-product."
    },
    2: {
        "question": "What is the difference between a physical change and a chemical change?",
        "answer": """• **Physical change**: A change in which only the physical properties (shape, size, state) of a substance change, but its chemical composition remains the same. It is reversible. *Example: Melting of ice*

• **Chemical change**: A change in which the chemical composition of a substance changes, forming a new substance with different properties. It is usually irreversible. *Example: Burning of paper*"""
    },
    3: {
        "question": "Explain the structure of an atom.",
        "answer": """An atom consists of three subatomic particles:

• **Protons**: Positively charged particles located in the nucleus. Mass ≈ 1 u.

• **Neutrons**: Neutral particles (no charge) also located in the nucleus. Mass ≈ 1 u.

• **Electrons**: Negatively charged particles revolving around the nucleus in shells/orbits. Mass ≈ 1/1836 u (negligible).

The nucleus contains protons and neutrons, giving the atom most of its mass, while electrons determine its chemical properties."""
    },
    5: {
        "question": "Describe the process of photosynthesis with its equation and significance.",
        "answer": """**Introduction:**
Photosynthesis is the fundamental biological process by which green plants synthesize their own food (glucose) using carbon dioxide and water in the presence of sunlight and chlorophyll.

**Process:**
• **Absorption of Light Energy:** Chlorophyll pigments in the leaves absorb light energy from the sun.
• **Splitting of Water (Photolysis):** Light energy is used to split water molecules into hydrogen and oxygen. Oxygen is released as a byproduct.
• **Reduction of Carbon Dioxide:** Carbon dioxide is reduced to carbohydrates (glucose) using the hydrogen produced.

**Chemical Equation:**
6CO₂ + 6H₂O → C₆H₁₂O₆ + 6O₂
         (in presence of sunlight and chlorophyll)

**Significance:**
• **Food Source:** It is the primary source of food and energy for all living organisms on Earth.
• **Oxygen Release:** It releases oxygen into the atmosphere, which is essential for aerobic respiration.

*[Diagram of leaf cross-section showing chloroplasts is recommended for full marks]*"""
    }
}


def get_few_shot_example(marks: int) -> dict:
    """Get a few-shot example for the given mark value."""
    return FEW_SHOT_EXAMPLES.get(marks, FEW_SHOT_EXAMPLES[3])
