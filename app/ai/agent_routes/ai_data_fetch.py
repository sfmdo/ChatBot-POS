from typing import AsyncGenerator, Dict, List, Any
import json
import re
from agent_mcp.client import mcp_manager
from mcp.types import TextContent
from app.ai.context_service import get_pepe_analyst_context, get_data_retrieval_context, get_data_planing_context
from app.ai.llm_service import call_openai_standard
from app.ai.ai_tools import _parse_response, json_load
from app.ai.storage_service import finalize_storage # Asegúrate de tener esta importación

class DataFetchReActAgent:
    def __init__(self, clean_intent: str, telegram_id: int, language="Spanish"):
        self.clean_intent = clean_intent
        self.telegram_id = telegram_id
        self.detected_lang = language
        self.max_steps = 10
        self.pepemodel = 1
        self.plan_data = {} 
        self.messages = []
        self.last_action = ""

    async def generate_plan(self) -> bool:
        """
        FASE 0.5: TECHNICAL ARCHITECT
        Diseña la estrategia técnica basada en la intención limpia y el resumen del historial.
        """
        print(f"\n{'='*30} [PHASE 0.5: PLANNING] {'='*30}")

        planning_instructions = get_data_planing_context()
    
        user_content = (
            f"CLEAN INTENT: {self.clean_intent}\n"
            "Give me the **FINAL ANSWER**:{json}"
        )   
        print(f"[PLANNING INPUT]:\n{user_content}")

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

        print(f"\n[ARCHITECT RAW RESPONSE]:\n{repr(raw_response)}")

        if not raw_response:
            print("Error: La IA no devolvió ninguna respuesta en la fase de planeación.")
            return False

        # 4. Parseo del FINAL ANSWER
        parsed = _parse_response(content=raw_response)
    
        if parsed["type"] == "final":
            json_raw = parsed["data"]
            print(f"Informacion parseada: {parsed["data"]}")
            # Extraemos el bloque JSON del texto
            json_match = re.search(r"\{.*\}", json_raw, re.DOTALL)
        
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                    self.plan_data = data
                    self.domain = data.get("domain", "ANALYTICS")
                    self.steps = data.get("step_by_step_plan", [])
                    self.time_args = data.get("time_arguments")
            
                    print(f"\n[PLAN GENERATED]: Domain={self.domain} | Steps={len(self.steps)}")
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
        print(f"\n{'='*30} [PHASE 1: AGENT INIT] {'='*30}")
        identity_context = get_data_retrieval_context()
        
        plan_str = "\n".join(self.plan_data.get("step_by_step_plan", []))
        time_args = json.dumps(self.plan_data.get("time_arguments", {}))
        domain = self.plan_data.get("domain", "ANALYTICS")

        directive = (
            f"TARGET DOMAIN: {domain}\n"
            f"EXECUTION PLAN:\n{plan_str}\n"
            f"TIME CONSTRAINTS: {time_args}\n"
        )

        print(f"[KERNEL DIRECTIVE]:\n{directive}")

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
        print(f"\n[TOOL CALL]: {name} | ARGS: {args}")
        if name in ["fetch_chat_history", "search_system_context"]:
            args["telegram_id"] = self.telegram_id

        current_action = f"{name}-{json.dumps(args, sort_keys=True)}"
        if current_action == self.last_action:
            print("[TOOL WARNING]: Duplicate call detected")
            return "SYSTEM: Duplicate tool call. Use previous observation or change arguments."
        
        self.last_action = current_action

        if not mcp_manager.session:
            print("[MCP ERROR]: No active session")
            return "Error: MCP session is not active."

        try:
            result = await mcp_manager.session.call_tool(name, arguments=args)
            obs = "\n".join([c.text for c in result.content if isinstance(c, TextContent)])
            print(f"[OBSERVATION]: {len(obs)}")
            print(f"[DATA PREVIEW]: {obs[:200]}...")
            if obs== "[]" or obs == "" or "No records" in obs:
                return f"OBSERVATION: Empty Result. No data was found for {args}. CRITICAL: This means the entity does not exist in the database. DO NOT retry this search. Provide your FINAL ANSWER informing the user."
            return obs[:30000]
        except Exception as e:
            print(f"[TOOL ERROR]: {str(e)}")
            return f"Error executing tool: {str(e)}"

    async def run(self) -> AsyncGenerator[str, None]:
        """Bucle principal ReAct."""
        
        yield "🏗️ *Diseñando estrategia de datos...*"
        if not await self.generate_plan():
            yield "❌ No pude diseñar un plan de ejecución."
            return

        await self.initialize_agent()

        print(f"\n{'='*30} [PHASE 2: REACT LOOP] {'='*30}")

        for step in range(1, self.max_steps + 1):
            print(f"\n--- [STEP {step}] ---")
            prepared_msgs = self.messages + [{"role": "system", "content": self._build_step_nudge(step)}]
            
            raw_content = await call_openai_standard(
                prepared_msgs, 
                stop_sequences=["\n**OBSERVATION**", "OBSERVATION:"], 
                temperature=0.0, 
                model=self.pepemodel
            )
            
            if not raw_content: break

            print(f"[AGENT THOUGHT]:\n{raw_content}")

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
                print(f"Obervacion: {observation}")
                self.messages.append({"role": "user", "content": f"**OBSERVATION**: {observation}"})
                continue

            elif parsed["type"] == "final":
                print(f"[PLAN COMPLETED] at step {step}")
                yield "📊 *Formateando reporte...*"
                final_technical_report = parsed["data"]
                
                pepe_response = await self._translate_to_pepe(final_technical_report)
                
                print(f"[FINALIZE]: Guardando en Storage...")
                await finalize_storage(self.telegram_id, self.clean_intent, pepe_response)
                
                yield pepe_response
                return

        yield "⚠️ El análisis tomó demasiado tiempo y fue truncado."

    async def _translate_to_pepe(self, technical_report: str) -> str:
        """Fase 2: Traducción al lenguaje ejecutivo de Pepe."""

        print(f"\n{'='*30} [PHASE 3: PEPE ANALYST] {'='*30}")
        print(f"[REPORT TO ANALYZE]: {technical_report[:500]}...")

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
        
        print(f"[PEPE RAW RESPONSE]:\n{repr(response)}")

        final_text = re.split(r"FINAL\s*ANSWER:?", response, flags=re.IGNORECASE)[-1].strip()  # type: ignore
        return final_text

    def _clean_thought_for_user(self, thought: str) -> str:
        """Limpia el pensamiento técnico para mostrarlo en Telegram."""
        text = thought.replace("THOUGHT:", "💡").replace("PLANNING:", "📋")
        lines = [line.strip() for line in text.split('\n') if line.strip() and not line.startswith("---")]
        return "\n".join(lines[:2]) # Solo mostrar las primeras 2 líneas de pensamiento

async def run_ai_data_fetch(clean_intent: str, telegram_id: int, language: str) -> AsyncGenerator[str, None]:
    """
    Orquesta el flujo completo de DATA_FETCH: 
    Planning -> ReAct Execution -> Pepe Analysis.
    """
    agent = DataFetchReActAgent(
        clean_intent=clean_intent, 
        telegram_id=telegram_id, 
        language=language,
    )

    yield "🏗️ *Diseñando estrategia de datos...*"
    plan_success = await agent.generate_plan()
    
    if not plan_success:
        print("[ORCHESTRATOR ERROR]: Planning phase failed.")
        yield "❌ No logré diseñar un plan para obtener esos datos. Por favor, intenta ser más específico."
        return

    async for chunk in agent.run():
        yield chunk
    
    print(f"[DATA_FETCH FLOW FINISHED]")