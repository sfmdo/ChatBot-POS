import logging
from app.models.database import get_user_context
from rag_lite.src.core.orchestrator import RAGOrchestrator

orchestrator = RAGOrchestrator()

logger = logging.getLogger(__name__)

def setup_memory_and_rag_tools(mcp):
    """
    Registers Memory and RAG tools to allow the agent to self-manage 
    context and internal knowledge during its reasoning cycles.
    """

    # ! CHAT HISTORY 
    @mcp.tool()
    async def fetch_chat_history(telegram_id: int, limit: int = 5) -> str:
        """
        Retrieves the last N messages from the current conversation.
        USE THIS TOOL WHEN:
        1. The user refers to previous statements (e.g., "as I said," "repeat that").
        2. You need to confirm a value mentioned earlier in the chat.
        3. The current prompt is ambiguous and requires context from the immediate past.
        """
        try:
            history = await get_user_context(telegram_id=telegram_id, limit=limit)
            
            if not history:
                return "System: No previous conversation history found for this user."
            
            output = "### RECENT CONVERSATION LOG \n"
            for entry in history:
                role = "User" if entry["role"] == "user" else "Assistant (You)"
                content = entry["content"]
                output += f"[{role}]: {content}\n"
            output += "### END OF LOG"
            
            return output
            
        except Exception as e:
            logger.error(f"Error fetching history for {telegram_id}: {e}")
            return f"System Error: Unable to access chat history. Proceeding without context."


    # ! RAG
    @mcp.tool()
    async def search_system_context(query: str, telegram_id: int) -> str:
        """
        Searches the user's past chat history AND the POS knowledge base (documents, manuals) simultaneously.
        USE THIS TOOL WHEN:
        1. You need to recall what the user said previously in the conversation.
        2. You need to look up business rules, store policies, or system operations from the manuals.
        3. The user asks a question that requires background context to answer correctly.
        
        Provide a concise query summarizing what you are looking for (e.g., "refund policy", "what did the user want to buy").
        """
        try:
            logger.info(f"Retrieving context for user {telegram_id} with query: '{query}'")
            
            context = await orchestrator.search_context(
                query=query, 
                user_id=str(telegram_id)
            )
            
            return context
            
        except Exception as e:
            logger.error(f"Error in RAG Orchestrator for {telegram_id}: {e}")
            return "System Error: Unable to retrieve background context or chat memory at this time. Proceed with general knowledge."
