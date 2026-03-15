# app/services/suppliers_api.py
from typing import List, Dict, Any, Optional, Union
from app.services.api_client import get_http_client
import logging

logger = logging.getLogger(__name__)

def _fetch_data(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Union[List[Any], Dict[str, Any]]:
    """Función interna para peticiones GET seguras."""
    try:
        with get_http_client() as client:
            response = client.get(endpoint, params=params)
            
            if response.status_code == 401:
                with get_http_client(force_relogin=True) as new_client:
                    response = new_client.get(endpoint, params=params)
            
            if response.status_code == 403:
                return {"error": "Permiso denegado. El token actual no tiene privilegios de ADMIN u OWNER para ver proveedores."}
                
            if response.status_code == 404:
                return {"error": "Proveedor no encontrado."}
                
            response.raise_for_status()
            return response.json()
            
    except Exception as e:
        logger.error(f"Error en GET {endpoint}: {e}")
        return {"error": f"Error de conexión: {str(e)}"}

def get_all_suppliers() -> List[Dict[str, Any]]:
    """Obtiene el directorio completo de proveedores registrados."""
    data = _fetch_data("/suppliers/")
    return data if isinstance(data, list) else []

def get_supplier_detail(supplier_id: int) -> Dict[str, Any]:
    """Obtiene los datos fiscales y de contacto de un proveedor específico."""
    data = _fetch_data(f"/suppliers/{supplier_id}/")
    return data if isinstance(data, dict) else {"error": "Respuesta inesperada"}