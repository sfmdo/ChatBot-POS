import json
import datetime
from agent_mcp.client import mcp_manager

async def get_dynamic_context(telegram_id: int):
    tools_list = "No tools available."
    if mcp_manager.session:
        try:
            mcp_tools = await mcp_manager.session.list_tools()
            tools_list = "\n".join([
                f"- {t.name}: {t.description} (Args: {json.dumps(t.inputSchema)})" 
                for t in mcp_tools.tools
            ])
        except Exception as e:
            tools_list = f"Error fetching tools: {str(e)}"

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    return f"""
### OPERATIONAL PROTOCOL (ReAct)
You must use the following loop for every interaction:
1. **THOUGHT**: Analyze the intent and identify missing data in English.
2. **TOOL_CALL**: If data is needed, use: `TOOL_CALL: {{"tool": "name", "arguments": {{...}}}}`.
3. **FINAL ANSWER**: Once you have the data, provide the final response.

### SESSION INFO
- Current Time: {now}
- Token Saver: Long messages are replaced by "[INSERTED INTO RAG]". Use your `search_system_context` tool to retrieve them if needed, the context have the date of the messages.
- Active User ID: {telegram_id}

### AVAILABLE TOOLS
{tools_list}
"""