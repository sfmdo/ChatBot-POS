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
    
    @mcp.tool()
    async def system_capabilities():
        """
        Return the actions that the system can do
        """
        return"""
#SYSTEM CAPABILITIES & TECHNICAL HELP GUIDE

## 1. SALES & ANALYTICS MODULE
I can generate financial reports and analyze business performance:
- **Sales Summary:** Retrieve total revenue by period (today, yesterday, months, years) or custom date ranges.
- **Product Ranking:** List "Top Sellers" or "Least Sold" items to identify trends.
- **Sales Velocity:** Calculate how fast an item sells and estimate "days of stock remaining."
- **Revenue Contribution:** Measure what percentage of total income a specific product generates.

## 2. INVENTORY & CATALOG MANAGEMENT
I have real-time access to warehouse data and price lists:
- **Price & Stock Lookup:** Search for any item by Name, SKU, or ID to check current pricing and availability.
- **Critical Inventory:** Identify "Low Stock" items or "Out of Stock" (Stockouts) for restocking.
- **Dead Inventory:** Find stagnant products that haven't recorded sales since a specific date.
- **Warehouse Valuation:** Calculate the total monetary value of your current stock and projected margins.
- **Promotions:** Check active discounts, store-wide sales, and specific product offers.

## 3. CUSTOMER RELATIONSHIP MANAGEMENT (CRM)
I manage client profiles and financial standing:
- **Customer Search:** Locate profiles by Name, identify "Frequent Shoppers," or filter by "Debtors."
- **Financial History:** Check outstanding debts, credit limits, payment records, and loyalty points.
- **Spending Habits:** Analyze what a specific customer has purchased over recent months.
- **Order Breakdown:** Retrieve itemized details for any transaction using the Folio or Order ID.

## 4. SUPPLIER DIRECTORY
I manage your commercial partners' data:
- **Contact Information:** Lookup tax IDs (RFC), business addresses, emails, and phone numbers.
- **Supplier Catalog:** Identify which products are supplied by specific vendors using their ID.

## 5. SYSTEM & MEMORY
- **Chat Context:** I can recall recent messages to resolve pronouns like "it," "him," or "that product we mentioned."
- **User Authorization:** Verify system access and connection details for authorized mobile numbers.

---

## TIME & DATE LOGIC
I understand natural language for time-based reports:
- **Relative:** "last 15 days," "past 3 months," "last year."
- **Predefined:** "today," "yesterday," "this month," "last month."
- **Absolute:** "from January 1st to March 15th."

---
"""
    @mcp.tool
    async def system_greeting_protocol():
        """
        Returns a professional greeting and redirects the user to POS tasks.
        """
        return """
    **POS SYSTEM ONLINE**
    Hello. I am your Enterprise Data Assistant. I am optimized for professional POS operations only.

    I can assist you with:
    - **📦 Inventory:** Stock, prices, and catalog.
    - **📊 Sales:** Revenue reports, rankings, and analytics.
    - **👤 Customers:** Debt, loyalty points, and profiles.
    - **🤝 Suppliers:** Contact info and vendor details.

    Please provide a specific data request or ask for 'help' to see more details.
        """