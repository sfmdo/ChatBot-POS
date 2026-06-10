import json
import re
import logging
from typing import AsyncGenerator
from .llm_service import call_openai_standard
from app.models.database import get_user_context
from app.ai.context_service import get_gatekeeper_context

from app.ai.agent_routes.ai_data_fetch import DataFetchReActAgent 
from app.ai.agent_routes.ai_rejection import AgentRejecter
from app.ai.agent_routes.ai_chat import AgentChat
from app.ai.agent_routes.ai_drill_down import AgentDrillDown

logger = logging.getLogger("pepe.orchestrator")

class PepeOrchestrator:
    def __init__(self, telegram_id: int, message: str):
        self.telegram_id = telegram_id
        self.raw_message = message
        self.pepemodel = 1
        self.detected_lang = "Spanish"

    async def _get_clean_history(self) -> str:
        """
        Obtiene los últimos 2 logs de negocio de la base de datos.
        Este historial ya viene filtrado y limpio (sin basura de chat).
        """
        raw_history = await get_user_context(limit=2, telegram_id=self.telegram_id)
        if not raw_history:
            return "No previous business logs."
        
        history_lines = []
        for msg in raw_history:
            role = "Pepe" if msg.get("role") == "assistant" else "User"
            content = msg.get("content", "").replace("\n", " ")
            history_lines.append(f"[{role}]: {content}")
        print(f"[HISTORY CONTEXT]: {len(history_lines)} logs recuperados.")
        return "\n".join(history_lines)

    async def route_request(self) -> AsyncGenerator[str, None]:
        """
        FASE 0: MASTER ROUTER
        Punto de entrada lógico que decide el destino de la petición.
        """
        yield "🛡️ *Analizando petición...*"
    
        history = await self._get_clean_history()

        print(f"\n{'='*30} [PHASE 0: MASTER ROUTER] {'='*30}")
        print(f"INPUT USER: {self.raw_message}")

        router_prompt = get_gatekeeper_context(history=history, user_petition=self.raw_message)
        response = await call_openai_standard([{"role": "user", "content": router_prompt}], model=self.pepemodel)

        print(f"\n[ROUTER RAW RESPONSE]:\n{repr(response)}") 
        print(f"{'-'*70}")

        if not response:
            logger.error("El Master Router devolvió una respuesta vacía.")
            yield "No pude determinar la intención. ¿Podrías reformular tu pregunta?"
            return
        # 3. Extracción de lógica del JSON
        json_match = re.search(r"\{.*\}", response, re.DOTALL) # type: ignore
        if not json_match:
            logger.warning(f"No se encontró JSON en la respuesta: {response}")
            yield "No pude determinar la intención. ¿Podrías reformular tu pregunta?"
            return

        try:
            route_data = json.loads(json_match.group(0))
        
            route = route_data.get("route", "CHAT")
            clean_intent = route_data.get("clean_intent", self.raw_message)
            log_summary = route_data.get("log_summary", "")
            intent_description = route_data.get("intent_description", "")
            is_valid = route_data.get("is_valid", True)
            reject_reason = route_data.get("reject_reason", "Topic unrelated to POS/Business.")
            self.detected_lang = route_data.get("language", "Spanish")
        
            print(f"[ROUTER PARSED]: Route={route} | Lang={self.detected_lang} | Valid={is_valid}")
            print(f"[CLEAN INTENT]: {clean_intent}")

            if route == "REJECTION" or not is_valid:
                print(f"Dispatching to --> AGENT_REJECTER")
                async for chunk in self._handle_rejection(reason=reject_reason):
                    yield chunk

            elif route == "CHAT":
                print(f" Dispatching to --> AGENT_CHAT")
                async for chunk in self._handle_chat():
                    yield chunk

            elif route == "DRILL_DOWN":
                print(f"Dispatching to --> AGENT_DRILL_DOWN")
                async for chunk in self._handle_drill_down(
                    intent_description=intent_description,
                    clean_intent=clean_intent, 
                    history=history
                ):
                    yield chunk

            elif route == "DATA_FETCH":
                print(f"Dispatching to --> DATA_FETCH_AGENT")
                async for chunk in self._handle_data_fetch(
                    clean_intent=clean_intent, 
                    log_summary=log_summary
                ):
                    yield chunk

            print(f"\n{'='*30} [ROUTING FINISHED] {'='*30}\n")
        except json.JSONDecodeError as je:
            print(f"[JSON ERROR]: Error al decodificar la intención. Detalle: {str(je)}")
            yield "Hubo un error de formato en la comunicación interna."
        except Exception as e:
            print(f"Error Crítico en Orchestrator: {str(e)}")
            yield "Lo siento, tuve un problema interno al organizar tu respuesta técnica."

    async def _handle_rejection(self, reason: str) -> AsyncGenerator[str, None]:
        """Maneja peticiones fuera de contexto."""
        agent = AgentRejecter(
            telegram_id=self.telegram_id,
            user_petition=self.raw_message,
            reject_reason=reason,
            language=self.detected_lang
        )
        async for chunk in agent.run():
            yield chunk 

    async def _handle_chat(self) -> AsyncGenerator[str, None]:
        """Maneja saludos, agradecimientos y despedidas."""
        agent = AgentChat(
            telegram_id=self.telegram_id,
            user_message=self.raw_message,
            language=self.detected_lang
        )
        async for chunk in agent.run():
            yield chunk

    async def _handle_drill_down(self, intent_description: str,clean_intent: str, history: str) -> AsyncGenerator[str, None]:
        """Maneja análisis profundos basados únicamente en el historial."""
        yield "🧠 *Analizando datos previos...*"
        agent = AgentDrillDown(
            telegram_id=self.telegram_id,
            intent_description=intent_description,
            clean_intent=clean_intent,
            history=history,
            language=self.detected_lang
        )
        async for chunk in agent.run():
            yield chunk

    async def _handle_data_fetch(self, clean_intent: str, log_summary: str) -> AsyncGenerator[str, None]:
        """Maneja la extracción de nuevos datos (Planning + ReAct)."""
        agent = DataFetchReActAgent(
            clean_intent=clean_intent, 
            telegram_id=self.telegram_id, 
            language=self.detected_lang
        )

        async for chunk in agent.run():
            yield chunk


async def query_ai(message: str, telegram_id: int) -> AsyncGenerator[str, None]:
    """
    Función de entrada principal llamada por el bot de Telegram.
    Instancia el orquestador y comienza el flujo de respuesta.
    """
    orchestrator = PepeOrchestrator(telegram_id, message)
    
    async for response in orchestrator.route_request():
        yield response