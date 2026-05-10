import json
import re
from typing import AsyncGenerator
from .context_service import get_dynamic_context, get_pepe_analyst_context, get_gatekeeper_context
from .llm_service import call_openai_standard
from .storage_service import finalize_storage
from app.models.database import get_user_context
from agent_mcp.client import mcp_manager
from typing import AsyncGenerator, Dict, List, Any
from mcp.types import TextContent

class ReActAgent:
    def __init__(self, telegram_id: int, message: str, max_steps: int = 10):
        self.telegram_id = telegram_id
        self.original_message = message
        self.max_steps = max_steps
        self.detected_lang = "Spanish"
        self.last_action = ""
        self.messages = []
        self.requires_info = True
        self.history_text = "No Past history"
        self.requires_analysis = False
        self.pepemodel = 1
        self.qwenmodel = 2

    async def initialize(self):
        """Prepara el contexto inicial con la jerarquía correcta."""
        identity_context = get_dynamic_context(self.telegram_id)
        self.messages = [
            {"role": "system", "content": identity_context},
            {"role": "user", "content": f"**USER PETITION**: {self.original_message}"}
        ]

    def _build_step_nudge(self, step: int) -> str:
        instruction = f"\n\n--- [KERNEL STEP {step}/{self.max_steps}] ---\n"
        
        if not self.requires_info and self.requires_analysis:
            instruction += (
                "**PHASE 1: CONTEXTUAL ANALYSIS BYPASS**\n"
                "The Gatekeeper determined this request does NOT require fetching new database info, but it DOES require analyzing past context.\n"
                "1. DO NOT call any database or inventory tools.\n"
                "2. You may ONLY call the 'fetch_chat_history' tool (Limit: 1 time) to retrieve the formatted history.\n"
                "3. Analyze the history and immediately output EXACTLY -> FINAL ANSWER: [Your detailed summary or analysis of the retrieved context]."
            )
        
        if not self.requires_info:
            instruction += (
                "**PHASE 1: CONVERSATIONAL BYPASS**\n"
                "The Gatekeeper determined this request does NOT require fetching database info.\n"
                "DO NOT call any tools. DO NOT use search_system_context.\n"
                "Immediately output EXACTLY -> FINAL ANSWER: Empty Technical Report. Pure conversational intent."
            )
        
        elif step == self.max_steps:
            instruction += (
                "**CRITICAL: LAST ATTEMPT.** Summarize all partial data found. "
                "If a tool failed, explain technically why (e.g., 'Validation Error in argument X'). "
                "Output FINAL ANSWER with the current state of knowledge."
            )
        elif step == 1:
            instruction += (
                "The only tool you need to call in this step is the system context tool.\n"
                "**PHASE 1: CONTEXTUAL ANALYSIS & ROADMAP**\n"
                "1. **PAST CONTEXT**: Check if the User, ID, or SKU was mentioned in previous messages.\n"
                "2. **DOMAIN**: Is this [PRODUCTS], [SUPPLIERS], [CUSTOMERS], [SYSTEM], [ANALYTICS] or [CONVERSATION]?\n"
                "3. **SCHEMA CHECK**: Call 'search_system_context' to get the EXACT JSON keys for the tools you need. "
                "DO NOT guess argument names (like 'query' or 'search'). Use what the documentation says.\n"
                "4. **STRATEGY**: Define your path (e.g., Search Supplier -> Get ID -> Filter Products. Or for Analytics -> search tool -> Execute)."
            )
        else: 
            instruction += (
        "**PHASE N: EXECUTION & ADAPTATION**\n"
        "1. **ANALYZE LAST OBSERVATION**: Briefly assess the result from the previous tool call.\n"
        "2. **IMMEDIATE ACTION**: Based on your analysis, you MUST either:\n"
        "   a) **Call the NEXT logical tool** to continue your plan.\n"
        "   b) **Output FINAL ANSWER** if you have all the data.\n"
        "**CRITICAL**: DO NOT stay in a thinking loop. Analyze, then ACT. Your goal is to progress, not to perfect the plan indefinitely.\n"
        "**Format**: THOUGHT: (Brief analysis and next action) -> TOOL_CALL: {JSON} OR FINAL ANSWER: (Full data)."
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

    async def analyze_intent(self) -> dict:
        """Evalúa la intención resolviendo el contexto y la inyecta al Gatekeeper."""
    
        # 1. Recuperar historial y aplanarlo
        raw_history = await get_user_context(limit=2, telegram_id=self.telegram_id)
        history_text = "No history."
    
        if raw_history and isinstance(raw_history, list):
            history_lines = []
            for msg in raw_history:
                role = "Bot" if msg.get("role") == "assistant" else "User"
                content = msg.get("content", "").replace("\n", " ")
                history_lines.append(f"[{role}]: {content}")
            history_text = "\n".join(history_lines)

        # ¡NUEVO! Guardamos el historial en la clase para que Pepe lo use después
        self.history_text = history_text

        # 2. Obtener el prompt completamente formateado con los datos inyectados
        gatekeeper_prompt = get_gatekeeper_context(history=history_text, user_petition=self.original_message)
    
        # 3. Enviarlo al LLM (Qwen 2.5 Coder)
        # Al ponerlo en "user", forzamos a que el modelo responda inmediatamente al comando.
        messages = [
            {"role": "user", "content": gatekeeper_prompt}
        ]
    
        raw_response = await call_openai_standard(messages=messages, temperature=0.5, model=self.pepemodel)
    
        # 4. Extraer el JSON
        # 4. Extraer el JSON
        json_match = re.search(r"\{.*\}", raw_response, re.DOTALL)
        if json_match:
            try:
                intent_data = json.loads(json_match.group(0))
            
                # --- NUEVO FAILSAFE PROGRAMÁTICO ---
                # Si el dominio es técnico, SIEMPRE requiere información, sin importar qué diga el LLM.
                technical_domains = ["PRODUCTS", "SUPPLIERS", "CUSTOMERS", "ANALYTICS"]
                if intent_data.get("domain") in technical_domains:
                    intent_data["requires_info"] = True
                # -----------------------------------
            
                return intent_data
            except json.JSONDecodeError:
                pass
            
        # Fallback de seguridad
        return {
            "is_valid": True, 
            "requires_info": True,
            "domain": "SYSTEM", 
            "optimized_query": "No se pudo entender la peticion del usuario", 
            "reject_reason": None
        }

    async def generate_pepe_rejection(self,reject_reason: str) -> str:
        """Genera una respuesta de Pepe cuando la petición es rechazada."""
        prompt = [
            {"role": "system", "content": get_pepe_analyst_context(language=self.detected_lang,original_msg=reject_reason,gathered_data_from_phase_1="NO DATA")},
            {"role": "user", "content": "El usuario preguntó algo fuera de lugar. Como Pepe, dile amablemente que solo puedes ayudarle con temas del negocio, ventas, inventario, etc. Usa un emoji. FINAL ANSWER:"}
        ]
        response = await call_openai_standard(messages=prompt, temperature= 0.7,model=self.qwenmodel)
    
        final_text = re.split(r"FINAL\s*ANSWER:?", response, flags=re.IGNORECASE)[-1].strip()
        await finalize_storage(self.telegram_id, self.original_message, final_text)
        return final_text

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
                raw_json_string = json_match.group(0)
                print(f"\n--- RAW JSON FROM LLM ---\n{raw_json_string}\n-------------------------") # Añade esto
                try:
                    return {"type": "tool", "data": json.loads(raw_json_string)}
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
            stop_words = ["OBSERVATION:", "### OBSERVATION", "\nObservation:", "**OBSERVATION**"]
            raw_content = await call_openai_standard(prepared_msgs, stop_sequences=stop_words, temperature=0.1,model=self.pepemodel)
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
                        f"**OBSERVATION**: \n"
                        f"{observation}\n\n"
                        "### CRITICAL SYSTEM DIRECTIVE ###\n"
                        "Do NOT call 'search_system_context' again. "
                        "Read the tools provided in the observation above. "
                        "Extract the required arguments from the user's petition, pick the correct tool, and CALL IT now."
                    )
                    self.messages.append({"role": "user", "content": rag_content})
                else:
                    self.messages.append({"role": "user", "content": f"**OBSERVATION**: {observation}"})
                continue

            elif parsed["type"] == "final":
                final_text = parsed["data"]
                if not self.requires_info:
                    final_text += f"\nHISTORY CHAT TO COMPLETE THE ANSWE\n {self.history_text}"
                    print(f"\n Texto final: {final_text}\n")
                final_text_origin_language = await self._translate_to_pepe(final_answer=final_text)
                print(f"\n=== FINAL TEXT TO THE USER===\n{final_text_origin_language}")
                await finalize_storage(self.telegram_id, self.original_message, final_text_origin_language)
                yield final_text_origin_language
                
                return

            else: 
                fallback_text = parsed["data"]
                translated_fallback = await self._translate_to_pepe(fallback_text)
                print(f"\n=== FALLBACK TRANSLATED ===\n{translated_fallback}")
                await finalize_storage(self.telegram_id, self.original_message, translated_fallback)
                yield translated_fallback

                return

    async def _translate_to_pepe(self, final_answer: str) -> str:
        print(f"Mensaje original:{self.original_message}, Informacion dada:{final_answer}")
        
        user_prompt = (
            f"The user said: {self.original_message}\n\n"
            f"TECHNICAL_REPORT to present:\n{final_answer}\n\n"
            "INSTRUCTION: If the report contains data, lists, or help menus, EXPLAIN ALL OF THEM without omitting anything. "
            "If the report says 'Pure conversational intent', just reply naturally to the user based on the CHAT_HISTORY.\n"
            f"FINAL ANSWER LANGUAGE:{self.detected_lang} \n"
            "ONLY RETURN THE **FINAL ANSWER**:"
        )

        translation_prompt = [
            {"role": "system", "content": get_pepe_analyst_context(
                language=self.detected_lang,
                original_msg=self.original_message,
                gathered_data_from_phase_1=final_answer,
                history=self.history_text                
            )},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await call_openai_standard(translation_prompt, temperature=0.7,model=self.pepemodel)
        final_response = self._parse_response(response)
        
        if final_response["type"] == "final":
            return final_response["data"]
        return response.replace("**FINAL ANSWER**:", "").strip()
    
async def query_ai(message: str, telegram_id: int) -> AsyncGenerator[str, None]:
    agent = ReActAgent(telegram_id, message)
    
    yield "🛡️ *Analizando intención...*"
    
    # FASE 0: Gatekeeper con Contexto
    intent_data = await agent.analyze_intent()
    print(f"\n=== INTENT DATA ===\n{json.dumps(intent_data, indent=2)}")
    
    # Si la petición es rechazada
    if not intent_data.get("is_valid", True):
        rejection_msg = await agent.generate_pepe_rejection(intent_data.get("reject_reason", "Off-topic"))
        yield rejection_msg
        return

    # FASE 1: Inicializar Agente ReAct
    optimized_query = intent_data.get("optimized_query", message)
    domain = intent_data.get("domain", "SYSTEM") 
    time_args = intent_data.get("time_arguments") # <--- Obtenemos el diccionario JSON
    
    agent.requires_info = intent_data.get("requires_info", True)
    agent.requires_analysis = intent_data.get("requires_analysis", False)

    # --- INYECCIÓN DEL TIEMPO AL AGENTE ---
    if time_args:
        # Lo convertimos a string JSON bonito para que el agente lo copie fácil
        time_str = f"\n**READY-TO-USE TIME ARGUMENTS**: {json.dumps(time_args)}\n(Merge these exact keys into your TOOL_CALL arguments if the tool requires time)."
    else:
        time_str = ""
    
    agent.original_message = (
        f"User Request: '{message}'\n"
        f"Contextual Target: '{optimized_query}'\n"
        f"Pre-calculated Domain: [{domain}]"
        f"{time_str}"
    )

    async for chunk in agent.run():
        yield chunk