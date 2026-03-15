## Catálogo de Servicios POS (Documentación para MCP y LLM)

Este documento especifica las herramientas de lectura del sistema de Punto de Venta (POS) disponibles para el Agente de IA. Se debe utilizar esta referencia para seleccionar la herramienta adecuada según la consulta del usuario.
### 1. Módulo de Analítica (analytics_api)

Proporciona métricas financieras, comportamiento de ventas y estado del inventario.

*   **`get_sales_summary(start_date, end_date)`**

    *   **Propósito:** Consulta general de rendimiento financiero y operativo.

    *   **Retorna:** Ingresos totales, ticket promedio (alto/bajo)`, horas con mayor volumen de transacciones y desglose por métodos de pago dentro del rango de fechas.

*   **`get_product_ranking(limit, criterion, start_date, end_date)`**

    *   **Propósito:** Identificación de artículos de mayor o menor rotación.

    *   **Parámetros Críticos:**

        *   **`criterion`** (String): Define el orden de la lista. Acepta únicamente "most" (más vendidos), "least" (menos vendidos) o "both" (retorna ambos extremos). El valor por defecto es "most".

    *   **Retorna:** Lista ordenada de productos basada estrictamente en la cantidad de unidades vendidas (criterios: most o least).

*   **`get_low_stock(threshold)`**

    *   **Propósito:** Monitoreo y alertas de reabastecimiento.

    *   **Retorna:** Lista de productos cuyo nivel de inventario actual es inferior o igual al umbral (threshold) especificado.

*   **`get_dead_inventory(reference_date)`**

    *   **Propósito:**
    *   **Retorna:** Lista de artículos que cuentan con existencias pero no registran ventas desde la fecha de referencia.

*   **`get_customer_sales(customer_id, start_date, end_date)`**

    *   **Propósito:** Análisis de comportamiento y valor del cliente.

    *   **Retorna:** Historial de compras, gasto total acumulado, ticket promedio, producto más comprado y horas de actividad de un cliente específico.

*   **`get_sales_velocity(identifier, period_days)`**

    *   **Propósito:** Proyecciones de stock y ritmo de venta.

    *   **Retorna:** Tasa promedio diaria de ventas de un producto y la estimación de días restantes antes de su agotamiento total.

*   **`get_inventory_valuation(product_identifier)`**

    *   **Propósito:** Análisis del valor financiero del almacén.

    *   **Retorna:** Costo total de adquisición del inventario, ingresos potenciales de venta y porcentaje de margen de utilidad proyectado.

*   **`get_product_contribution(product_identifier, start_date, end_date)`**

    *   **Propósito:** Evaluación del impacto de un producto específico en la facturación global.

    *   **Retorna:** El porcentaje exacto que representan las ventas del producto frente al total de ingresos del negocio en el periodo establecido.

### 2. Módulo de Órdenes y Tickets (orders_api)

Proporciona acceso a la información transaccional y folios de recibos.

*   **`get_order_detail(order_id)`**

    *   **Propósito:** Auditoría detallada de una transacción específica.

    *   **Retorna:** Desglose financiero completo a nivel de partida (líneas de artículos), cálculos de impuestos (IVA), descuentos aplicados e información del vendedor. Requiere el ID numérico interno de la orden.

*   **`search_recent_orders(ticket_folio, status, limit)`**

    *   **Propósito:** Búsqueda y seguimiento de transacciones recientes.

    *   **Retorna:** Lista de órdenes filtradas mediante coincidencia exacta del folio alfanumérico del ticket o por su estado operativo (PENDING, PAID, CANCELLED).

### 3. Módulo de Usuarios del Bot (chatbot_users_api)

Proporciona acceso a los registros de seguridad y control de acceso del sistema.

*   **`get_all_chatbot_users()`**

    *   **Propósito:** Auditoría global de accesos al sistema.

    *   **Retorna:** Lista completa de los nombres y números telefónicos autorizados para interactuar con la plataforma.

*   **`get_chatbot_user(mobile_number)`**

    *   **Propósito:** Verificación de acceso de un individuo.

    *   **Retorna:** Datos de registro y registro de tiempo (timestamp) de la última interacción del número telefónico consultado.

### 4. Módulo de Productos y Promociones (products_api)

Proporciona acceso al inventario, precios y descuentos vigentes.

*   **`get_all_products()`**

    *   **Propósito:** Consultar el catálogo completo de la tienda.

    *   **Retorna:** Lista de productos con nombre, SKU, stock disponible (available_to_sell) y precio final con IVA.

*   **`get_product_by_id(product_id)`**

    *   **Propósito:** Ver información técnica y stock de un artículo específico.

    *   **Retorna:** Detalle extendido del producto incluyendo proveedor y cantidades reservadas.

*   **`get_all_promotions()`**

    *   **Propósito:** Listar todos los eventos de descuento (Rebajas, Black Friday, etc.).

    *   **Retorna:** Nombre de la promoción, porcentaje de descuento y fechas de validez.

*   **`get_promotions_by_product(product_id)`**

    *   **Propósito:** Verificar si un producto específico tiene un descuento aplicado actualmente.

    *   **Retorna:** Detalles de la promoción aplicable a ese ID de producto.

### 5. Módulo de Gestión de Clientes y Crédito (customers_api)

Proporciona seguimiento de perfiles, sistemas de lealtad y estados de cuenta crediticios.

*   **`get_all_customers()`**

    *   **Propósito:** Auditoría y listado de la base de datos de clientes.

    *   **Retorna:** Lista de clientes incluyendo nombre, contacto, estatus de "Cliente Frecuente" y puntos de lealtad actuales.

*   **`get_customer_detail(customer_id)`**

    *   **Propósito:** Consulta de perfil individual y datos demográficos.

    *   **Retorna:** Información detallada del cliente, incluyendo fecha de nacimiento y correo electrónico para campañas dirigidas o validaciones.

*   **`get_customer_points_history(customer_id)`**

    *   **Propósito:** Auditoría del sistema de recompensas.

    *   **Retorna:** Historial cronológico de transacciones de puntos, detallando eventos de acumulación (EARN) y canje (REDEEM).

*   **`get_customer_credit_history(customer_id)`**

    *   **Propósito:** Revisión de estado de cuenta y solvencia.

    *   **Retorna:** Libro mayor de crédito de tienda, listando cargos por compras (CHARGE) y abonos realizados (PAYMENT).