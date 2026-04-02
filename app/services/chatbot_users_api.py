import asyncio
from app.services.api_client import get_http_client
from urllib.parse import quote
import logging

logger = logging.getLogger(__name__)

def _fetch_data(endpoint: str):
    """
    Helper function to make GET requests to the users API.
    Handles automatic re-login (401) and returns controlled errors (403, 404).
    """
    try:
        with get_http_client() as client:
            response = client.get(endpoint)
            
            if response.status_code == 401:
                logger.warning(f"Token expired at {endpoint}. Retrying login...")
                with get_http_client(force_relogin=True) as new_client:
                    response = new_client.get(endpoint)
            
            if response.status_code in [403, 404]:
                logger.warning(f"Response {response.status_code} at {endpoint}: {response.text}")
                return response.json()
                
            response.raise_for_status()
            return response.json()
            
    except Exception as e:
        logger.error(f"Critical error in GET request to {endpoint}: {e}")
        return {"error": f"Internal connection error: {str(e)}"}


async def get_all_chatbot_users():
    """
    Gets the list of all registered users in the bot.
    Returns a list of dictionaries or a dictionary with an error.
    """
    return await asyncio.to_thread(_fetch_data, "/chatbotusers/")

async def get_chatbot_user(mobile_number: str):
    """
    Gets the details of a specific user by their phone number.
    """
    safe_number = quote(mobile_number)
    return await asyncio.to_thread(_fetch_data, f"/chatbotusers/{safe_number}/")

async def get_authorized_phones():
    """
    Extracts ONLY the list of allowed numbers to use the Telegram bot.
    Connects directly in app/bot/handlers.py during the /start command.
    """
    response = await get_all_chatbot_users()
    
    if isinstance(response, list):
        return [user.get("mobile_number") for user in response if "mobile_number" in user]
    
    logger.error(f"Failed to extract authorized numbers: {response}")
    
    return []