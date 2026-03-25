import requests
import os
from app.models.database import get_user_context, save_message

MODEL = os.getenv('OLLAMA_MODEL')
OLLAMA_URL = os.getenv('OLLAMA_BASE_URL')

def query_ai(message: str, telegram_id: int) -> str:
    if OLLAMA_URL is None:
        return "No se ha configurado la url de ollama"
    
    prompt = get_user_context(telegram_id, limit=10)
    
    prompt.append({"role": "user", "content": message})
    print(prompt)
    
    payload = {
        "model": MODEL,
        "messages": prompt,
        "stream": False # False para que nos devuelva la respuesta completa de golpe
    }
    
    try:
        response = requests.post(f"{OLLAMA_URL}/api/chat", json=payload)
        response.raise_for_status()
        
        data = response.json() 
        
        ai_response = data.get("message", {}).get("content", "").strip()

        tokens = data.get('eval_count', 0)
        nanos = data.get('eval_duration', 0)
        
        if nanos > 0:
            tps = tokens / (nanos / 1e9)
            print(f"Velocidad: {tps:.2f} t/s")

        if ai_response:
            save_message(telegram_id, "user", message)
            save_message(telegram_id, "assistant", ai_response)
            return ai_response
        else:
            return "Lo siento, Pepe se quedó en blanco. ¿Podrías intentar de nuevo?"

    except Exception as e:
        print(f"Error en Ollama: {e}")
        return "Error al conectar con la mente de Pepe"