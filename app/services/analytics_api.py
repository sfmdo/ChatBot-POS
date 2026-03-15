from app.services.api_client import get_http_client
from typing import Optional, Dict, List, Any, Union
import logging

logger = logging.getLogger(__name__)

def _fetch_data(endpoint: str, params: Optional[Dict[Any, Any]] = None) -> Union[List[Any], Dict[Any, Any]]:
    """
    Función ayudante para hacer peticiones GET a la API.
    Maneja el re-login automático (401) y devuelve errores controlados (400, 404)
    para que la IA pueda leerlos y entender por qué falló algo.
    """
    if params is None:
        params = {}
        
    try:
        with get_http_client() as client:
            response = client.get(endpoint, params=params)
            

            if response.status_code == 401:
                logger.warning(f"Token expirado en {endpoint}. Reintentando login...")
                with get_http_client(force_relogin=True) as new_client:
                    response = new_client.get(endpoint, params=params)
            if response.status_code == 403:
                return {"error": "Permiso denegado. El token actual no tiene privilegios de ADMIN u OWNER para ver proveedores."}
            
            if response.status_code in [400, 404]:
                logger.warning(f"Respuesta {response.status_code} en {endpoint}: {response.text}")
                return response.json()
                
            response.raise_for_status()
            return response.json()
            
    except Exception as e:
        logger.error(f"Error crítico en la petición a {endpoint}: {e}")
        return {"error": f"Error de conexión interno: {str(e)}"}

def get_sales_summary(start_date=None, end_date=None):
    """Genera un reporte financiero y operativo para un periodo."""
    params = {}
    if start_date: params["start_date"] = start_date
    if end_date: params["end_date"] = end_date
    return _fetch_data("/analytics/sales-summary/", params)

def get_product_ranking(limit=10, criterion="most", start_date=None, end_date=None):
    """Devuelve el ranking de productos más o menos vendidos."""
    params = {"limit": limit, "criterion": criterion.lower()}
    if start_date: params["start_date"] = start_date
    if end_date: params["end_date"] = end_date
    return _fetch_data("/analytics/product-ranking/", params)

def get_low_stock(threshold=None):
    """Identifica productos con inventario bajo."""
    params = {"threshold": threshold} if threshold else {}
    return _fetch_data("/analytics/reports/low-stock/", params)

def get_dead_inventory(reference_date=None):
    """Identifica productos que no han tenido ventas desde una fecha."""
    params = {"reference_date": reference_date} if reference_date else {}
    return _fetch_data("/analytics/reports/dead-inventory/", params)

def get_customer_sales(customer_id, start_date=None, end_date=None):
    """Obtiene el historial de compras y métricas de un cliente específico."""
    params = {"customer_id": customer_id}
    if start_date: params["start_date"] = start_date
    if end_date: params["end_date"] = end_date
    return _fetch_data("/analytics/customer-sales/", params)

def get_sales_velocity(identifier, period_days=30):
    """Calcula la velocidad de venta y estima días de agotamiento."""
    params = {"identifier": identifier, "period_days": period_days}
    return _fetch_data("/analytics/sales-velocity/", params)

def get_inventory_valuation(product_identifier=None):
    """Calcula el valor financiero y ganancias proyectadas del inventario."""
    params = {}
    if product_identifier:
        params["product_identifier"] = product_identifier
    return _fetch_data("/analytics/inventory-valuation/", params)

def get_product_contribution(product_identifier, start_date=None, end_date=None):
    """Calcula el % de las ventas totales generadas por un producto."""
    params = {"product_identifier": product_identifier}
    if start_date: params["start_date"] = start_date
    if end_date: params["end_date"] = end_date
    return _fetch_data("/analytics/product-contribution/", params)