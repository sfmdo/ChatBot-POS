import os
import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)


_ACCESS_TOKEN: Optional[str] = None
def login_bot():
    """Consume el endpoint de login de Django para obtener el JWT."""
    global _ACCESS_TOKEN
    
    base_url = os.getenv("POS_API_URL") or ""
    if not base_url:
        raise ValueError("POS_API_URL no está configurada en las variables de entorno.")
    
    email = os.getenv("BOT_API_EMAIL")
    if not email:
        raise ValueError("BOT_API_EMAIL no está configurada en las variables de entorno.")
    
    password = os.getenv("BOT_API_PASSWORD")
    if not password:
        raise ValueError("BOT_API_PASSWORD no está configurada en las variables de entorno.")
    
    url = f"{base_url}/auth/login/"
    
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(url, json={"email": email, "password": password})
            response.raise_for_status()
            
            datos = response.json()
            _ACCESS_TOKEN = datos.get("access")
            
            logger.info("Bot logueado exitosamente en el POS.")
            return True
            
    except Exception as e:
        logger.error(f"Error al iniciar sesión en el POS: {e}")
        _ACCESS_TOKEN = None
        return False

def get_http_client(force_relogin=False):
    """Devuelve el cliente HTTP configurado con el Token Bearer."""
    global _ACCESS_TOKEN
    
    if not _ACCESS_TOKEN or force_relogin:
        login_bot()
        
    base_url = os.getenv("POS_API_URL")
    if not base_url:
        raise EnvironmentError(
            "CRITICAL ERROR: La variable de entorno 'POS_API_URL' no está definida. "
            "El servidor MCP no puede comunicarse con el backend de Django."
        )
    headers = {}
    
    if _ACCESS_TOKEN:
        headers["Authorization"] = f"Bearer {_ACCESS_TOKEN}"
        
    return httpx.Client(base_url=base_url, headers=headers, timeout=15.0,follow_redirects=True)