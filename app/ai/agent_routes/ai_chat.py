import re
from typing import AsyncGenerator
from app.ai.context_service import get_pepe_chat_context
from app.ai.llm_service import call_openai_standard
from app.ai.ai_tools import _parse_response  # Importamos tu parser unificado

class AgentChat:
    def __init__(self, telegram_id: int, user_message: str, language: str = "Spanish"):
        self.telegram_id = telegram_id
        self.user_message = user_message
        self.lang = language
        self.pepemodel = 1  # Pepe-7B

    async def run(self) -> AsyncGenerator[str, None]:
        """
        Orchestrator for the CHAT route.
        """
        response = await self._generate_chat_response()
        
        yield response

    async def _generate_chat_response(self) -> str:
        """
        Calls the LLM and uses the unified parser to extract the final answer.
        """
        system_context = get_pepe_chat_context(language=self.lang)

        messages = [
            {"role": "system", "content": system_context},
            {"role": "user", "content": self.user_message + f"**FINAL ANSWER LANGUAGE**:{self.lang}"}
        ]

        raw_response = await call_openai_standard(
            messages=messages, 
            temperature=0.8, 
            model=self.pepemodel
        )

        if not raw_response:
            return "¡Hola! Soy Pepe, tu analista de Obsidiana POS. ¿En qué puedo apoyarte con tus datos hoy? 📊"

        parsed = _parse_response(content=raw_response)

        if parsed["type"] == "final":
            return parsed["data"]

        return parsed["data"] if "data" in parsed else str(raw_response).strip()