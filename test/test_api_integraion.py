import unittest
import os
from dotenv import load_dotenv
load_dotenv()
import requests

class TestAPIIntegration(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):

        cls.base_url = os.getenv('POS_API_URL')
        
        cls.headers = {
            "Authorization": "Bearer TEST_TOKEN_AQUI",
            "Content-Type": "application/json"
        }

    def check_endpoint_alive(self, endpoint, params=None):
        """
        Función auxiliar: Hace un GET al endpoint y verifica que 
        el servidor responda (status code < 500).
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.get(url, params=params, headers=self.headers, timeout=5)
            
            self.assertLess(
                response.status_code, 
                500, 
                f"CRASH del servidor (500+) en {endpoint}. Código: {response.status_code}. Respuesta: {response.text}"
            )
            return response
            
        except requests.exceptions.ConnectionError:
            self.fail(f"Fallo de conexión: No se pudo conectar a {url}. ¿Está el servidor encendido?")
        except requests.exceptions.Timeout:
            self.fail(f" Timeout: El endpoint {url} tardó demasiado en responder.")

    # TESTS DE ANALYTICS (Tus rutas actuales)

    def test_analytics_sales_summary(self):
        self.check_endpoint_alive("/analytics/sales-summary/", {"start_date": "2026-03-01"})

    def test_analytics_product_ranking(self):
        self.check_endpoint_alive("/analytics/product-ranking/", {"limit": 10, "criterion": "most"})

    def test_analytics_low_stock(self):
        self.check_endpoint_alive("/analytics/reports/low-stock/", {"threshold": 5})

    def test_analytics_dead_inventory(self):
        self.check_endpoint_alive("/analytics/reports/dead-inventory/")

    def test_analytics_customer_sales(self):
        # Usamos un ID de cliente genérico (ej. 1), si no existe dará 404, lo cual es válido aquí.
        self.check_endpoint_alive("/analytics/customer-sales/", {"customer_id": 1})

    def test_analytics_sales_velocity(self):
        self.check_endpoint_alive("/analytics/sales-velocity/", {"identifier": "TEST-PROD", "period_days": 30})

    def test_analytics_inventory_valuation(self):
        self.check_endpoint_alive("/analytics/inventory-valuation/")

    def test_analytics_product_contribution(self):
        self.check_endpoint_alive("/analytics/product-contribution/", {"product_identifier": "TEST-PROD"})

    # ==========================================
    # OTROS SERVICIOS (Ejemplos a completar)
    # ==========================================

    def test_products_list(self):
        self.check_endpoint_alive("/products/")

    def test_customers_list(self):
        self.check_endpoint_alive("/customers/")

    def test_sales_list(self):
        self.check_endpoint_alive("/sales/")
        
    def test_providers_list(self):
        self.check_endpoint_alive("/providers/")

if __name__ == "__main__":
    unittest.main()