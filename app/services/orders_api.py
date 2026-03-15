# app/services/orders_api.py
from app.services.api_client import get_http_client
import logging

logger = logging.getLogger(__name__)

def _fetch_data(endpoint: str):
    """
    Función ayudante para hacer peticiones GET a la API de Órdenes.
    Maneja el re-login automático (401) y devuelve errores controlados (404).
    """
    try:
        with get_http_client() as client:
            response = client.get(endpoint)
            
            if response.status_code == 401:
                logger.warning(f"Token expirado en {endpoint}. Reintentando login...")
                with get_http_client(force_relogin=True) as new_client:
                    response = new_client.get(endpoint)
            
            if response.status_code == 403:
                return {"error": "Permiso denegado. El token actual no tiene privilegios de ADMIN u OWNER para ver proveedores."}
            
            if response.status_code == 404:
                logger.warning(f"Orden no encontrada en {endpoint}")
                return response.json() if response.text else {"error": "Orden no encontrada."}
                
            response.raise_for_status()
            return response.json()
            
    except Exception as e:
        logger.error(f"Error crítico en la petición GET a {endpoint}: {e}")
        return {"error": f"Error de conexión interno: {str(e)}"}

def get_order_detail(order_id: int):
    """
    Busca exactamente por el ID numérico de la orden.
    Ejemplo: get_order_detail(6)
    """
    return _fetch_data(f"/orders/{order_id}/")

def search_recent_orders(ticket_folio=None, status=None, limit=10):
    """
    Como la API no filtra, descargamos las órdenes y las filtramos aquí mismo
    para que la IA pueda buscar por folio (ej. 'AC6D6A89') o estado ('PENDING').
    """
    todas_las_ordenes = _fetch_data("/orders/")
    
    
    if not isinstance(todas_las_ordenes, list):
        logger.error(f"Se esperaba una lista pero se recibió: {type(todas_las_ordenes)}")
        return todas_las_ordenes

    if isinstance(todas_las_ordenes, dict) and "error" in todas_las_ordenes:
        return todas_las_ordenes
    
    resultados = todas_las_ordenes

    if ticket_folio:
        resultados = [orden for orden in resultados if orden.get("ticket_folio") == ticket_folio]
        
    if status:
        resultados = [orden for orden in resultados if orden.get("status") == status.upper()]

    return resultados[:limit]