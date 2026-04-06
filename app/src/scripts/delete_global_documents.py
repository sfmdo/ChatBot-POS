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

async def wipe_global_documents():
    """
    Scans the 'processed' folder, removes global documents from the RAG's 
    vector database, and moves files back to 'pending' for re-processing.
    """
    # Ensure directories exist
    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # List files in the processed folder
    processed_files = [f for f in PROCESSED_DIR.iterdir() if f.is_file() and not f.name.startswith(".")]

    if not processed_files:
        logger.info("No processed global documents found to delete.")
        return

    logger.info(f"Starting deletion of {len(processed_files)} global documents from the database...")
    
    orchestrator = RAGOrchestrator()

    for file_path in processed_files:
        logger.info(f"Deleting from RAG: {file_path.name}")
        
        try:
            # 1. Delete from Vector Database
            # delete_global_document uses os.path.basename internally for the source_name
            result = await orchestrator.delete_global_document(str(file_path.resolve()))
            
            if result.get("status") == "success":
                logger.info(f"Success: '{file_path.name}' removed from ChromaDB.")

                # 2. Move physical file back to PENDING
                dest_path = PENDING_DIR / file_path.name
                
                # If it already exists in pending, unlink it to avoid move errors
                if dest_path.exists():
                    dest_path.unlink()
                    
                shutil.move(str(file_path), str(dest_path))
                logger.info(f"File moved back to: {PENDING_DIR.name}/")
            else:
                logger.warning(f"Could not confirm deletion of '{file_path.name}' in the DB.")

        except Exception as e:
            logger.error(f"Critical error while trying to delete '{file_path.name}': {str(e)}")

    logger.info("Global cleanup process finished.")

if __name__ == "__main__":
    try:
        asyncio.run(wipe_global_documents())
    except KeyboardInterrupt:
        logger.info("Process cancelled by user.")