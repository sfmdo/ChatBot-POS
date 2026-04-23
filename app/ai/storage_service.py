import asyncio
import logging
from app.models.database import save_message
from rag_lite.src.core.orchestrator import RAGOrchestrator

logger = logging.getLogger(__name__)
rag_orchestrator = RAGOrchestrator()

RAG_THRESHOLD = 500 

async def finalize_storage(telegram_id: int, user_msg: str, assistant_msg: str):
    """
    Saves the interaction. If a message is too long, it moves to RAG 
    and saves a placeholder in SQL to prevent token saturation.
    """
    sql_user_content = user_msg
    sql_assistant_content = assistant_msg

    try:
        await save_message(telegram_id, "user", sql_user_content)
        await save_message(telegram_id, "assistant", sql_assistant_content)
        logger.debug(f"SQL History updated for {telegram_id}")
    except Exception as e:
        logger.error(f"Failed to save to SQL: {e}")