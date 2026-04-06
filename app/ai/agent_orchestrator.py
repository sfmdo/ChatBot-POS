import json
import asyncio
from typing import AsyncGenerator
from .context_service import get_dynamic_context
from .llm_service import call_ollama
from .storage_service import finalize_storage
from app.models.database import get_user_context
from agent_mcp.client import mcp_manager
from mcp.types import TextContent
import re

async def query_ai(message: str, telegram_id: int) -> AsyncGenerator[str, None]:
    dynamic_context = await get_dynamic_context(telegram_id=telegram_id)
    
    messages = [
        {"role": "system", "content": dynamic_context},
        {"role": "user", "content": message}
    ]

    max_steps = 7
    final_text = "" 
    detected_lang = "the user's language" 

    for step in range(1, max_steps + 1):
        step_nudge = (
            f"\n\n[SYSTEM INSTRUCTION - STEP {step}/{max_steps}: "
            f"1. Your **THOUGHT**: MUST be in ENGLISH (Internal logic). "
            f"2. Use 'search_system_context' to find tool schemas if you don't have them. "
            f"3. Only the **FINAL ANSWER**: is in {detected_lang}. "
            f"4. If you use **TOOL_CALL**:, write ONLY the raw JSON.]"
            f"DO NOT search for the same schema more than twice."
        )
        
        current_messages = messages.copy()
        current_messages[-1]["content"] += step_nudge

        try:
            raw_content = await call_ollama(current_messages)
            if not raw_content: break

            # --- [DEBUG 1: THOUGHT] ---
            # Extraemos lo que sea que haya antes de TOOL_CALL o FINAL ANSWER
            thought_part = re.split(r"TOOL_CALL|FINAL\s*ANSWER", raw_content, flags=re.IGNORECASE)[0]
            print(f"\n{'='*20} [DEBUG STEP {step}] {'='*20}")
            print(f"--- THOUGHT ---\n{thought_part.strip()}")

            # --- [DETECCIÓN DE TOOL_CALL (FLEXIBLE)] ---
            if re.search(r"TOOL_CALL", raw_content, re.IGNORECASE):
                try:
                    # Buscamos el JSON entre llaves { } sin importar los tags
                    json_match = re.search(r"\{.*\}", raw_content, re.DOTALL)
                    
                    if json_match:
                        json_str = json_match.group(0)
                        tool_json = json.loads(json_str)
                        
                        name = tool_json.get("tool")
                        args = tool_json.get("arguments", {})

                        if name in ["fetch_chat_history", "search_system_context"]:
                            args["telegram_id"] = telegram_id

                        # --- [DEBUG 2: ACTION] ---
                        print(f"--- ACTION ---\nTool: {name} | Args: {args}")
                        yield f"🔍 *Executing {name}...*"
                        
                        if mcp_manager.session:
                            result = await mcp_manager.session.call_tool(name, arguments=args)
                            obs = "\n".join([c.text for c in result.content if isinstance(c, TextContent)])
                            
                            # --- [DEBUG 3: OBSERVATION] ---
                            print(f"--- OBSERVATION ---\n{obs}")
                            
                            if len(obs) > 30000: 
                                obs = obs[:30000] + (
                                        "\n\n[SYSTEM ERROR: Output too long and has been truncated. "
                                            "DO NOT call this tool again. You must provide a FINAL ANSWER "
                                            "based only on the partial data shown above.]"
                                        )
                        else:
                            obs = "Error: MCP session is not active."
                        
                        messages.append({"role": "assistant", "content": raw_content})
                        messages.append({"role": "user", "content": f"**OBSERVATION**: {obs}"})
                        continue
                    else:
                        print("--- ERROR: TOOL_CALL detected but no JSON found ---")
                except Exception as e:
                    print(f"--- ERROR: JSON Parsing failed: {e} ---")
                    messages.append({"role": "user", "content": f"ERROR: Invalid JSON. {str(e)}"})
                    continue

            # --- [DETECCIÓN DE FINAL ANSWER (FLEXIBLE)] ---
            elif re.search(r"FINAL\s*ANSWER", raw_content, re.IGNORECASE):
                final_part = re.split(r"FINAL\s*ANSWER:?", raw_content, flags=re.IGNORECASE)[-1]
                final_text = final_part.replace("**", "").strip()
                print(f"--- FINAL ANSWER ---\n{final_text}")
                yield final_text
                break

            else:
                final_text = raw_content.strip()
                print(f"--- FALLBACK ANSWER ---\n{final_text}")
                yield final_text
                break

        except Exception as e:
            print(f"--- CRITICAL ERROR: {e} ---")
            yield f"System Error: {str(e)}"
            return

    if final_text:
        await finalize_storage(telegram_id, message, final_text)