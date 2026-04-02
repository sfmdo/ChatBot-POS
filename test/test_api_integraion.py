import unittest
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

class TestAPIIntegration(unittest.IsolatedAsyncioTestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.base_url = os.getenv('POS_API_URL')
        cls.headers = {
            "Authorization": "Bearer TEST_TOKEN_HERE",
            "Content-Type": "application/json"
        }

    async def check_endpoint_alive(self, endpoint, params=None):
        """
        Helper function: Makes an async GET request to the endpoint and verifies that 
        the server responds without crashing (status code < 500).
        """
        url = f"{self.base_url}{endpoint}"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, headers=self.headers, timeout=5.0)
            
            self.assertLess(
                response.status_code, 
                500, 
                f"Server CRASH (500+) at {endpoint}. Code: {response.status_code}. Response: {response.text}"
            )
            return response
            
        except httpx.ConnectError:
            self.fail(f"Connection failed: Could not connect to {url}. Is the server running?")
        except httpx.TimeoutException:
            self.fail(f"Timeout: Endpoint {url} took too long to respond.")

    # ==========================================
    # ANALYTICS TESTS (Current routes)
    # ==========================================

    async def test_analytics_sales_summary(self):
        await self.check_endpoint_alive("/analytics/sales-summary/", {"start_date": "2026-03-01"})

    async def test_analytics_product_ranking(self):
        await self.check_endpoint_alive("/analytics/product-ranking/", {"limit": 10, "criterion": "most"})

    async def test_analytics_low_stock(self):
        await self.check_endpoint_alive("/analytics/reports/low-stock/", {"threshold": 5})

    async def test_analytics_dead_inventory(self):
        await self.check_endpoint_alive("/analytics/reports/dead-inventory/")

    async def test_analytics_customer_sales(self):
        # We use a generic customer ID (e.g., 1), if it doesn't exist it will return 404, which is valid here.
        await self.check_endpoint_alive("/analytics/customer-sales/", {"customer_id": 1})

    async def test_analytics_sales_velocity(self):
        await self.check_endpoint_alive("/analytics/sales-velocity/", {"identifier": "TEST-PROD", "period_days": 30})

    async def test_analytics_inventory_valuation(self):
        await self.check_endpoint_alive("/analytics/inventory-valuation/")

    async def test_analytics_product_contribution(self):
        await self.check_endpoint_alive("/analytics/product-contribution/", {"product_identifier": "TEST-PROD"})

    # ==========================================
    # OTHER SERVICES (Examples to complete)
    # ==========================================

    async def test_products_list(self):
        await self.check_endpoint_alive("/products/")

    async def test_customers_list(self):
        await self.check_endpoint_alive("/customers/")

    async def test_sales_list(self):
        await self.check_endpoint_alive("/sales/")
        
    async def test_providers_list(self):
        await self.check_endpoint_alive("/providers/")

if __name__ == "__main__":
    unittest.main()