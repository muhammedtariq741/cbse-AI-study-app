"""
Gemini Model Tuning Module

Handles the creation and management of tuned Gemini models for CBSE-style responses.
"""

from google import genai
from google.genai import types
from typing import List, Optional, Dict, Any
from pathlib import Path
import json
import logging
from datetime import datetime

from app.config import settings
from app.models.schemas import TuningExample

logger = logging.getLogger(__name__)


class GeminiTuner:
    """
    Manages Gemini model tuning for CBSE-specific response style.
    
    Tuning teaches the model HOW to format, not WHAT to answer.
    Knowledge comes from RAG, style comes from tuning.
    """
    
    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.tuning_data_dir = Path("./data/tuning")
        self.tuning_data_dir.mkdir(parents=True, exist_ok=True)
    
    def prepare_tuning_dataset(
        self,
        examples: List[TuningExample],
        output_file: str,
        subject: Optional[str] = None
    ) -> Path:
        """
        Prepare a tuning dataset file.
        
        Args:
            examples: List of tuning examples
            output_file: Output filename
            subject: Optional subject for filtering
            
        Returns:
            Path: Path to the created dataset file
        """
        output_path = self.tuning_data_dir / output_file
        
        # Format for Gemini tuning
        tuning_data = []
        for example in examples:
            tuning_data.append({
                "text_input": example.text_input,
                "output": example.output
            })
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(tuning_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Created tuning dataset with {len(tuning_data)} examples at {output_path}")
        return output_path
    
    def load_tuning_examples(self, file_path: str) -> List[TuningExample]:
        """Load tuning examples from a JSON file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        examples = []
        for item in data:
            examples.append(TuningExample(
                text_input=item["text_input"],
                output=item["output"],
                subject=item.get("subject"),
                marks=item.get("marks")
            ))
        
        return examples
    
    async def create_tuned_model(
        self,
        training_data_path: str,
        model_display_name: str,
        epochs: int = 5,
        batch_size: int = 4,
        learning_rate: float = 0.001
    ) -> Dict[str, Any]:
        """
        Create a tuned model using Gemini's tuning API.
        
        Note: This requires Vertex AI setup for production.
        For development, we use the AI Studio tuning.
        
        Args:
            training_data_path: Path to the training data JSON
            model_display_name: Display name for the tuned model
            epochs: Number of training epochs
            batch_size: Training batch size
            learning_rate: Learning rate
            
        Returns:
            Dict with tuning job information
        """
        logger.info(f"Starting tuning job: {model_display_name}")
        
        # Load training data
        with open(training_data_path, "r", encoding="utf-8") as f:
            training_data = json.load(f)
        
        # Create tuning job
        # Note: The actual API call depends on whether using AI Studio or Vertex AI
        try:
            tuning_job = self.client.tunings.create(
                base_model="models/gemini-2.0-flash",
                training_dataset=types.TuningDataset(
                    examples=[
                        types.TuningExample(
                            text_input=ex["text_input"],
                            output=ex["output"]
                        )
                        for ex in training_data
                    ]
                ),
                config=types.CreateTuningJobConfig(
                    epoch_count=epochs,
                    batch_size=batch_size,
                    learning_rate=learning_rate,
                    tuned_model_display_name=model_display_name
                )
            )
            
            logger.info(f"Tuning job created: {tuning_job.name}")
            
            return {
                "job_name": tuning_job.name,
                "status": "CREATED",
                "model_name": model_display_name,
                "created_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to create tuning job: {e}")
            raise
    
    def check_tuning_status(self, job_name: str) -> Dict[str, Any]:
        """Check the status of a tuning job."""
        try:
            job = self.client.tunings.get(name=job_name)
            return {
                "job_name": job.name,
                "status": job.state,
                "tuned_model": getattr(job, "tuned_model", None)
            }
        except Exception as e:
            logger.error(f"Failed to get tuning status: {e}")
            raise
    
    def list_tuned_models(self) -> List[Dict[str, Any]]:
        """List all tuned models."""
        try:
            models = self.client.tunings.list()
            return [
                {
                    "name": m.name,
                    "display_name": getattr(m, "display_name", ""),
                    "state": m.state,
                    "tuned_model": getattr(m, "tuned_model", None)
                }
                for m in models
            ]
        except Exception as e:
            logger.error(f"Failed to list tuned models: {e}")
            return []


def create_sample_tuning_data() -> List[TuningExample]:
    """
    Create sample tuning data for CBSE Class 9 Science.
    
    These examples teach the model the CBSE answer style.
    """
    examples = [
        # 1-mark definitions
        TuningExample(
            text_input="Define matter. (1 mark) [Class 9 Science]",
            output="**Matter** is anything that occupies space and has mass.",
            subject="Science",
            marks=1
        ),
        TuningExample(
            text_input="What is an atom? (1 mark) [Class 9 Science]",
            output="An **atom** is the smallest particle of an element that can take part in a chemical reaction and retains all the properties of that element.",
            subject="Science",
            marks=1
        ),
        
        # 2-mark questions
        TuningExample(
            text_input="Define photosynthesis and write its equation. (2 marks) [Class 9 Science]",
            output="""**Photosynthesis** is the process by which green plants prepare their food (glucose) using carbon dioxide and water in the presence of sunlight and chlorophyll.

**Chemical Equation:**
6CO₂ + 6H₂O → C₆H₁₂O₆ + 6O₂
         (sunlight, chlorophyll)""",
            subject="Science",
            marks=2
        ),
        TuningExample(
            text_input="Differentiate between elements and compounds. (2 marks) [Class 9 Science]",
            output="""| **Elements** | **Compounds** |
|--------------|---------------|
| Made up of only one type of atom | Made up of two or more types of atoms chemically combined |
| Cannot be broken down into simpler substances | Can be broken down into elements by chemical reactions |
| Example: Iron (Fe), Oxygen (O₂) | Example: Water (H₂O), Carbon dioxide (CO₂) |""",
            subject="Science",
            marks=2
        ),
        
        # 3-mark questions
        TuningExample(
            text_input="State and explain the law of conservation of mass. (3 marks) [Class 9 Science]",
            output="""**Law of Conservation of Mass** (Lavoisier's Law):

**Statement:** Mass can neither be created nor destroyed in a chemical reaction. The total mass of reactants equals the total mass of products.

**Explanation:**
• In any chemical reaction, atoms are neither created nor destroyed
• They are only rearranged to form new substances
• Therefore, the total mass remains constant

**Example:**
Zn + H₂SO₄ → ZnSO₄ + H₂↑
65g + 98g = 161g + 2g
163g = 163g (Mass is conserved)""",
            subject="Science",
            marks=3
        ),
        TuningExample(
            text_input="Describe the structure of an animal cell with a diagram. (3 marks) [Class 9 Science]",
            output="""**Animal Cell Structure:**

An animal cell consists of:

• **Cell membrane (Plasma membrane)**: Outer covering that controls movement of substances in and out of the cell

• **Cytoplasm**: Jelly-like substance containing cell organelles

• **Nucleus**: Control center containing genetic material (DNA); bounded by nuclear membrane

• **Mitochondria**: Powerhouse of the cell; produces energy (ATP) through respiration

• **Endoplasmic Reticulum**: Network for protein and lipid synthesis

• **Golgi apparatus**: Packages and secretes proteins

*[Diagram showing labelled animal cell should be drawn]*""",
            subject="Science",
            marks=3
        ),
        
        # 5-mark questions
        TuningExample(
            text_input="Explain the process of respiration in plants with its types and importance. (5 marks) [Class 9 Science]",
            output="""**Respiration in Plants:**

**Definition:** Respiration is the biochemical process by which organisms break down glucose to release energy in the form of ATP.

**Chemical Equation:**
C₆H₁₂O₆ + 6O₂ → 6CO₂ + 6H₂O + Energy (ATP)

**Types of Respiration:**

**1. Aerobic Respiration:**
• Occurs in presence of oxygen
• Takes place in mitochondria
• Complete breakdown of glucose
• Produces 36-38 ATP molecules
• Products: CO₂ and H₂O

**2. Anaerobic Respiration:**
• Occurs in absence of oxygen
• Takes place in cytoplasm
• Incomplete breakdown of glucose
• Produces only 2 ATP molecules
• Products: Ethanol + CO₂ (in plants) or Lactic acid (in muscles)

**Importance of Respiration:**
• Provides energy for all life processes
• Essential for growth and repair
• Maintains body temperature in organisms
• Produces CO₂ used in photosynthesis

**Key Difference from Photosynthesis:**
Respiration releases energy; Photosynthesis stores energy.""",
            subject="Science",
            marks=5
        ),
        
        # Maths examples
        TuningExample(
            text_input="Factorise: x² + 5x + 6 (2 marks) [Class 9 Mathematics]",
            output="""**Solution:**

x² + 5x + 6

**Step 1:** Find two numbers whose product = 6 and sum = 5
• Numbers are 2 and 3 (2 × 3 = 6, 2 + 3 = 5)

**Step 2:** Split the middle term
= x² + 2x + 3x + 6

**Step 3:** Group and factorise
= x(x + 2) + 3(x + 2)
= **(x + 2)(x + 3)**""",
            subject="Mathematics",
            marks=2
        ),
        
        # Social Science example
        TuningExample(
            text_input="What were the main causes of the French Revolution? (3 marks) [Class 9 Social Science]",
            output="""**Causes of the French Revolution (1789):**

**1. Social Inequality:**
• French society divided into three estates
• Third Estate (commoners) comprised 97% population but had no privileges
• First Estate (clergy) and Second Estate (nobles) were exempted from taxes

**2. Economic Crisis:**
• France was bankrupt due to wars and extravagant spending by Louis XVI
• Heavy taxes burdened the common people
• Bread prices skyrocketed due to bad harvests

**3. Inspiration from Philosophers:**
• Ideas of Rousseau (Social Contract), Voltaire (freedom of speech), and Montesquieu (separation of powers)
• American Revolution inspired French citizens

**Immediate Cause:** Calling of Estates-General in May 1789 and the formation of National Assembly by the Third Estate.""",
            subject="Social Science",
            marks=3
        ),
    ]
    
    return examples


async def create_cbse_tuning_dataset():
    """Create and save the CBSE tuning dataset."""
    tuner = GeminiTuner()
    
    # Get sample data
    examples = create_sample_tuning_data()
    
    # Save to file
    output_file = tuner.prepare_tuning_dataset(
        examples=examples,
        output_file="cbse_class9_tuning.json"
    )
    
    logger.info(f"Created tuning dataset at: {output_file}")
    return output_file
