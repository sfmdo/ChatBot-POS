import re
import json
from typing import AsyncGenerator
from app.ai.context_service import get_pepe_drill_down_context
from app.ai.llm_service import call_openai_standard
from app.ai.ai_tools import _parse_response
from app.ai.storage_service import finalize_storage

class AgentDrillDown:
    def __init__(self, telegram_id: int, intent_description: str, history: str, language: str = "Spanish"):
        self.telegram_id = telegram_id
        self.intent_description = intent_description 
        self.history = history 
        self.lang = language
        self.pepemodel = 1 # Pepe-7B

    async def run(self) -> AsyncGenerator[str, None]:
        """
        Orquestador de la ruta DRILL_DOWN.
        Realiza un análisis cognitivo del historial sin usar herramientas.
        """
        yield "🧠 *Analizando datos anteriores...*"

        final_analysis = await self._generate_analysis()

        await finalize_storage(self.telegram_id, self.intent_description, final_analysis)

        yield final_analysis

    async def _generate_analysis(self) -> str:
        """
        Llama al LLM para procesar la lógica de análisis profundo sobre el log.
        """
        system_context = get_pepe_drill_down_context(
            history=self.history,
            language=self.lang
        )

        messages = [
            {"role": "system", "content": system_context},
            {"role": "user", "content": f"Based on the history, perform this task: {self.intent_description}, Give me the final answr in {self.lang}"}
        ]

        raw_response = await call_openai_standard(
            messages=messages,
            temperature=0.4, 
            model=self.pepemodel
        )

        if not raw_response:
            return "No logré encontrar los datos suficientes en nuestra conversación previa para ese análisis. ¿Gustas que realicemos una nueva búsqueda? 📊"

        parsed = _parse_response(content=raw_response)

        if parsed["type"] == "final":
            return parsed["data"]
        
        return parsed["data"] if "data" in parsed else str(raw_response).strip()