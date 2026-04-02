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
    
    context_to_rag = []

    sql_user_content = user_msg
    sql_assistant_content = assistant_msg

    if len(user_msg) > RAG_THRESHOLD:
        context_to_rag.append({'role': 'user','content': f'{user_msg}'})
        sql_user_content = "[LONG MESSAGE INSERTED INTO RAG - USE SEARCH TOOL TO RETRIEVE, PREFER USING THE DATETIME]"

    if len(assistant_msg) > RAG_THRESHOLD:
        context_to_rag.append({'role': 'assistant','content': f'{assistant_msg}'})
        sql_assistant_content = "[DETAILED RESPONSE INSERTED INTO RAG - USE SEARCH TOOL TO RETRIEVE,PREFER USING THE DATETIME]"

    if context_to_rag:
        try:
            await rag_orchestrator.ingest_user_context(
                text=context_to_rag,
                user_id=str(telegram_id),
            )
            logger.info(f"Long-term memory indexed for user {telegram_id}")
        except Exception as e:
            logger.error(f"Failed to save to RAG: {e}")
            # Fallback: if RAG fails, keep original text in SQL
            sql_user_content = user_msg
            sql_assistant_content = assistant_msg

    try:
        await asyncio.to_thread(save_message, telegram_id, "user", sql_user_content)
        await asyncio.to_thread(save_message, telegram_id, "assistant", sql_assistant_content)
        logger.debug(f"SQL History updated for {telegram_id}")
    except Exception as e:
        logger.error(f"Failed to save to SQL: {e}")