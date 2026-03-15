# app/services/chatbot_users_api.py
from app.services.api_client import get_http_client
from urllib.parse import quote
import logging

logger = logging.getLogger(__name__)

def _fetch_data(endpoint: str):
    """
    Función ayudante para hacer peticiones GET a la API de usuarios.
    Maneja el re-login automático (401) y devuelve errores controlados (403, 404).
    """
    try:
        with get_http_client() as client:
            response = client.get(endpoint)
            
            if response.status_code == 401:
                logger.warning(f"Token expirado en {endpoint}. Reintentando login...")
                with get_http_client(force_relogin=True) as new_client:
                    response = new_client.get(endpoint)
            
            if response.status_code in [403, 404]:
                logger.warning(f"Respuesta {response.status_code} en {endpoint}: {response.text}")
                return response.json()
                
            response.raise_for_status()
            return response.json()
            
    except Exception as e:
        logger.error(f"Error crítico en la petición GET a {endpoint}: {e}")
        return {"error": f"Error de conexión interno: {str(e)}"}


def get_all_chatbot_users():
    """
    Obtiene la lista de todos los usuarios registrados en el bot.
    Retorna una lista de diccionarios o un diccionario con error.
    """
    return _fetch_data("/chatbotusers/")

def get_chatbot_user(mobile_number: str):
    """
    Obtiene los detalles de un usuario específico por su número de teléfono.
    """
    safe_number = quote(mobile_number)
    return _fetch_data(f"/chatbotusers/{safe_number}/")

def obtener_telefonos_autorizados():
    """
    Extrae SOLO la lista de números permitidos para usar el bot de Telegram.
    Se conecta directamente en app/bot/handlers.py durante el comando /start.
    """
    respuesta = get_all_chatbot_users()
    
    if isinstance(respuesta, list):
        return [user.get("mobile_number") for user in respuesta if "mobile_number" in user]
    
    logger.error(f"Falló la extracción de números autorizados: {respuesta}")
    
    return []