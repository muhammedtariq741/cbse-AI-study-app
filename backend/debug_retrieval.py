
import asyncio
import logging
import sys

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.storage.vector_store import get_vector_store
from app.core.retriever import get_retriever

async def debug():
    print("--- DEBUGGING RETRIEVAL ---")
    
    # 1. Check Vector Store Stats
    vs = get_vector_store()
    stats = vs.get_stats()
    print(f"Vector Store Stats: {stats}")
    
    if stats["total_vectors"] == 0:
        print("CRITIAL: Vector store is empty! Ingestion failed or index not loaded.")
        return

    # 2. Check a raw search (no filters)
    query = "states of matter"
    print(f"\nSearching for: '{query}' (NO FILTERS)")
    from app.core.embeddings import embed_query
    emb = await embed_query(query)
    results_raw = vs.search(emb, top_k=5)
    print(f"Raw results found: {len(results_raw)}")
    for r in results_raw:
        print(f" - Score: {r.score:.4f} | Chapter: {r.chunk.metadata.chapter} | Class: {r.chunk.metadata.class_level}")

    # 3. Check Retriever (with filters)
    print(f"\nSearching via Retriever (WITH FILTERS)")
    retriever = get_retriever()
    results = await retriever.retrieve(query)
    print(f"Retriever results found: {len(results)}")
    
    if len(results) == 0:
        print("CRITICAL: Retriever returned 0 results. Likely a metadata filter mismatch.")
        # Check what filters are being used
        # We can't easily see internal logic, but we know it uses {"class": 9}
        print("Checking metadata of first raw result to see if it matches 'class': 9")
        if results_raw:
            print(f"First chunk metadata: {results_raw[0].chunk.metadata}")

if __name__ == "__main__":
    asyncio.run(debug())
