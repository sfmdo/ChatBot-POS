import requests
import json
import os
from dotenv import load_dotenv
load_dotenv()

MODEL = os.getenv('OLLAMA_MODEL')
OLLAMA_URL = os.getenv('OLLAMA_BASE_URL')

analytics_data = {
    "period": "Marzo 2026",
    "total_visits": 15420,
    "conversions": 342,
    "traffic_sources": {
        "organic": 8500,
        "direct": 4120,
        "referrals": 2800
    },
    "sales_by_device": {
        "mobile": 210,
        "desktop": 132
    }
}

user_question = "Basado en estos datos, ¿cuál fue nuestra principal fuente de tráfico? Además, ¿cuántos usuarios vinieron de campañas de Email Marketing?"

full_prompt = f"""
DATOS DE ANALÍTICA:
{json.dumps(analytics_data, indent=2)}

INSTRUCCIONES:
1. Responde a TODAS las partes de la pregunta del usuario.
2. Basa tu respuesta ÚNICAMENTE en los datos provistos.
3. Si te piden un dato que no existe, responde la parte que sí sabes y aclara brevemente qué información falta.

PREGUNTA DEL USUARIO:
{user_question}
"""

payload = {
    "model": MODEL,
    "prompt": full_prompt,
    "stream": False # False para que nos devuelva la respuesta completa de golpe
}

print("Enviando el reporte a Pepe...\n")

try:
    response = requests.post(f"{OLLAMA_URL}/api/generate", json=payload)
    response.raise_for_status()
    
    pepe_response = response.json().get("response", "")
    
    print("REPORTE DE PEPE:")
    print("-" * 50)
    print(pepe_response)
    print("-" * 50)
    
except Exception as e:
    print(f"Error al conectar con la mente de Pepe: {e}")