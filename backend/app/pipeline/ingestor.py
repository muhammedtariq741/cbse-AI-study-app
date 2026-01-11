"""
Data Ingestion Pipeline

CLI tool for batch processing CBSE content:
1. Parse PDFs
2. Create chunks  
3. Generate embeddings
4. Store in vector database
"""

import asyncio
import argparse
import json
from pathlib import Path
from typing import Optional
import logging
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.pipeline.parser import PDFParser, parse_directory
from app.pipeline.chunker import IntelligentChunker
from app.core.embeddings import generate_embeddings_batch
from app.storage.vector_store import FAISSVectorStore
from app.models.schemas import SourceType

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class IngestionPipeline:
    """
    End-to-end ingestion pipeline for CBSE content.
    """
    
    def __init__(
        self,
        data_dir: str = "./data",
        output_dir: str = "./data/embeddings"
    ):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.parser = PDFParser()
        self.chunker = IntelligentChunker()
        self.vector_store = FAISSVectorStore(index_path=str(self.output_dir))
    
    async def ingest_pdfs(
        self,
        pdf_dir: str,
        subject: str,
        source_type: str = "ncert_textbook",
        class_level: int = 9,
        save_intermediate: bool = True
    ) -> dict:
        """
        Ingest PDFs from a directory.
        
        Args:
            pdf_dir: Directory containing PDFs
            subject: Subject name (Science, Mathematics, etc.)
            source_type: Type of source (ncert_textbook, sample_paper, etc.)
            class_level: Class level
            save_intermediate: Whether to save intermediate JSON files
            
        Returns:
            dict: Statistics about the ingestion
        """
        logger.info(f"Starting ingestion for {subject} from {pdf_dir}")
        
        # Step 1: Parse PDFs
        logger.info("Step 1: Parsing PDFs...")
        pages = parse_directory(pdf_dir, subject, class_level)
        logger.info(f"Parsed {len(pages)} pages")
        
        if save_intermediate:
            self._save_parsed_pages(pages, subject)
        
        # Step 2: Create chunks
        logger.info("Step 2: Creating chunks...")
        source_type_enum = SourceType(source_type)
        chunks = self.chunker.chunk_pages(pages, subject, source_type_enum, class_level)
        logger.info(f"Created {len(chunks)} chunks")
        
        if save_intermediate:
            self._save_chunks(chunks, subject)
        
        # Step 3: Generate embeddings
        logger.info("Step 3: Generating embeddings...")
        texts = [chunk.text for chunk in chunks]
        embeddings = await generate_embeddings_batch(texts)
        logger.info(f"Generated {len(embeddings)} embeddings")
        
        # Step 4: Store in vector database
        logger.info("Step 4: Storing in vector database...")
        if self.vector_store.index is None:
            self.vector_store.create_index()
        
        self.vector_store.add(chunks, embeddings)
        self.vector_store.save()
        
        stats = {
            "pages_parsed": len(pages),
            "chunks_created": len(chunks),
            "embeddings_generated": len(embeddings),
            "index_total": self.vector_store.index.ntotal
        }
        
        logger.info(f"Ingestion complete: {stats}")
        return stats
    
    async def ingest_text_file(
        self,
        text_file: str,
        subject: str,
        chapter: str,
        source_type: str = "ncert_textbook",
        class_level: int = 9
    ) -> dict:
        """
        Ingest content from a plain text file.
        
        Useful for prepared Q&A content or marking schemes.
        """
        logger.info(f"Ingesting text file: {text_file}")
        
        with open(text_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Create a fake page for chunking
        from app.models.schemas import ParsedPage
        
        page = ParsedPage(
            source_file=Path(text_file).name,
            page_number=1,
            chapter=chapter,
            raw_text=content,
            elements=[{"type": "paragraph", "text": content}]
        )
        
        source_type_enum = SourceType(source_type)
        chunks = self.chunker.chunk_pages([page], subject, source_type_enum, class_level)
        
        texts = [chunk.text for chunk in chunks]
        embeddings = await generate_embeddings_batch(texts)
        
        if self.vector_store.index is None:
            self.vector_store.create_index()
        
        self.vector_store.add(chunks, embeddings)
        self.vector_store.save()
        
        return {
            "chunks_created": len(chunks),
            "embeddings_generated": len(embeddings)
        }
    
    def _save_parsed_pages(self, pages, subject: str):
        """Save parsed pages to JSON."""
        output_file = self.data_dir / "processed" / f"{subject.lower()}_pages.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        pages_data = [p.model_dump(mode="json") for p in pages]
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(pages_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved parsed pages to {output_file}")
    
    def _save_chunks(self, chunks, subject: str):
        """Save chunks to JSON."""
        output_file = self.data_dir / "processed" / f"{subject.lower()}_chunks.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        chunks_data = [c.model_dump(mode="json") for c in chunks]
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(chunks_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved {len(chunks)} chunks to {output_file}")
    
    def get_stats(self) -> dict:
        """Get current index statistics."""
        return self.vector_store.get_stats()


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="CBSE Content Ingestion Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ingest Science PDFs
  python ingestor.py --pdf-dir ./data/raw/science --subject Science
  
  # Ingest Maths with different source type
  python ingestor.py --pdf-dir ./data/raw/maths --subject Mathematics --source-type ncert_textbook
  
  # Ingest a text file
  python ingestor.py --text-file ./data/raw/marking_scheme.txt --subject Science --chapter "Light"
        """
    )
    
    parser.add_argument(
        "--pdf-dir",
        help="Directory containing PDFs to ingest"
    )
    parser.add_argument(
        "--text-file",
        help="Text file to ingest"
    )
    parser.add_argument(
        "--subject",
        required=True,
        choices=["Science", "Mathematics", "Social Science", "English"],
        help="Subject name"
    )
    parser.add_argument(
        "--chapter",
        default="General",
        help="Chapter name (for text file ingestion)"
    )
    parser.add_argument(
        "--source-type",
        default="ncert_textbook",
        choices=["ncert_textbook", "ncert_exemplar", "sample_paper", "previous_year", "marking_scheme"],
        help="Source type"
    )
    parser.add_argument(
        "--class-level",
        type=int,
        default=9,
        help="Class level (default: 9)"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show index statistics"
    )
    
    args = parser.parse_args()
    
    pipeline = IngestionPipeline()
    
    if args.stats:
        stats = pipeline.get_stats()
        print("\n📊 Index Statistics:")
        print(f"  Total vectors: {stats['total_vectors']}")
        print(f"  Dimension: {stats['dimension']}")
        print(f"  Index path: {stats['index_path']}")
        print(f"  Subjects: {stats['subjects']}")
        return
    
    if args.pdf_dir:
        asyncio.run(pipeline.ingest_pdfs(
            pdf_dir=args.pdf_dir,
            subject=args.subject,
            source_type=args.source_type,
            class_level=args.class_level
        ))
    elif args.text_file:
        asyncio.run(pipeline.ingest_text_file(
            text_file=args.text_file,
            subject=args.subject,
            chapter=args.chapter,
            source_type=args.source_type,
            class_level=args.class_level
        ))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
