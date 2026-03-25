# RAG_MODULE: POS_BILINGUAL_API_CATALOG
# CONTEXT: Point of Sale System Integration
# ROLE: Bridge Spanish user queries to English API functions.
# TOKEN_EFFICIENCY: High (Keyword-dense)

## [SECTION] SYSTEM_RULES
- INPUT: Spanish (Natural Language)
- LOGIC: English (API Calls)
- OUTPUT: Spanish (Natural Response)
- DATE_RULE: Always use `TIME_TRANSLATOR_LOGIC` for date parameters.

## [MODULE] ANALYTICS_API (Metricas y Reportes)
- `get_sales_summary(start_date, end_date)`
  - **Triggers (ES):** ¿Cuánto vendimos?, resumen de ventas, ingresos, reporte financiero.
  - **Returns:** Total revenue, avg ticket, peak hours, payment methods.

- `get_product_ranking(limit, criterion, start_date, end_date)`
  - **Triggers (ES):** Top de productos, más vendidos, peores ventas, ranking.
  - **Constraints:** `criterion` must be: "most" (más), "least" (menos), or "both".

- `get_low_stock(threshold)`
  - **Triggers (ES):** Productos agotándose, falta mercancía, stock bajo, ¿qué hay que comprar?
  - **Logic:** Returns items where current_stock <= threshold.

- `get_dead_inventory(reference_date)`
  - **Triggers (ES):** Mercancía estancada, productos sin movimiento, no se vende desde.

- `get_sales_velocity(identifier, period_days)`
  - **Triggers (ES):** ¿Qué tan rápido se vende X?, ¿cuándo se va a acabar el stock?
  - **Returns:** Daily rate and "days-to-empty" estimate.

- `get_inventory_valuation(product_identifier)`
  - **Triggers (ES):** Valor del inventario, ¿cuánto dinero hay en el almacén?, margen de utilidad.

- `get_product_contribution(product_identifier, start_date, end_date)`
  - **Triggers (ES):** ¿Cuánto aporta este producto al total?, impacto en la facturación.

- `get_customer_sales(customer_id, start_date, end_date)`
  - **Triggers (ES):** Compras de un cliente, ¿qué ha comprado [ID]?, hábitos de gasto, productos favoritos del cliente, valor del cliente.
  - **Logic:** Analyzes specific client behavior (spending patterns and top purchased items).

## [MODULE] ORDERS_API (Ventas y Transacciones)
- `get_order_detail(order_id)`
  - **Triggers (ES):** Ver ticket, detalle de venta, ¿qué se vendió en la orden X?
- `search_recent_orders(ticket_folio, status, limit)`
  - **Triggers (ES):** Buscar folio, ventas pendientes, órdenes pagadas, ventas canceladas.

## [MODULE] PRODUCTS_API (Catalogo y Precios)
- `get_all_products()`
  - **Triggers (ES):** Ver catálogo, lista de precios, existencias totales, SKU.
- `get_all_promotions()`
  - **Triggers (ES):** Ofertas vigentes, promociones, descuentos, rebajas.
- `get_promotions_by_product(product_id)`
  - **Triggers (ES):** ¿Este producto tiene descuento?, ver rebaja de este ID.
- `get_product_by_id(product_id)`
  - **Triggers (ES):** Info técnica del producto, ver SKU específico, proveedor de este artículo, ver stock reservado por ID.
  - **Logic:** Returns technical details, supplier information, and quantities reserved for pending orders.


## [MODULE] CUSTOMERS_API (Clientes y Fidelización)
- `get_all_customers()`
  - **Triggers (ES):** Lista de clientes, socios, clientes frecuentes.
- `get_customer_points_history(customer_id)`
  - **Triggers (ES):** Puntos de lealtad, ¿cuánto ha canjeado?, historial de puntos.
- `get_customer_credit_history(customer_id)`
  - **Triggers (ES):** Deuda del cliente, ¿cuánto debe?, historial de pagos, crédito disponible.
- `get_customer_detail(customer_id)`
  - **Triggers (ES):** Perfil completo del cliente, datos de contacto de [ID], correo del cliente, fecha de nacimiento, info demográfica.
  - **Logic:** Accesses the full personal profile, including contact email and birthday for targeted validation.

## [MODULE] CHATBOT_USERS_API (Seguridad)
- `get_all_chatbot_users()`
  - **Triggers (ES):** ¿Quién tiene permiso?, lista blanca, usuarios del bot.
- `get_chatbot_user(mobile_number)`
  - **Triggers (ES):** Verificar acceso, última conexión de un número.

# [BILINGUAL_MAPPER]
- "días" -> `dia`
- "semanas" -> `semana`
- "meses" -> `mes`
- "años" -> `año`
- "más vendido" -> `most`
- "menos vendido" -> `least`