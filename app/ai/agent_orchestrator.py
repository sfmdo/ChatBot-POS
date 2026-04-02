import json
import asyncio
from typing import AsyncGenerator
from .context_service import get_dynamic_context
from .llm_service import call_ollama
from .storage_service import finalize_storage
from app.models.database import get_user_context
from agent_mcp.client import mcp_manager
from mcp.types import TextContent

async def query_ai(message: str, telegram_id: int) -> AsyncGenerator[str, None]:
    # ! Setup Context
    dynamic_context = await get_dynamic_context(telegram_id=telegram_id)
    history = await get_user_context(telegram_id, limit=2)
    
    messages = [
        {"role": "system", "content": dynamic_context},
        *history,
        {"role": "user", "content": message}
    ]

    max_steps = 5
    final_text = ""

    # 2. ReAct Loop
    for step in range(1, max_steps + 1):
        # Apply step nudge
        original_prompt = messages[-1]["content"]
        messages[-1]["content"] += f"\n\n(Step {step}/{max_steps})"

        try:
            raw_content = await call_ollama(messages)
            messages[-1]["content"] = original_prompt # Clean history

            if not raw_content: break

            # CASE A: TOOL CALL
            if "TOOL_CALL:" in raw_content:
                # Yield Thought for UI
                if "THOUGHT:" in raw_content:
                    thought = raw_content.split("TOOL_CALL:")[0].replace("THOUGHT:", "").strip()
                    if thought: yield f"💭 _{thought}_"

                try:
                    tool_json = json.loads(raw_content.split("TOOL_CALL:")[-1].strip())
                    name = tool_json.get("tool")
                    args = tool_json.get("arguments", tool_json.get("query", {}))
                    if isinstance(args, dict):
                        args["telegram_id"] = telegram_id

                    yield f"🔍 *Executing {name}...*"
                    
                    if mcp_manager.session:
                        result = await mcp_manager.session.call_tool(name, arguments=args)
                        obs = "\n".join([c.text for c in result.content if isinstance(c, TextContent)])
                    else:
                        obs = "Error: MCP session is not active."
                    
                    
                    messages.append({"role": "assistant", "content": raw_content})
                    messages.append({"role": "user", "content": f"OBSERVATION: {obs}"})
                    continue
                except Exception as e:
                    messages.append({"role": "user", "content": f"ERROR: Invalid format. {str(e)}"})
                    continue

            # CASE B: FINAL ANSWER
            elif "FINAL ANSWER:" in raw_content:
                final_text = raw_content.split("FINAL ANSWER:")[-1].strip()
                yield final_text
                break

            # CASE C: DIRECT RESPONSE (Fallback)
            else:
                final_text = raw_content
                yield final_text
                break

        except Exception as e:
            yield f"❌ System Error: {str(e)}"
            return

    # 3. Finalize and Store (L1 SQL + L2 RAG)
    if final_text:
        await finalize_storage(telegram_id, message, final_text)