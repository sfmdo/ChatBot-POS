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

import json
import asyncio
import re
from typing import AsyncGenerator
from .context_service import get_dynamic_context
from .llm_service import call_ollama
from .storage_service import finalize_storage
from agent_mcp.client import mcp_manager
from mcp.types import TextContent

async def query_ai(message: str, telegram_id: int) -> AsyncGenerator[str, None]:
    dynamic_context = await get_dynamic_context(telegram_id=telegram_id)
    
    messages = [
        {"role": "system", "content": dynamic_context},
        {"role": "user", "content": message}
    ]
    
    last_action = ""
    max_steps = 10
    final_text = "" 
    detected_lang = "the user's original language" 

    for step in range(1, max_steps + 1):
        # --- NUDGE DINÁMICO ---
        # Si es el último paso, forzamos el cierre.
        if step == max_steps:
            instruction = f"FINAL STEP! You MUST provide your **FINAL ANSWER** in {detected_lang} now. Tool calls are FORBIDDEN."
        else:
            instruction = (
                f"Step {step}/{max_steps}. 1. THOUGHT in English. 2. Identified Language: {detected_lang}. "
                f"3. If tool schema is missing, use 'search_system_context'. 4. Use **TOOL_CALL**: {{}} or **FINAL ANSWER**: text. "
                f"5. When searching context, use GENERAL technical terms (e.g., 'product price', 'inventory lookup', 'customer debt') "
                f"instead of specific user data (e.g., avoid 'tortilla price' or 'Oscar debt')."
            )

        step_nudge = f"\n\n[SYSTEM: {instruction}]"
        print(step_nudge)
        current_messages = messages.copy()
        current_messages[-1]["content"] += step_nudge

        try:
            raw_content = await call_ollama(current_messages)
            if not raw_content: break

            # --- [DEBUG 1: THOUGHT & LANGUAGE] ---
            # Extraemos el pensamiento para el log
            thought_part = re.split(r"TOOL_CALL|FINAL\s*ANSWER", raw_content, flags=re.IGNORECASE)[0]
            print(f"\n{'='*20} [DEBUG STEP {step}] {'='*20}")
            print(f"--- THOUGHT ---\n{thought_part.strip()}")

            # Detección de idioma en el primer paso para consistencia
            if step == 1:
                lang_match = re.search(r"LANGUAGE:\s*(\w+)", raw_content, re.IGNORECASE)
                if lang_match:
                    detected_lang = lang_match.group(1).strip()
                    print(f"--- LANGUAGE DETECTED: {detected_lang} ---")

            # --- [DETECCIÓN DE TOOL_CALL] ---
            if re.search(r"TOOL_CALL", raw_content, re.IGNORECASE) and step < max_steps:
                try:
                    json_match = re.search(r"\{.*\}", raw_content, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                        tool_json = json.loads(json_str)
                        
                        name = tool_json.get("tool")
                        args = tool_json.get("arguments", {})

                        if name in ["fetch_chat_history", "search_system_context"]:
                            args["telegram_id"] = telegram_id
                        
                        # --- PREVENCIÓN DE BUCLES ---
                        current_action = f"{name}-{json.dumps(args, sort_keys=True)}"
                        if current_action == last_action:
                            print(f"--- [LOOP PREVENTION] Repeating {name} ---")
                            obs = "SYSTEM: You already called this tool with these args. Use the previous OBSERVATION to answer."
                            messages.append({"role": "assistant", "content": raw_content})
                            messages.append({"role": "user", "content": obs})
                            continue 

                        last_action = current_action

                        # --- EJECUCIÓN ---
                        print(f"--- ACTION ---\nTool: {name} | Args: {args}")
                        yield f"🔍 *Executing {name}...*"
                        
                        if mcp_manager.session:
                            result = await mcp_manager.session.call_tool(name, arguments=args)
                            obs = "\n".join([c.text for c in result.content if isinstance(c, TextContent)])
                            
                            print(f"--- OBSERVATION ---\n{obs}")
                            
                            if len(obs) > 30000: 
                                obs = obs[:30000] + "\n\n[SYSTEM: Data truncated. Do not retry. Answer with what you have.]"
                        else:
                            obs = "Error: MCP session is not active."
                        
                        messages.append({"role": "assistant", "content": raw_content})
                        messages.append({"role": "user", "content": f"**OBSERVATION**: {obs}"})
                        continue

                except Exception as e:
                    print(f"--- JSON ERROR: {e} ---")
                    messages.append({"role": "user", "content": f"ERROR: Invalid JSON in TOOL_CALL. {str(e)}"})
                    continue

            # --- [DETECCIÓN DE FINAL ANSWER] ---
            elif re.search(r"FINAL\s*ANSWER", raw_content, re.IGNORECASE):
                final_part = re.split(r"FINAL\s*ANSWER:?", raw_content, flags=re.IGNORECASE)[-1]
                final_text = final_part.replace("**", "").strip()
                print(f"--- FINAL ANSWER ---\n{final_text}")
                yield final_text
                break

            else:
                # Fallback: si no hay tags pero hay texto, lo tomamos como respuesta final si no es el paso 1
                final_text = raw_content.strip()
                print(f"--- FALLBACK ANSWER ---\n{final_text}")
                yield final_text
                break

        except Exception as e:
            print(f"--- CRITICAL ERROR: {e} ---")
            yield f"System Error: {str(e)}"
            return

    # Guardado final en SQL/RAG
    if final_text:
        await finalize_storage(telegram_id, message, final_text)