import asyncio
from typing import Optional, Dict, List, Any, Union
from app.services.api_client import get_http_client
import logging

logger = logging.getLogger(__name__)

def _fetch_data(endpoint: str, params: Optional[Dict[Any, Any]] = None) -> Union[List[Any], Dict[Any, Any]]:
    """
    Internal function for GET requests. Handles authentication and errors.
    """
    try:
        with get_http_client() as client:
            response = client.get(endpoint, params=params)
            
            if response.status_code == 401:
                with get_http_client(force_relogin=True) as new_client:
                    response = new_client.get(endpoint, params=params)
            
            if response.status_code == 403:
                return {"error": "Permission denied. Current token lacks ADMIN or OWNER privileges to view providers."}
            
            if response.status_code == 404:
                return {"error": "Resource not found."}
                
            response.raise_for_status()
            return response.json()
            
    except Exception as e:
        logger.error(f"Error in GET {endpoint}: {e}")
        return {"error": str(e)}

async def get_all_products():
    """
    Retrieves the complete product catalog, including available stock
    and final prices with calculated taxes.
    """
    return await asyncio.to_thread(_fetch_data, "/products/")

async def get_product_by_id(product_id: int):
    """
    Retrieves the details of a specific product by its ID.
    """
    return await asyncio.to_thread(_fetch_data, f"/products/{product_id}/")

async def search_product_by_sku(sku: str):
    """
    Searches for a product by its SKU in the local catalog.
    """
    products = await get_all_products()
    
    if isinstance(products, list):
        for p in products:
            if p.get("sku") == sku:
                return p
    return {"error": "Product not found by SKU."}

async def get_all_promotions():
    """
    Lists all promotions registered in the system.
    """
    return await asyncio.to_thread(_fetch_data, "/promotions/")

async def get_promotions_by_product(product_id: int):
    """
    Retrieves active or scheduled promotions for a specific product.
    Uses the API filter: /promotions/?product={id}
    """
    return await asyncio.to_thread(_fetch_data, "/promotions/", params={"product": product_id})