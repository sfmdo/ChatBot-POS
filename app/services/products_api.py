# app/services/products_api.py
from typing import Optional, Dict, List, Any, Union
from app.services.api_client import get_http_client
import logging

logger = logging.getLogger(__name__)

def _fetch_data(endpoint: str, params: Optional[Dict[Any, Any]] = None) -> Union[List[Any], Dict[Any, Any]]:
    """
    Función interna para peticiones GET. Maneja autenticación y errores.
    """
    try:
        with get_http_client() as client:
            response = client.get(endpoint, params=params)
            
            if response.status_code == 401:
                with get_http_client(force_relogin=True) as new_client:
                    response = new_client.get(endpoint, params=params)
            
            if response.status_code == 403:
                return {"error": "Permiso denegado. El token actual no tiene privilegios de ADMIN u OWNER para ver proveedores."}
            
            if response.status_code == 404:
                return {"error": "Recurso no encontrado."}
                
            response.raise_for_status()
            return response.json()
            
    except Exception as e:
        logger.error(f"Error en GET {endpoint}: {e}")
        return {"error": str(e)}

def get_all_products():
    """
    Obtiene el catálogo completo de productos, incluyendo stock disponible
    y precios finales con impuestos calculados.
    """
    return _fetch_data("/products/")

def get_product_by_id(product_id: int):
    """
    Obtiene el detalle de un producto específico por su ID.
    """
    return _fetch_data(f"/products/{product_id}/")

def search_product_by_sku(sku: str):
    """
    Busca un producto por su SKU en el catálogo local.
    """
    products = get_all_products()
    if isinstance(products, list):
        for p in products:
            if p.get("sku") == sku:
                return p
    return {"error": "Producto no encontrado por SKU."}

def get_all_promotions():
    """
    Lista todas las promociones registradas en el sistema.
    """
    return _fetch_data("/promotions/")

def get_promotions_by_product(product_id: int):
    """
    Obtiene las promociones activas o programadas para un producto específico.
    Utiliza el filtro de API: /promotions/?product={id}
    """
    return _fetch_data("/promotions/", params={"product": product_id})