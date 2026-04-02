import os
import httpx

OLLAMA_URL = os.getenv('OLLAMA_BASE_URL')
MODEL = os.getenv('OLLAMA_MODEL')

async def call_ollama(messages: list):
    async with httpx.AsyncClient(timeout=150.0) as client:
        response = await client.post(f"{OLLAMA_URL}/api/chat", json={
            "model": MODEL,
            "messages": messages,
            "stream": False,
        })
        response.raise_for_status()
        return response.json().get("message", {}).get("content", "").strip()