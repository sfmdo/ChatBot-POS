import asyncio
from typing import List, Dict, Any, Optional, Union
from app.services.api_client import get_http_client
import logging

logger = logging.getLogger(__name__)

def _fetch_data(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Union[List[Any], Dict[str, Any]]:
    """Internal function for secure GET requests."""
    try:
        with get_http_client() as client:
            response = client.get(endpoint, params=params)
            
            if response.status_code == 401:
                with get_http_client(force_relogin=True) as new_client:
                    response = new_client.get(endpoint, params=params)
            
            if response.status_code == 403:
                return {"error": "Permission denied. Current token lacks ADMIN or OWNER privileges to view suppliers."}
                
            if response.status_code == 404:
                return {"error": "Supplier not found."}
                
            response.raise_for_status()
            return response.json()
            
    except Exception as e:
        logger.error(f"Error in GET {endpoint}: {e}")
        return {"error": f"Connection error: {str(e)}"}

async def get_all_suppliers() -> List[Dict[str, Any]]:
    """Retrieves the complete directory of registered suppliers."""
    data = await asyncio.to_thread(_fetch_data, "/suppliers/")
    return data if isinstance(data, list) else []

async def get_supplier_detail(supplier_id: int) -> Dict[str, Any]:
    """Retrieves the tax and contact details of a specific supplier."""
    data = await asyncio.to_thread(_fetch_data, f"/suppliers/{supplier_id}/")
    return data if isinstance(data, dict) else {"error": "Unexpected response"}