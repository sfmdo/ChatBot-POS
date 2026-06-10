import re
from typing import AsyncGenerator
from app.ai.context_service import get_pepe_rejection_context
from app.ai.llm_service import call_openai_standard
from app.ai.ai_tools import _parse_response

class AgentRejecter:
    def __init__(self, telegram_id: int, user_petition: str, reject_reason: str, language: str = "Spanish"):
        self.telegram_id = telegram_id
        self.user_petition = user_petition
        self.reject_reason = reject_reason
        self.lang = language
        self.pepemodel = 1 # Pepe-7B

    async def run(self) -> AsyncGenerator[str, None]:
        """
        Orquestador de la ruta REJECTION.
        Explica amablemente por qué no se puede procesar la solicitud 
        y guía al usuario de vuelta al contexto de negocio.
        """
        print(f"\n--- [AGENT: REJECTER START] ---")
        yield "🛡️ *Validando límites del sistema...*" 

        final_response = await self._generate_response()

        print(f"[REJECTER FINISHED]: Response generated")
        print(f"--- [AGENT: REJECTER END] ---\n")
        
        yield final_response

    async def _generate_response(self) -> str:
        """
        Llama al LLM utilizando el prompt especializado de rechazo 
        y extrae la respuesta final usando el parser unificado.
        """
        system_context = get_pepe_rejection_context()

        print(f"\n[REJECTER INPUT]:")
        print(f"   Petition: {self.user_petition}")
        print(f"   Reason: {self.reject_reason}")
        print(f"   Language: {self.lang}")

        user_input = (
            f"Explain why this petition is out of scope.\n"
            f"User Petition: {self.user_petition}\n"
            f"Rejection Reason: {self.reject_reason}\n"
            f"Give me the Final Answer in this Language:{self.lang}"
        )

        messages = [
            {"role": "system", "content": system_context},
            {"role": "user", "content": user_input}
        ]

        raw_response = await call_openai_standard(
            messages=messages, 
            temperature=0.7, 
            model=self.pepemodel
        )

        if not raw_response:
            return "Lo siento, tuve un problema al procesar tu solicitud. Pero estoy listo para ayudarte con tus ventas o inventario. 📊"

        print(f"\n[REJECTER RAW RESPONSE]:\n{repr(raw_response)}")
        parsed = _parse_response(content=raw_response)
        print(f"[REJECTER PARSE TYPE]: {parsed.get('type')}")

        if parsed["type"] == "final":
            return parsed["data"]

        return parsed["data"] if "data" in parsed else "Ocurrio un error, intente otra vez"