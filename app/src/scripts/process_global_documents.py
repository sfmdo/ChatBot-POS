import asyncio
import logging
import shutil
from pathlib import Path
from rag_lite.src.core.orchestrator import RAGOrchestrator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path.cwd()
PENDING_DIR = PROJECT_ROOT / "agent_mcp" / "resources" / "pending"
PROCESSED_DIR = PROJECT_ROOT / "agent_mcp" / "resources" / "processed"

async def process_global_documents():
    """
    Scans the 'pending' folder, ingests the documents into the RAG's global collection,
    and moves them to the 'processed' folder upon success.
    """
    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    pending_files = [f for f in PENDING_DIR.iterdir() if f.is_file() and not f.name.startswith(".")]

    if not pending_files:
        logger.info("No pending global documents to process in the startup folder.")
        return

    logger.info(f"Starting ingestion of {len(pending_files)} global documents...")
    
    orchestrator = RAGOrchestrator()

    for file_path in pending_files:
        logger.info(f"Ingesting file: {file_path.name}")
        
        try:
            result = await orchestrator.ingest_global_document(str(file_path.resolve()))
            
            chunks_inserted = result.get('chunks_inserted', 0)
            logger.info(f"Successfully processed '{file_path.name}': {chunks_inserted} chunks inserted.")

            dest_path = PROCESSED_DIR / file_path.name
            
            # If a file with the same name already exists in processed, overwrite it
            if dest_path.exists():
                dest_path.unlink()
                
            shutil.move(str(file_path), str(dest_path))
            logger.debug(f"File moved to: {dest_path}")

        except Exception as e:
            logger.error(f"Error processing file '{file_path.name}': {str(e)}")

    logger.info("Global injection process finished.")

if __name__ == "__main__":
    asyncio.run(process_global_documents())