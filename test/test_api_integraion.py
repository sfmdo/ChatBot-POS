import unittest
import os
from typing import List, Dict

from dotenv import load_dotenv
load_dotenv()

from app.services.products_api import get_all_products
from app.services.suppliers_api import get_all_suppliers
from app.services.customers_api import get_all_customers
from app.services.analytics_api import get_sales_summary
from app.services.orders_api import search_recent_orders

class TestAPIIntegration(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """
        Validación estricta de entorno. SIN URLs POR DEFECTO.
        Si no se provee la URL del POS, las pruebas no deben ejecutarse.
        """
        if not os.getenv("POS_API_URL"):
            raise EnvironmentError(
                "CRITICAL ERROR: 'POS_API_URL' no está definida. "
                "Debes proveer la URL real del backend para ejecutar las pruebas de integración."
            )

    # PRUEBAS DEL MÓDULO DE PRODUCTOS

    def test_01_get_all_products(self):
        """Verifica que el catálogo de productos responda correctamente."""
        response = get_all_products()
        
        if isinstance(response, dict) and "error" in response:
            self.fail(f"Fallo en Productos: {response['error']}")
            
        self.assertIsInstance(response, list, "La API debe devolver una lista de productos.")

    # PRUEBAS DEL MÓDULO DE PROVEEDORES

    def test_02_get_all_suppliers(self):
        """Verifica el acceso al directorio de proveedores (Requiere ADMIN/OWNER)."""
        response = get_all_suppliers()
        
        if isinstance(response, dict) and "error" in response:
            error_msg = str(response.get("error"))
            
            if "Permiso denegado" in error_msg:
                print("\n[INFO] Prueba de proveedores arrojó 403 (Permiso denegado). Esto es correcto si el Bot usa un token de EMPLOYEE.")
            else:
                self.fail(f"Error inesperado en Proveedores: {error_msg}")
        else:
            self.assertIsInstance(response, list)

    # PRUEBAS DEL MÓDULO DE CLIENTES

    def test_03_get_all_customers(self):
        """Verifica la respuesta del listado de clientes y sus atributos de lealtad."""
        response = get_all_customers()
        
        if isinstance(response, dict) and "error" in response:
            error_msg = str(response.get("error"))
            self.fail(f"Fallo en Clientes: {error_msg}")
            
        self.assertIsInstance(response, list)

    # PRUEBAS DEL MÓDULO DE ANALÍTICA

    def test_04_get_sales_summary(self):
        """Verifica el resumen de ventas enviando fechas en formato ISO 8601."""
        start = "2026-03-01"
        end = "2026-03-31"
        response = get_sales_summary(start_date=start, end_date=end)
        
        if isinstance(response, dict) and "error" in response:
            self.fail(f"Fallo en Analítica (Sales Summary): {response['error']}")
            
        self.assertIsInstance(response, dict, "El resumen de ventas debe ser un objeto JSON (dict).")

    # PRUEBAS DEL MÓDULO DE ÓRDENES

    def test_05_search_recent_orders(self):
        """Verifica la consulta de tickets recientes."""
        response = search_recent_orders(limit=5)
        
        if isinstance(response, dict) and "error" in response:
            error_msg = str(response.get("error"))
            self.fail(f"Fallo en Órdenes: {error_msg}")
            
        self.assertIsInstance(response, list, "La búsqueda de órdenes debe devolver una lista.")

if __name__ == '__main__':
    unittest.main()