# app/services/customers_api.py
from typing import List, Dict, Any, Optional, Union
from app.services.api_client import get_http_client
import logging

logger = logging.getLogger(__name__)

def _fetch_data(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Union[List[Any], Dict[str, Any]]:
    """
    Función interna para peticiones GET seguras.
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
                return {"error": "Cliente o historial no encontrado."}
                
            response.raise_for_status()
            return response.json()
            
    except Exception as e:
        logger.error(f"Error en GET {endpoint}: {e}")
        return {"error": f"Error de conexión: {str(e)}"}

# ! GESTIÓN DE CLIENTES

def get_all_customers() -> List[Dict[str, Any]]:
    """Obtiene la lista completa de clientes y sus estatus (Frecuente/Puntos)."""
    data = _fetch_data("/customers/")
    return data if isinstance(data, list) else []

def get_customer_detail(customer_id: int) -> Dict[str, Any]:
    """Obtiene el perfil detallado de un cliente por su ID."""
    data = _fetch_data(f"/customers/{customer_id}/")
    return data if isinstance(data, dict) else {"error": "Respuesta inesperada"}

# ! LEALTAD Y PUNTOS

def get_customer_points_history(customer_id: int) -> List[Dict[str, Any]]:
    """Obtiene el libro mayor de puntos (Ganados/Canjeados)."""
    data = _fetch_data(f"/customers/{customer_id}/history/")
    return data if isinstance(data, list) else []

# ! CRÉDITO DE TIENDA

def get_customer_credit_history(customer_id: int) -> List[Dict[str, Any]]:
    """Obtiene el historial de cargos y abonos al crédito del cliente."""
    data = _fetch_data(f"/customers/{customer_id}/credit-history/")
    return data if isinstance(data, list) else []