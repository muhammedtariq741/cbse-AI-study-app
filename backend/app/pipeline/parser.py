"""
PDF Parser Module

Extracts structured text from NCERT and CBSE PDFs.
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Optional, Dict, Any
import re
import logging

from app.models.schemas import ParsedPage

logger = logging.getLogger(__name__)


class PDFParser:
    """
    Parses NCERT/CBSE PDFs with structure preservation.
    
    Handles:
    - Multi-column layouts
    - Headers and footers removal
    - Chapter/topic detection
    - Definition extraction
    """
    
    def __init__(self):
        # Patterns for NCERT structure
        self.chapter_patterns = [
            r"^CHAPTER\s*(\d+)",
            r"^Chapter\s*(\d+)",
            r"^(\d+)\.\s+[A-Z]",
        ]
        self.heading_patterns = [
            r"^(\d+\.\d+)\s+",  # 1.1, 2.3 format
            r"^[A-Z][A-Z\s]+$",  # ALL CAPS headings
        ]
        self.definition_pattern = r"(?:is defined as|is called|refers to|means|is the)"
    
    def parse_pdf(
        self,
        pdf_path: str,
        subject: str,
        class_level: int = 9
    ) -> List[ParsedPage]:
        """
        Parse a PDF file and extract structured content.
        
        Args:
            pdf_path: Path to the PDF file
            subject: Subject name (Science, Maths, etc.)
            class_level: Class level (default 9)
            
        Returns:
            List[ParsedPage]: Parsed pages with structured content
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        logger.info(f"Parsing PDF: {pdf_path.name}")
        
        doc = fitz.open(pdf_path)
        parsed_pages = []
        current_chapter = None
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Extract text with layout preservation
            text = page.get_text("text")
            
            # Clean the text
            text = self._clean_text(text)
            
            if not text.strip():
                continue
            
            # Detect chapter changes
            detected_chapter = self._detect_chapter(text)
            if detected_chapter:
                current_chapter = detected_chapter
            
            # Extract structural elements
            elements = self._extract_elements(text)
            
            parsed_page = ParsedPage(
                source_file=pdf_path.name,
                page_number=page_num + 1,
                chapter=current_chapter,
                raw_text=text,
                elements=elements
            )
            
            parsed_pages.append(parsed_page)
        
        doc.close()
        logger.info(f"Parsed {len(parsed_pages)} pages from {pdf_path.name}")
        
        return parsed_pages
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text."""
        # Remove page numbers
        text = re.sub(r"^\d+\s*$", "", text, flags=re.MULTILINE)
        
        # Remove excessive whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)
        
        # Remove header/footer patterns (customize based on NCERT format)
        text = re.sub(r"NCERT not to be republished", "", text, flags=re.IGNORECASE)
        text = re.sub(r"©\s*NCERT.*", "", text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def _detect_chapter(self, text: str) -> Optional[str]:
        """Detect chapter title from page text."""
        lines = text.split("\n")[:10]  # Check first 10 lines
        
        for line in lines:
            line = line.strip()
            for pattern in self.chapter_patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    # Extract full chapter title
                    return line
        
        return None
    
    def _extract_elements(self, text: str) -> List[Dict[str, Any]]:
        """Extract structural elements from text."""
        elements = []
        lines = text.split("\n")
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                i += 1
                continue
            
            # Check for heading
            if self._is_heading(line):
                elements.append({
                    "type": "heading",
                    "text": line,
                    "level": self._get_heading_level(line)
                })
                i += 1
                continue
            
            # Check for definition
            if re.search(self.definition_pattern, line, re.IGNORECASE):
                # Collect the full definition (may span multiple lines)
                definition_text = line
                i += 1
                while i < len(lines) and lines[i].strip() and not self._is_heading(lines[i]):
                    definition_text += " " + lines[i].strip()
                    i += 1
                    if "." in lines[i-1]:  # End at sentence boundary
                        break
                
                # Extract term being defined
                term = self._extract_defined_term(definition_text)
                elements.append({
                    "type": "definition",
                    "term": term,
                    "definition": definition_text
                })
                continue
            
            # Check for list items
            if re.match(r"^[\•\-\*\d\)]\s*", line):
                elements.append({
                    "type": "list_item",
                    "text": re.sub(r"^[\•\-\*\d\)]\s*", "", line)
                })
                i += 1
                continue
            
            # Default: paragraph
            para_text = line
            i += 1
            while i < len(lines) and lines[i].strip() and not self._is_heading(lines[i]):
                if re.match(r"^[\•\-\*\d\)]\s*", lines[i]):
                    break
                para_text += " " + lines[i].strip()
                i += 1
            
            if len(para_text) > 50:  # Only include substantial paragraphs
                elements.append({
                    "type": "paragraph",
                    "text": para_text
                })
        
        return elements
    
    def _is_heading(self, line: str) -> bool:
        """Check if a line is a heading."""
        line = line.strip()
        
        # Short ALL CAPS lines
        if line.isupper() and len(line) < 100:
            return True
        
        # Numbered headings
        for pattern in self.heading_patterns:
            if re.match(pattern, line):
                return True
        
        return False
    
    def _get_heading_level(self, line: str) -> int:
        """Determine heading level."""
        if re.match(r"^CHAPTER", line, re.IGNORECASE):
            return 1
        if re.match(r"^\d+\.\d+\.\d+", line):
            return 3
        if re.match(r"^\d+\.\d+", line):
            return 2
        if line.isupper():
            return 2
        return 3
    
    def _extract_defined_term(self, definition: str) -> str:
        """Extract the term being defined."""
        # Look for patterns like "X is defined as", "X is called"
        patterns = [
            r"^([A-Za-z\s]+?)\s+(?:is|are)\s+(?:defined|called|known)",
            r"^The\s+([A-Za-z\s]+?)\s+(?:is|are)",
            r"^([A-Za-z]+)",  # Fallback: first word
        ]
        
        for pattern in patterns:
            match = re.match(pattern, definition, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "Unknown"


def parse_directory(
    directory: str,
    subject: str,
    class_level: int = 9
) -> List[ParsedPage]:
    """
    Parse all PDFs in a directory.
    
    Args:
        directory: Path to directory containing PDFs
        subject: Subject name
        class_level: Class level
        
    Returns:
        List[ParsedPage]: All parsed pages
    """
    parser = PDFParser()
    all_pages = []
    
    dir_path = Path(directory)
    pdf_files = list(dir_path.glob("*.pdf"))
    
    logger.info(f"Found {len(pdf_files)} PDF files in {directory}")
    
    for pdf_file in pdf_files:
        try:
            pages = parser.parse_pdf(str(pdf_file), subject, class_level)
            all_pages.extend(pages)
        except Exception as e:
            logger.error(f"Failed to parse {pdf_file}: {e}")
    
    return all_pages
