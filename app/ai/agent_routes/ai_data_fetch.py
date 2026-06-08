from typing import AsyncGenerator, Dict, List, Any
import json
import re
from agent_mcp.client import mcp_manager
from mcp.types import TextContent
from app.ai.context_service import get_pepe_analyst_context, get_data_retrieval_context, get_data_planing_context
from app.ai.llm_service import call_openai_standard
from app.ai.ai_tools import _parse_response
from app.ai.storage_service import finalize_storage # Asegúrate de tener esta importación

class DataFetchReActAgent:
    def __init__(self, clean_intent: str,log_summary: str, telegram_id: int, language="Spanish",history_summary = ""):
        self.clean_intent = clean_intent
        self.history_summary = history_summary
        self.telegram_id = telegram_id
        self.detected_lang = language
        self.max_steps = 10
        self.pepemodel = 1
        self.plan_data = {} 
        self.messages = []
        self.last_action = ""
        self.log_summary = log_summary

    async def generate_plan(self) -> bool:
        """
        FASE 0.5: TECHNICAL ARCHITECT
        Diseña la estrategia técnica basada en la intención limpia y el resumen del historial.
        """
        # 1. Obtenemos solo las instrucciones (System Prompt estático)
        planning_instructions = get_data_planing_context()
    
        # 2. Construimos el mensaje del usuario con la data variable
        # self.log_summary viene inyectado desde el Orquestador
        user_content = (
            f"CLEAN INTENT: {self.clean_intent}\n"
            f"BUSINESS LOG SUMMARY: {self.log_summary if hasattr(self, 'log_summary') else 'No context'}"
        )   

        messages = [
            {"role": "system", "content": planning_instructions},
            {"role": "user", "content": user_content}
        ]

        # 3. Llamada al LLM
        raw_response = await call_openai_standard(
            messages=messages, 
            temperature=0.2, 
            model=self.pepemodel
        )

        if not raw_response:
            print("❌ Error: La IA no devolvió ninguna respuesta en la fase de planeación.")
            return False

        # 4. Parseo del FINAL ANSWER
        parsed = _parse_response(content=raw_response)
    
        if parsed["type"] == "final":
            json_raw = parsed["data"]
            # Extraemos el bloque JSON del texto
            json_match = re.search(r"\{.*\}", json_raw, re.DOTALL)
        
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                
                    # Guardamos en variables de instancia para el Obrero (ReAct)
                    self.plan_data = data
                    self.domain = data.get("domain", "ANALYTICS")
                    self.steps = data.get("step_by_step_plan", [])
                    self.time_args = data.get("time_arguments")
            
                    print(f"Plan generado exitosamente para el dominio {self.domain}")
                    return True
                except json.JSONDecodeError:
                    print("Error: El Arquitecto generó un JSON inválido.")
            else:
                print("Error: No se encontró un bloque JSON en la respuesta del Arquitecto.")

        return False

    async def initialize_agent(self):
        """
        FASE 1: PREPARAR EL REACT AGENT (OBRERO)
        Inyecta el plan y el contexto de recuperación.
        """
        identity_context = get_data_retrieval_context()
        
        plan_str = "\n".join(self.plan_data.get("step_by_step_plan", []))
        time_args = json.dumps(self.plan_data.get("time_arguments", {}))
        domain = self.plan_data.get("domain", "ANALYTICS")

        directive = (
            f"TARGET DOMAIN: {domain}\n"
            f"EXECUTION PLAN:\n{plan_str}\n"
            f"TIME CONSTRAINTS: {time_args}\n"
            f"CLEAN USER INTENT: {self.clean_intent}\n"
        )

        self.messages = [
            {"role": "system", "content": identity_context},
            {"role": "user", "content": directive}
        ]

    def _build_step_nudge(self, step: int) -> str:
        """Instrucciones de control para el bucle ReAct."""
        instruction = f"\n\n--- [KERNEL STEP {step}/{self.max_steps}] ---\n"
        
        if step == self.max_steps:
            instruction += "CRITICAL: Last attempt. Summarize data and output FINAL ANSWER now."
        elif step == 1:
            instruction += "Start with Step 1 of the EXECUTION PLAN. Use search_system_context if you need tool definitions."
        else:
            instruction += "Analyze last observation. If data is complete, output FINAL ANSWER. If not, proceed to next step in plan."
        
        return instruction

    async def _execute_tool(self, name: str, args: Dict[str, Any]) -> str:
        """Ejecución vía MCP."""
        if name in ["fetch_chat_history", "search_system_context"]:
            args["telegram_id"] = self.telegram_id

        current_action = f"{name}-{json.dumps(args, sort_keys=True)}"
        if current_action == self.last_action:
            return "SYSTEM: Duplicate tool call. Use previous observation or change arguments."
        
        self.last_action = current_action

        if not mcp_manager.session:
            return "Error: MCP session is not active."

        try:
            result = await mcp_manager.session.call_tool(name, arguments=args)
            obs = "\n".join([c.text for c in result.content if isinstance(c, TextContent)])
            return obs[:30000]
        except Exception as e:
            return f"Error executing tool: {str(e)}"

    async def run(self) -> AsyncGenerator[str, None]:
        """Bucle principal ReAct."""
        
        yield "🏗️ *Diseñando estrategia de datos...*"
        if not await self.generate_plan():
            yield "❌ No pude diseñar un plan de ejecución."
            return

        await self.initialize_agent()

        for step in range(1, self.max_steps + 1):
            prepared_msgs = self.messages + [{"role": "system", "content": self._build_step_nudge(step)}]
            
            raw_content = await call_openai_standard(
                prepared_msgs, 
                stop_sequences=["\n**OBSERVATION**", "OBSERVATION:"], 
                temperature=0.0, 
                model=self.pepemodel
            )
            
            if not raw_content: break

            thought = re.split(r"TOOL_CALL|FINAL\s*ANSWER", raw_content, flags=re.IGNORECASE)[0]
            display_thought = self._clean_thought_for_user(thought)
            if display_thought:
                yield f"🧠 *{display_thought}*"

            parsed = _parse_response(content=raw_content)

            if parsed["type"] == "tool":
                tool_name = parsed["data"].get("tool")
                tool_args = parsed["data"].get("arguments", {})

                self.messages.append({"role": "assistant", "content": raw_content})
                
                observation = await self._execute_tool(tool_name, tool_args)
                self.messages.append({"role": "user", "content": f"**OBSERVATION**: {observation}"})
                continue

            elif parsed["type"] == "final":
                yield "📊 *Formateando reporte...*"
                final_technical_report = parsed["data"]
                
                pepe_response = await self._translate_to_pepe(final_technical_report)
                
                await finalize_storage(self.telegram_id, self.clean_intent, pepe_response)
                
                yield pepe_response
                return

        yield "⚠️ El análisis tomó demasiado tiempo y fue truncado."

    async def _translate_to_pepe(self, technical_report: str) -> str:
        """Fase 2: Traducción al lenguaje ejecutivo de Pepe."""
        system_context = get_pepe_analyst_context(
            language=self.detected_lang,
            user_request=self.clean_intent,
            technical_info=technical_report
        )
        
        prompt = [
            {"role": "system", "content": system_context},
            {"role": "user", "content": f"Summarize this technical data for the user: {technical_report}"}
        ]
        
        response = await call_openai_standard(prompt, temperature=0.7, model=self.pepemodel)
        

        final_text = re.split(r"FINAL\s*ANSWER:?", response, flags=re.IGNORECASE)[-1].strip()  # type: ignore
        return final_text

    def _clean_thought_for_user(self, thought: str) -> str:
        """Limpia el pensamiento técnico para mostrarlo en Telegram."""
        text = thought.replace("THOUGHT:", "💡").replace("PLANNING:", "📋")
        lines = [line.strip() for line in text.split('\n') if line.strip() and not line.startswith("---")]
        return "\n".join(lines[:2]) # Solo mostrar las primeras 2 líneas de pensamiento

async def run_ai_data_fetch(clean_intent: str, telegram_id: int, language: str, history_summary: str, log_summary: str) -> AsyncGenerator[str, None]:
    """
    Orquesta el flujo completo de DATA_FETCH: 
    Planning -> ReAct Execution -> Pepe Analysis.
    """
    agent = DataFetchReActAgent(
        log_summary=log_summary,
        clean_intent=clean_intent, 
        telegram_id=telegram_id, 
        language=language,
        history_summary=history_summary,
    )

    yield "🏗️ *Diseñando estrategia de datos...*"
    plan_success = await agent.generate_plan()
    
    if not plan_success:
        yield "❌ No logré diseñar un plan para obtener esos datos. Por favor, intenta ser más específico."
        return

    async for chunk in agent.run():
        yield chunk