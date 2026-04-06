# app/bot/mcp_tools.py
from typing import Optional, Dict, Any, List
from app.utils.time_translator import TimeTranslator
from app.services import analytics_api, orders_api, products_api, customers_api, chatbot_users_api, suppliers_api
import logging

logger = logging.getLogger(__name__)

def setup_tools(mcp):
    """Registra todas las herramientas del sistema POS en el servidor MCP."""

    # ! ANALYTICS 

    @mcp.tool()
    async def get_sales_summary(
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None, 
        period: Optional[str] = None,
        unit: Optional[str] = None,
        quantity: Optional[int] = None
    ) -> Any:
        """Generates a financial report. Use 'period' for relative dates or 'unit'/'quantity' for lookbacks."""
    
        time_params = {}
        if period:
            time_params = {"period": period}
        elif unit and quantity:
            time_params = {"unit": unit, "quantity": quantity}

        if time_params:
            dates = TimeTranslator.process_request(time_params)
            if "error" not in dates:
                start_date = dates.get("start_date")
                end_date = dates.get("end_date")
            
        return await analytics_api.get_sales_summary(start_date=start_date, end_date=end_date)

    @mcp.tool()
    async def get_product_ranking(
        limit: int = 10, 
        criterion: str = "most", 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None, 
        period: Optional[str] = None,
        unit: Optional[str] = None,
        quantity: Optional[int] = None
    ) -> Any:
        """Returns ranking of products. Use 'period' or 'unit'/'quantity' for time filtering."""
    
        time_params = {}
        if period:
            time_params = {"period": period}
        elif unit and quantity:
            time_params = {"unit": unit, "quantity": quantity}

        if time_params:
            dates = TimeTranslator.process_request(time_params)
            if "error" not in dates:
                start_date = dates.get("start_date")
                end_date = dates.get("end_date")

        return await analytics_api.get_product_ranking(
            limit=limit, criterion=criterion, start_date=start_date, end_date=end_date
        )

    @mcp.tool()
    async def get_low_stock(threshold: Optional[int] = None) -> Any:
        """Identifies products with low inventory levels where current stock is less than or equal to threshold."""
        return await analytics_api.get_low_stock(threshold=threshold)

    @mcp.tool()
    async def get_dead_inventory(reference_date: Optional[str] = None,period: Optional[str] = None,
                                unit: Optional[str] = None,
                                quantity: Optional[int] = None) -> Any:
        """Identifies products that have had no sales since a given reference date."""
        return await analytics_api.get_dead_inventory(reference_date=reference_date)

    @mcp.tool()
    async def get_sales_velocity(identifier: str, period_days: int = 30) -> Any:
        """Calculates sales velocity and estimates days until stock depletion for a product."""
        return await analytics_api.get_sales_velocity(identifier=identifier, period_days=period_days)

    @mcp.tool()
    async def get_inventory_valuation(product_identifier: Optional[str] = None) -> Any:
        """Calculates the financial value and projected profits of the inventory."""
        return await analytics_api.get_inventory_valuation(product_identifier=product_identifier)

    @mcp.tool()
    async def get_product_contribution(
        product_identifier: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None, 
        period: Optional[str] = None,
        unit: Optional[str] = None,
        quantity: Optional[int] = None
    ) -> Any:
        """Calculates revenue % for a product. Supports 'period' and 'unit'/'quantity'."""
    
        time_params = {}
        if period:
            time_params = {"period": period}
        elif unit and quantity:
            time_params = {"unit": unit, "quantity": quantity}

        if time_params:
            dates = TimeTranslator.process_request(time_params)
            if "error" not in dates:
                start_date = dates.get("start_date")
                end_date = dates.get("end_date")

        return await analytics_api.get_product_contribution(
            product_identifier=product_identifier, start_date=start_date, end_date=end_date
        )

    @mcp.tool()
    async def get_customer_sales(
        customer_id: int, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None, 
        period: Optional[str] = None,
        unit: Optional[str] = None,
        quantity: Optional[int] = None
    ) -> Any:
        """Customer purchase history. Supports 'period' and 'unit'/'quantity'."""
    
        time_params = {}
        if period:
            time_params = {"period": period}
        elif unit and quantity:
            time_params = {"unit": unit, "quantity": quantity}

        if time_params:
            dates = TimeTranslator.process_request(time_params)
            if "error" not in dates:
                start_date = dates.get("start_date")
                end_date = dates.get("end_date")

        return await analytics_api.get_customer_sales(
            customer_id=customer_id, start_date=start_date, end_date=end_date
        )
    # ! ORDERS MODULE 

    @mcp.tool()
    async def get_order_detail(order_id: int) -> Any:
        """Retrieves the full details of a specific order or ticket."""
        return await orders_api.get_order_detail(order_id=order_id)

    @mcp.tool()
    async def search_recent_orders(ticket_folio: Optional[str] = None, status: Optional[str] = None, limit: int = 10) -> Any:
        """Searches recent orders by folio, status (PENDING, PAID, CANCELLED), or gets a general list."""
        return await orders_api.search_recent_orders(ticket_folio=ticket_folio, status=status, limit=limit)

    # ! PRODUCTS MODULE

    @mcp.tool()
    async def get_all_products() -> Any:
        """Retrieves the full product catalog, pricing, and total stock."""
        full_data = await products_api.get_all_products()
        clean_data = [
            {"id": p["id"], "name": p["name"], "sku": p["sku"], "price": p["final_price"]} 
            for p in full_data
        ]
        return clean_data

    @mcp.tool()
    async def get_all_promotions() -> Any:
        """Retrieves all currently active promotions, discounts, and sales."""
        return await products_api.get_all_promotions()

    @mcp.tool()
    async def get_promotions_by_product(product_id: int) -> Any:
        """Checks if a specific product has any active discounts or promotions."""
        return await products_api.get_promotions_by_product(product_id=product_id)

    @mcp.tool()
    async def get_product_by_id(product_id: int) -> Any:
        """Returns technical details, SKU, supplier information, and reserved stock for a specific product."""
        return await products_api.get_product_by_id(product_id=product_id)
    
    @mcp.tool()
    async def search_product_by_sku(sku: str) -> Any:
        """
        Searches for a specific product by its SKU (Stock Keeping Unit) in the local catalog.
        Useful for quick identification of items by their code.
        """
        products = await products_api.get_all_products()
        

        if isinstance(products, list):
            for p in products:
                if str(p.get("sku", "")).upper() == sku.upper():
                    return p
                    
        return {"error": f"Product with SKU '{sku}' not found in the catalog."}

    # !  CUSTOMERS MODULE

    @mcp.tool()
    async def get_all_customers() -> Any:
        """Retrieves the complete list of registered customers and frequent shoppers."""
        return await customers_api.get_all_customers()

    @mcp.tool()
    async def get_customer_points_history(customer_id: int) -> Any:
        """Retrieves the loyalty points history and redemption records for a customer."""
        return await customers_api.get_customer_points_history(customer_id=customer_id)

    @mcp.tool()
    async def get_customer_credit_history(customer_id: int) -> Any:
        """Retrieves the credit history, current debt, available credit, and payment records for a customer."""
        return await customers_api.get_customer_credit_history(customer_id=customer_id)

    @mcp.tool()
    async def get_customer_detail(customer_id: int) -> Any:
        """Retrieves the full personal profile, contact email, and demographic info (e.g., birthday) of a customer."""
        return await customers_api.get_customer_detail(customer_id=customer_id)

    # ! CHATBOT USERS MODULE 

    @mcp.tool()
    async def get_all_chatbot_users() -> Any:
        """Retrieves the whitelist of users authorized to interact with the bot."""
        return await chatbot_users_api.get_all_chatbot_users()

    @mcp.tool()
    async def get_chatbot_user(mobile_number: str) -> Any:
        """Verifies access and last connection details for a specific bot user by their mobile number."""
        return await chatbot_users_api.get_chatbot_user(mobile_number=mobile_number)
    
    # ! SUPPLIERS MODULE 

    @mcp.tool()
    async def get_all_suppliers() -> List[Dict[str, Any]]:
        """Retrieves the complete directory of registered suppliers and their general information."""
        return await suppliers_api.get_all_suppliers()

    @mcp.tool()
    async def get_supplier_detail(supplier_id: int) -> Any:
        """
        Retrieves full tax identification (RFC/Tax ID) and contact details (email, phone, address) 
        of a specific supplier by its ID.
        """
        return await suppliers_api.get_supplier_detail(supplier_id=supplier_id)