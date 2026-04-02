import asyncio
from app.services.api_client import get_http_client
import logging

logger = logging.getLogger(__name__)

def _fetch_data(endpoint: str):
    """
    Helper function to make GET requests to the Orders API.
    Handles automatic re-login (401) and returns controlled errors (404).
    """
    try:
        with get_http_client() as client:
            response = client.get(endpoint)
            
            if response.status_code == 401:
                logger.warning(f"Token expired at {endpoint}. Retrying login...")
                with get_http_client(force_relogin=True) as new_client:
                    response = new_client.get(endpoint)
            
            if response.status_code == 403:
                return {"error": "Permission denied. Current token lacks ADMIN or OWNER privileges to view providers."}
            
            if response.status_code == 404:
                logger.warning(f"Order not found at {endpoint}")
                return response.json() if response.text else {"error": "Order not found."}
                
            response.raise_for_status()
            return response.json()
            
    except Exception as e:
        logger.error(f"Critical error in GET request to {endpoint}: {e}")
        return {"error": f"Internal connection error: {str(e)}"}

async def get_order_detail(order_id: int):
    """
    Searches exactly by the numeric ID of the order.
    Example: get_order_detail(6)
    """
    return await asyncio.to_thread(_fetch_data, f"/orders/{order_id}/")

async def search_recent_orders(ticket_folio=None, status=None, limit=10):
    """
    Since the API doesn't filter natively, we download the orders and filter them here
    so the AI can search by folio (e.g., 'AC6D6A89') or status ('PENDING').
    """
    all_orders = await asyncio.to_thread(_fetch_data, "/orders/")
    
    # Handle the case where the API returns an error dictionary instead of a list
    if isinstance(all_orders, dict) and "error" in all_orders:
        return all_orders
    
    if not isinstance(all_orders, list):
        logger.error(f"Expected a list but received: {type(all_orders)}")
        return all_orders

    results = all_orders

    if ticket_folio:
        results = [order for order in results if order.get("ticket_folio") == ticket_folio]
        
    if status:
        results = [order for order in results if order.get("status") == status.upper()]

    return results[:limit]