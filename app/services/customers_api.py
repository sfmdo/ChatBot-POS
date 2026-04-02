import asyncio
from typing import List, Dict, Any, Optional, Union
from app.services.api_client import get_http_client
import logging

logger = logging.getLogger(__name__)

def _fetch_data(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Union[List[Any], Dict[str, Any]]:
    """
    Internal helper function for secure GET requests.
    """
    try:
        with get_http_client() as client:
            response = client.get(endpoint, params=params)
            
            if response.status_code == 401:
                with get_http_client(force_relogin=True) as new_client:
                    response = new_client.get(endpoint, params=params)
                    
            if response.status_code == 403:
                return {"error": "Permission denied. Current token lacks ADMIN or OWNER privileges."}
            
            if response.status_code == 404:
                return {"error": "Customer or history not found."}
                
            response.raise_for_status()
            return response.json()
            
    except Exception as e:
        logger.error(f"Error in GET {endpoint}: {e}")
        return {"error": f"Connection error: {str(e)}"}

# ! CUSTOMER MANAGEMENT

async def get_all_customers() -> List[Dict[str, Any]]:
    """Retrieves the complete list of customers and their statuses (Frequent/Points)."""
    data = await asyncio.to_thread(_fetch_data, "/customers/")
    return data if isinstance(data, list) else []

async def get_customer_detail(customer_id: int) -> Dict[str, Any]:
    """Retrieves the detailed profile of a customer by their ID."""
    data = await asyncio.to_thread(_fetch_data, f"/customers/{customer_id}/")
    return data if isinstance(data, dict) else {"error": "Unexpected response"}

# ! LOYALTY AND POINTS

async def get_customer_points_history(customer_id: int) -> List[Dict[str, Any]]:
    """Retrieves the points ledger (Earned/Redeemed)."""
    data = await asyncio.to_thread(_fetch_data, f"/customers/{customer_id}/history/")
    return data if isinstance(data, list) else []

# ! STORE CREDIT

async def get_customer_credit_history(customer_id: int) -> List[Dict[str, Any]]:
    """Retrieves the history of charges and payments to the customer's credit."""
    data = await asyncio.to_thread(_fetch_data, f"/customers/{customer_id}/credit-history/")
    return data if isinstance(data, list) else []