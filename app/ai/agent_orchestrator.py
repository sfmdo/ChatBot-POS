import json
import re
from typing import AsyncGenerator
from .context_service import get_dynamic_context, get_pepe_analyst_context
from .llm_service import call_ollama
from .storage_service import finalize_storage
from app.models.database import get_user_context
from agent_mcp.client import mcp_manager
from typing import AsyncGenerator, Dict, List, Any, Optional
from mcp.types import TextContent

class ReActAgent:
    def __init__(self, telegram_id: int, message: str, max_steps: int = 10):
        self.telegram_id = telegram_id
        self.original_message = message
        self.max_steps = max_steps
        self.detected_lang = "Spanish"
        self.last_action = ""
        self.messages = []

    async def initialize(self):
        """Prepara el contexto inicial con la jerarquía correcta."""
        identity_context = get_dynamic_context(self.telegram_id)
        self.messages = [
            {"role": "system", "content": identity_context},
            {"role": "user", "content": f"**USER PETITION**: {self.original_message}"}
        ]

    def _build_step_nudge(self, step: int) -> str:
        instruction = f"\n\n--- [KERNEL STEP {step}/{self.max_steps}] ---\n"
        
        if step == self.max_steps:
            instruction += (
                "**CRITICAL: LAST ATTEMPT.** Summarize all partial data found. "
                "If a tool failed, explain technically why (e.g., 'Validation Error in argument X'). "
                "Output FINAL ANSWER with the current state of knowledge."
            )
        elif step == 1:
            instruction += (
                "The only tool you need to call in this step is the system context tool"
                "**PHASE 1: CONTEXTUAL ANALYSIS & ROADMAP**\n"
                "1. **PAST CONTEXT**: Check if the User, ID, or SKU was mentioned in previous messages.\n"
                "2. **DOMAIN**: Is this [PRODUCTS], [SUPPLIERS], [CUSTOMERS] or [SYSTEM]?\n"
                "3. **SCHEMA CHECK**: Call 'search_system_context' to get the EXACT JSON keys for the tools you need. "
                "DO NOT guess argument names (like 'query' or 'search'). Use what the documentation says.\n"
                "4. **STRATEGY**: Define your path (e.g., Search Supplier -> Get ID -> Filter Products)."
            )
        else:
            instruction += (
                "**PHASE N: ITERATIVE EXECUTION & ERROR RECOVERY**\n"
                "1. **ANALYZE LAST OBSERVATION**: \n"
                "    - If the observation return the data of the tool, analyze it to see if that if the required for the objective of the **USER PETITION**"
                "   - If 'ValidationError' or 'Unexpected keyword': You used a wrong JSON key. READ the tool definition again and FIX the argument name.\n"
                "   - If 'Empty Result': The search was too specific. Try a broader search or a partial name.\n"
                "2. **REASONING**: If Strategy A fails, try Strategy B. For example, if searching products by name fails, search for the supplier first to get a list.\n"
                "3. **MULTI-STEP**: Do not stop until you have the final data (prices, stock, etc.). Use the ID obtained in the previous step.\n"
                "**Format**: THOUGHT: (Deep analysis of the error or next step) -> TOOL_CALL: {JSON} OR FINAL ANSWER: (Full data)."
            )
        
        return f"{instruction}\nSystem Language: English (Technical)\n---"

    async def _prepare_messages(self, step: int) -> List[Dict[str, str]]:
        """
        Crea una versión de la conversación para enviar al LLM.
        Añade instrucciones temporales que NO se guardan en el historial permanente.
        """
        instrumented_msgs = [m.copy() for m in self.messages]
        
        nudge = self._build_step_nudge(step)
        
        if step == 1:
            instrumented_msgs.append({"role": "system", "content": f"{nudge}"})
        else:
            instrumented_msgs.append({"role": "system", "content": nudge})
            
        return instrumented_msgs

    async def _execute_tool(self, name: str, args: Dict[str, Any]) -> str:
        """Maneja la ejecución de herramientas a través de MCP."""
        if name in ["fetch_chat_history", "search_system_context"]:
            args["telegram_id"] = self.telegram_id

        current_action = f"{name}-{json.dumps(args, sort_keys=True)}"
        if current_action == self.last_action:
            return "SYSTEM: You already called this tool with these args. Use the previous OBSERVATION."
        
        self.last_action = current_action

        if not mcp_manager.session:
            return "Error: MCP session is not active."

        try:
            result = await mcp_manager.session.call_tool(name, arguments=args)
            obs = "\n".join([c.text for c in result.content if isinstance(c, TextContent)])
            return obs[:30000] if len(obs) > 30000 else obs
        except Exception as e:
            return f"Error executing tool: {str(e)}"

    def _parse_response(self, content: str) -> Dict[str, Any]:
        """Extrae la intención (Tool o Final Answer) de la respuesta del LLM."""
        if re.search(r"TOOL_CALL", content, re.IGNORECASE):
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                try:
                    return {"type": "tool", "data": json.loads(json_match.group(0))}
                except:
                    return {"type": "error", "data": "Invalid JSON format."}
        
        if re.search(r"FINAL\s*ANSWER", content, re.IGNORECASE):
            final_part = re.split(r"FINAL\s*ANSWER:?", content, flags=re.IGNORECASE)[-1]
            final_text = final_part.replace("**", "").strip()
            return {"type": "final", "data": final_text}
        
        return {"type": "fallback", "data": content.strip()}

    def _clean_thought_for_user(self, thought: str) -> str:
        """Clean the text for the Telegram User"""
        text = thought.replace("PLANNING:", "📋").replace("THOUGHT:", "💡")
        text = text.replace("Status Update:", "").replace("Action Analysis:", "")
        text = text.replace("Domain Identification:", "").replace("Entity Status:", "")
        
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return "\n".join(lines)
    
    async def run(self) -> AsyncGenerator[str, None]:
        """Ciclo principal de ejecución del agente."""
        await self.initialize()

        for step in range(1, self.max_steps + 1):
            print(f"\n{'='*20} [DEBUG STEP {step}] {'='*20}")
            prepared_msgs = await self._prepare_messages(step)
            raw_content = await call_ollama(prepared_msgs)
            if not raw_content: break
            print(f"{raw_content}")
            thought = re.split(r"TOOL_CALL|FINAL\s*ANSWER", raw_content, flags=re.IGNORECASE)[0]
            
            display_thought = self._clean_thought_for_user(thought)
            
            if display_thought:
                yield f"🧠 *{display_thought}*"

            if step == 1:
                lang_match = re.search(r"LANGUAGE:\s*(\w+)", raw_content, re.IGNORECASE)
                if lang_match: self.detected_lang = lang_match.group(1).strip()

            parsed = self._parse_response(raw_content)

            if parsed["type"] == "tool":
                tool_name = parsed["data"].get("tool")
                tool_args = parsed["data"].get("arguments", {})

                self.messages.append({"role": "assistant", "content": raw_content})
                observation = await self._execute_tool(tool_name, tool_args)
                print(f"**Observation**: \n {observation}\n")
            
                if tool_name == "search_system_context":
                    rag_content = (
                        "### IMPORTANT: SYSTEM TOOLS FOUND ###\n"
                        "You MUST use one of the tools below to answer the user request. "
                        "If a tool matches the intent, extract the arguments and CALL IT.\n\n"
                        f"{observation}" 
                    )
                    self.messages.append({"role": "user", "content": rag_content})
                else:
                    self.messages.append({"role": "user", "content": f"**OBSERVATION**: {observation}"})
                continue

            elif parsed["type"] == "final":
                final_text = parsed["data"]
                await finalize_storage(self.telegram_id, self.original_message, final_text)
                final_text_origin_language = await self._translate_to_pepe(final_answer=final_text)
                print(f"\n=== FINAL TEXT TO THE USER===\n{final_text_origin_language}")
                yield final_text_origin_language
                
                return

            else: 
                fallback_text = parsed["data"]
                await finalize_storage(self.telegram_id, self.original_message, fallback_text)
                
                translated = await self._translate_to_pepe(fallback_text)
                print(f"\n=== FALLBACK TRANSLATED ===\n{translated}")
                yield translated

                return

    async def _translate_to_pepe(self, final_answer: str) -> str:
        """Traduce y aplica la personalidad de Pepe al resultado final."""
        translation_prompt = [
            {"role": "system", "content": get_pepe_analyst_context(language=self.detected_lang,original_msg=self.original_message,
                                                                gathered_data_from_phase_1=final_answer)},
            {"role": "user", "content": f"ONLY RETURN DE **FINAL ANSWER**\n\n"}
        ]
        response = await call_ollama(translation_prompt)
        final_response = self._parse_response(response)
        if final_response["type"] == "final":
            return final_response["data"]
        return response.replace("**FINAL ANSWER**:", "").strip()
    
async def query_ai(message: str, telegram_id: int) -> AsyncGenerator[str, None]:
    agent = ReActAgent(telegram_id, message)
    async for chunk in agent.run():
        yield chunk