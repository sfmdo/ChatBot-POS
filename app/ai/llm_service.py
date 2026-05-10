import os
import httpx
from dotenv import load_dotenv
load_dotenv()

LLM_URL1 = (
    os.getenv('LLM1_BASE_URL') or 
    'http://localhost:11434' 
)

LLM_URL2 = (
    os.getenv('LLM2_BASE_URL') or 
    'http://localhost:11434' 
)
BASE_URL1 = LLM_URL1.rstrip('/')
BASE_URL2 = LLM_URL2.rstrip('/')

MODEL1_NAME = "pepepos"
MODEL2_NAME = "qwen2.5_7b-instruct"

API_KEY = (
    os.getenv('OPENAI_API_KEY') or 
    os.getenv('API_KEY') or 
    'vllm-no-key-needed'
)

async def call_openai_standard(
    messages: list, 
    model: int,  
    temperature: float = 0.1, 
    stop_sequences: list | None = None
):
    """
    Realiza una petición a la API (Ollama/OpenAI).
    Ahora permite pasar el 'model' directamente en la llamada.
    """

    print(f"\nModel = {model}\n")

    if model == 1:
        url = f"{BASE_URL1}/v1/chat/completions"
    elif model == 2:
        url = f"{BASE_URL2}/v1/chat/completions"
    else:
        url = 'NO URL' 
    
    if model == 1:
        model_name = MODEL1_NAME
    if model == 2:
        model_name = MODEL2_NAME
    else:
        model_name = "pepepos"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model_name, 
        "messages": messages,
        "stream": False,
        "temperature": temperature,  
    }
    
    if stop_sequences:
        payload["stop"] = stop_sequences
    
    async with httpx.AsyncClient(timeout=620.0, follow_redirects=True) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        data = response.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()