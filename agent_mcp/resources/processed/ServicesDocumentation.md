# POS_SYSTEM_TECHNICAL_CATALOG

---

## [MODULE] TIME_TRANSLATOR_LOGIC
- **PURPOSE:** Maps relative time expressions to API-compatible parameters.
- **MODE 1: Absolute Dates**

  - Use `start_date` and `end_date` in `YYYY-MM-DD` format for specific ranges.

- **MODE 2: Predefined Periods**

  - Use the `period` parameter: `"hoy"`, `"ayer"`, `"esta_semana"`, `"semana_pasada"`, `"este_mes"`, `"mes_pasado"`, `"este_año"`.

- **MODE 3: Retroactive Lookback (Relative)**

  - Use `unit` (dia, semana, mes, año) and `quantity` (integer).

  - Example: "last 15 days" -> `unit: "dia", quantity: 15`.
- **LOGIC_RULES:**
  - **Daily:** "today" -> `period: "hoy"`, "yesterday" -> `period: "ayer"`
  - **Weekly:** "this week" -> `period: "esta_semana"`, "last week" -> `period: "semana_pasada"`
  - **Monthly:** "this month" -> `period: "este_mes"`, "last month" -> `period: "mes_pasado"`
  - **Yearly:** "this year" -> `period: "este_año"`, "last year" -> `period: "año_pasado"`
- **RETROACTIVE:** 
  - Units: "days" -> `dia`, "weeks" -> `semana`, "months" -> `mes`, "years" -> `año`.
  - Usage: `{"unit": "mes", "quantity": 3}` for "last 3 months".
  
### 1 TOOL: get_sales_summary
- **TOOL_NAME:** `get_sales_summary`
- **DESCRIPTION:** Generates a financial report. Use `period` for named ranges, `unit`/`quantity` for relative lookbacks (e.g., "last 5 days"), or `start_date`/`end_date` for specific dates.
- **KEYWORDS:** revenue, income, sales report, total earnings, financial summary.
- **ARGUMENTS:** `{"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD", "period": "hoy"|"ayer"|"este_mes"|"año_pasado", "unit": "dia"|"semana"|"mes"|"año", "quantity": int}`
- **EXAMPLE_QUESTIONS:** 
  - "How much did we sell in the last 15 days?" -> `{"unit": "dia", "quantity": 15}`
  - "Sales report from 2024-01-01 to 2024-01-20" -> `{"start_date": "2024-01-01", "end_date": "2024-01-20"}`
  - "Total revenue for last month" -> `{"period": "mes_pasado"}`
- **JSON_FORMAT:** `{"tool": "get_sales_summary", "arguments": {"unit": "dia", "quantity": 15}}`

---

### 2 TOOL: get_product_ranking
- **TOOL_NAME:** `get_product_ranking`
- **DESCRIPTION:** Returns a ranked list of products. Supports relative lookbacks via `unit` and `quantity`.
- **KEYWORDS:** top products, best sellers, worst products, sales ranking.
- **ARGUMENTS:** `{"limit": int, "criterion": "most"|"least", "period": string, "unit": "dia"|"semana"|"mes"|"año", "quantity": int, "start_date": string, "end_date": string}`
- **EXAMPLE_QUESTIONS:** 
  - "What are the top 5 products of the last 2 months?" -> `{"limit": 5, "unit": "mes", "quantity": 2}`
  - "Show me the worst sellers of the week" -> `{"criterion": "least", "period": "esta_semana"}`
- **JSON_FORMAT:** `{"tool": "get_product_ranking", "arguments": {"limit": 5, "unit": "mes", "quantity": 2}}`
---

### 3 TOOL: get_low_stock
- **TOOL_NAME:** `get_low_stock`
- **DESCRIPTION:** Identifies products where inventory levels have dropped below a specific number.
- **KEYWORDS:** low stock, out of stock, restocking, inventory shortage, critical inventory.
- **ARGUMENTS:** `{"threshold": int}`
- **EXAMPLE_QUESTIONS:** 
  - "What products are running out?"
  - "Show me everything with stock less than 10 units."
  - "Is there anything I need to restock right now?"
- **JSON_FORMAT:** `{"tool": "get_low_stock", "arguments": {"threshold": 5}}`

---

### 4 TOOL: get_dead_inventory
- **TOOL_NAME:** `get_dead_inventory`
- **DESCRIPTION:** Finds products that have recorded zero sales since a specific reference date.
- **KEYWORDS:** dead stock, stagnant inventory, no sales, slow moving items, stuck products.
- **ARGUMENTS:** `{"reference_date": string}`
- **EXAMPLE_QUESTIONS:** 
  - "Which products haven't sold since last year?"
  - "Show me dead inventory since 2024-01-01."
  - "What items are stuck in the warehouse without movement?"
- **JSON_FORMAT:** `{"tool": "get_dead_inventory", "arguments": {"reference_date": "2024-01-01"}}`

---

### 5 TOOL: get_sales_velocity
- **TOOL_NAME:** `get_sales_velocity`
- **DESCRIPTION:** Calculates how fast a product sells per day and estimates how many days of stock are left.
- **KEYWORDS:** sales speed, depletion rate, burn rate, stockout estimate, days left.
- **ARGUMENTS:** `{"identifier": string, "period_days": int}`
- **EXAMPLE_QUESTIONS:** 
  - "When will we run out of Coca-Cola?"
  - "What is the sales velocity of SKU-100?"
  - "How many days of stock do I have left for this product?"
- **JSON_FORMAT:** `{"tool": "get_sales_velocity", "arguments": {"identifier": "SKU-99", "period_days": 30}}`

---

### 6 TOOL: get_inventory_valuation
- **TOOL_NAME:** `get_inventory_valuation`
- **DESCRIPTION:** Calculates the total monetary value of the inventory and projected profit margins.Use ONLY for total asset reports. DO NOT use for individual product prices.
- **KEYWORDS:** inventory value, warehouse worth, total assets, stock valuation, total cost.
- **ARGUMENTS:** `{"product_identifier": string}`
- **EXAMPLE_QUESTIONS:** 
  - "How much money is tied up in the inventory?"
  - "What is the total valuation of the warehouse?"
  - "What is the financial value of my current stock?"
- **JSON_FORMAT:** `{"tool": "get_inventory_valuation", "arguments": {}}`

---

###  7 TOOL: get_product_contribution
- **TOOL_NAME:** `get_product_contribution`
- **DESCRIPTION:** Measures the percentage of total revenue generated by an item over a specific time range.
- **KEYWORDS:** revenue share, sales impact, contribution percentage.
- **ARGUMENTS:** `{"product_identifier": string, "period": string, "unit": "dia"|"semana"|"mes"|"año", "quantity": int, "start_date": string, "end_date": string}`
- **EXAMPLE_QUESTIONS:** 
  - "What was the contribution of SKU-100 in the last 30 days?" -> `{"product_identifier": "SKU-100", "unit": "dia", "quantity": 30}`
  - "Sales impact of this product during last year" -> `{"product_identifier": "ID", "period": "año_pasado"}`
- **JSON_FORMAT:** `{"tool": "get_product_contribution", "arguments": {"product_identifier": "A1", "unit": "dia", "quantity": 30}}`

---

### 8 TOOL: get_customer_sales
- **TOOL_NAME:** `get_customer_sales`
- **DESCRIPTION:** Analyzes customer spending and history. Supports lookbacks for behavior analysis.
- **KEYWORDS:** customer history, shopper habits, client spending patterns.
- **ARGUMENTS:** `{"customer_id": int, "period": string, "unit": "dia"|"semana"|"mes"|"año", "quantity": int, "start_date": string, "end_date": string}`
- **EXAMPLE_QUESTIONS:** 
  - "What has customer 450 bought in the last 6 months?" -> `{"customer_id": 450, "unit": "mes", "quantity": 6}`
  - "Spending habits of client 123 during 2023" -> `{"customer_id": 123, "start_date": "2023-01-01", "end_date": "2023-12-31"}`
- **JSON_FORMAT:** `{"tool": "get_customer_sales", "arguments": {"customer_id": 123, "unit": "mes", "quantity": 6}}`

---

### 9 TOOL: get_order_detail
- **TOOL_NAME:** `get_order_detail`
- **DESCRIPTION:** Retrieves the complete itemized breakdown of a specific transaction, including prices, quantities, and totals.
- **KEYWORDS:** ticket details, order info, specific sale, item breakdown, transaction content.
- **ARGUMENTS:** `{"order_id": int}`
- **EXAMPLE_QUESTIONS:** 
  - "Show me the details for order ID 501."
  - "What was sold in ticket #45?"
  - "Give me the breakdown for order 1024."
- **JSON_FORMAT:** `{"tool": "get_order_detail", "arguments": {"order_id": 501}}`

---

### 10 TOOL: search_recent_orders
- **TOOL_NAME:** `search_recent_orders`
- **DESCRIPTION:** Searches for transactions using filters like folio number or payment status. Can return a general list of the latest sales.
- **KEYWORDS:** recent sales, folio search, pending orders, paid tickets, cancelled sales, transaction history.
- **CONSTRAINTS:** `status` must be: "PENDING", "PAID", or "CANCELLED".
- **ARGUMENTS:** `{"ticket_folio": string, "status": string, "limit": int}`
- **EXAMPLE_QUESTIONS:** 
  - "Show me the last 10 sales."
  - "Search for folio number A-102."
  - "List all pending orders."
  - "Find the most recent cancelled tickets."
- **JSON_FORMAT:** `{"tool": "search_recent_orders", "arguments": {"status": "PAID", "limit": 5}}`


---

### 11 TOOL: get_total_product_count
- **TOOL_NAME:** `get_total_product_count`
- **DESCRIPTION:** Returns the total number of products currently registered in the catalog. Use this for a quick inventory overview without listing individual items.
- **KEYWORDS:** count products, total items, inventory size, catalog quantity, how many products.
- **ARGUMENTS:** `{}`
- **EXAMPLE_QUESTIONS:** 
  - "How many products do I have in total?" -> `{}`
  - "Total count of items in the catalog." -> `{}`
- **JSON_FORMAT:** `{"tool": "get_total_product_count", "arguments": {}}`

---

### 12 TOOL: search_products_in_inventory
- **TOOL_NAME:** `search_products_in_inventory`
- **DESCRIPTION:** Primary tool for retrieving individual item data. Use this whenever you need to find the PRICE, STOCK LEVEL, or TECHNICAL DETAILS of any product in the catalog using its name, SKU, or database ID.
- **KEYWORDS:** product lookup, price check, check stock, item cost, find product, unit price, catalog search, SKU lookup, item availability, product details, inventory search.
- **ARGUMENTS:** `{ "id": int, "name": string, "sku": string, "supplier_id": int, "low_stock": bool, "price": float, "final_price": float, "tax_rate": float, "tax_rate_display": string }
- **EXAMPLE_QUESTIONS:** 
  - "What is the price of [Product Name]?" -> `{"name": "[Product Name]"}`
  - "How much stock is left for SKU [Code]?" -> `{"sku": "[Code]"}`
  - "Show me all information for product ID [ID Number]." -> `{"id": [ID Number]}`
- **JSON_FORMAT:** `{"tool": "search_products_in_inventory", "arguments": {"name": "Product Name"}}`

---

### 13 TOOL: get_all_promotions
- **TOOL_NAME:** `get_all_promotions`
- **DESCRIPTION:** Retrieves a list of all currently active discounts, sales, and special offers across the store.
- **KEYWORDS:** active offers, store discounts, sales, current promos, price drops.
- **ARGUMENTS:** `{}`
- **EXAMPLE_QUESTIONS:** 
  - "What are the current promotions?"
  - "Are there any active discounts today?"
  - "Show me all products on sale."
- **JSON_FORMAT:** `{"tool": "get_all_promotions", "arguments": {}}`

---

### 14 TOOL: get_promotions_by_product
- **TOOL_NAME:** `get_promotions_by_product`
- **DESCRIPTION:** Checks if a specific product (by ID) has an active discount or is part of a special offer.
- **KEYWORDS:** check discount, item sale, product promo, discount status.
- **ARGUMENTS:** `{"product_id": int}`
- **EXAMPLE_QUESTIONS:** 
  - "Does product ID 45 have a discount?"
  - "Check if there's an offer for this item."
  - "Is this product on sale right now?"
- **JSON_FORMAT:** `{"tool": "get_promotions_by_product", "arguments": {"product_id": 45}}`

---

### 15 TOOL: get_total_customer_count
* **TOOL_NAME:** `get_total_customer_count`
* **DESCRIPTION:** Returns the total number of customers in the database. Use this for a quick overview of the customer base size.
* **KEYWORDS:** count customers, total clients, shopper base size, how many customers.
* **ARGUMENTS:** `{}`
* **EXAMPLE_QUESTIONS:** 
  - "How many customers are registered?" -> `{}`
  - "Total count of shoppers." -> `{}`
* **JSON_FORMAT:** `{"tool": "get_total_customer_count", "arguments": {}}`

---

### 16 TOOL: search_customers
* **TOOL_NAME:** `search_customers`
* **DESCRIPTION:** Targeted customer analysis. Allows searching by unified name, debt status, points, or birth month.
* **KEYWORDS:** customer lookup, client profile, debtor search, owe money, outstanding balance, credit status, loyalty points, rewards balance, frequent shopper, birthday lookup, shopper info, CRM, customer contact, customers ID.
* **ARGUMENTS:** `{ "id": int, "name": string, "is_frequent": bool, "has_debt": bool, "min_points": int, "birth_month": int }`
* **EXAMPLE_QUESTIONS:** 
  - "Is Oscar Gutierrez a frequent customer?" -> `{"name": "Oscar Gutierrez", "is_frequent": true}`
  - "Show me all debtors." -> `{"has_debt": true}`
  - "Search for customers born in February." -> `{"birth_month": 2}`
* **JSON_FORMAT:** `{"tool": "search_customers", "arguments": {"name": "Oscar", "has_debt": true}}`

---

### 17 TOOL: get_customer_points_history
- **TOOL_NAME:** `get_customer_points_history`
- **DESCRIPTION:** Retrieves the loyalty points balance, redemption history, and point accumulation records for a specific customer.
- **KEYWORDS:** loyalty points, reward balance, point redemption, points history, customer rewards.
- **ARGUMENTS:** `{"customer_id": int}`
- **EXAMPLE_QUESTIONS:** 
  - "How many points does customer 101 have?"
  - "Show me the points redemption history for client 45."
  - "What is the rewards balance for shopper ID 99?"
- **JSON_FORMAT:** `{"tool": "get_customer_points_history", "arguments": {"customer_id": 101}}`

---

### 18 TOOL: get_customer_credit_history
- **TOOL_NAME:** `get_customer_credit_history`
- **DESCRIPTION:** Provides a detailed financial history of a customer, including current debt (amount owed), available credit limits, and past payment records.
- **KEYWORDS:** customer debt, credit limit, amount owed, credit balance, payment records, available credit.
- **ARGUMENTS:** `{"customer_id": int}`
- **EXAMPLE_QUESTIONS:** 
  - "How much does customer 88 owe?"
  - "Show the credit history for client 10."
  - "What is the available credit limit for ID 45?"
- **JSON_FORMAT:** `{"tool": "get_customer_credit_history", "arguments": {"customer_id": 88}}`

---

### 19 TOOL: get_customer_detail
- **TOOL_NAME:** `get_customer_detail`
- **DESCRIPTION:** Retrieves the full personal profile of a customer, including contact email, demographic information, and date of birth.
- **KEYWORDS:** customer profile, personal info, contact email, birthday, demographic data, client details.
- **ARGUMENTS:** `{"customer_id": int}`
- **EXAMPLE_QUESTIONS:** 
  - "Get the profile for customer 123."
  - "What is the contact email for client 45?"
  - "Show me the demographic data for user ID 10."
- **JSON_FORMAT:** `{"tool": "get_customer_detail", "arguments": {"customer_id": 123}}`

---

### 20 TOOL: get_total_supplier_count
* **TOOL_NAME:** `get_total_supplier_count`
* **DESCRIPTION:** Returns the total count of registered suppliers in the system. Use this for quick administrative summaries.
* **KEYWORDS:** count suppliers, total vendors, how many suppliers, wholesale partners count.
* **ARGUMENTS:** `{}`
* **JSON_FORMAT:** `{"tool": "get_total_supplier_count", "arguments": {}}`

---

### 21 TOOL: search_suppliers
* **TOOL_NAME:** `search_suppliers`
* **DESCRIPTION:** Comprehensive search for supplier details including RFC, tax addresses, and phone numbers. Use this for detailed vendor profiling.
* **KEYWORDS:** search suppliers, vendor contact info, supplier RFC lookup, tax address , suppiers id,providers ID, providers.
* **ARGUMENTS:** `{ "id": int, "name": string, "contact_person": string, "rfc": string, "tax_address": string }`
* **EXAMPLE_QUESTIONS:** 
  - "What is the RFC for Marinela?" -> `{"name": "Marinela"}`
  - "Find suppliers located in 'Col. Santa Maria'." -> `{"tax_address": "Santa Maria"}`
  - "Get contact info for supplier ID 2." -> `{"id": 2}`
* **JSON_FORMAT:** `{"tool": "search_suppliers", "arguments": {"name": "Marinela"}}`

---

### 22 TOOL: get_supplier_detail
- **TOOL_NAME:** `get_supplier_detail`
- **DESCRIPTION:** Retrieves the full profile of a specific supplier, including tax identification (RFC/Tax ID), contact email, phone number, and physical address.
- **KEYWORDS:** supplier contact, vendor Tax ID, RFC, supplier address, vendor phone, supplier profile.
- **ARGUMENTS:** `{"supplier_id": int}`
- **EXAMPLE_QUESTIONS:** 
  - "What is the Tax ID (RFC) for supplier 10?"
  - "Show me the contact details and address for vendor 4."
  - "Get the profile for supplier ID 12."
- **JSON_FORMAT:** `{"tool": "get_supplier_detail", "arguments": {"supplier_id": 10}}`

---

### 23 TOOL: get_all_chatbot_users
- **TOOL_NAME:** `get_all_chatbot_users`
- **DESCRIPTION:** Retrieves the complete whitelist of authorized personnel who have permission to interact with the chatbot system.
- **KEYWORDS:** whitelist, bot users, authorized personnel, access list, chatbot permissions.
- **ARGUMENTS:** `{}`
- **EXAMPLE_QUESTIONS:** 
  - "Who is allowed to use this bot?"
  - "Show me the whitelist of authorized users."
  - "List all personnel with chatbot access."
- **JSON_FORMAT:** `{"tool": "get_all_chatbot_users", "arguments": {}}`

---

### 24 TOOL: get_chatbot_user
- **TOOL_NAME:** `get_chatbot_user`
- **DESCRIPTION:** Verifies the specific authorization status and retrieves the last connection details for a user identified by their mobile phone number.
- **KEYWORDS:** verify access, user status check, mobile number lookup, connection details, permission verify.
- **ARGUMENTS:** `{"mobile_number": string}`
- **EXAMPLE_QUESTIONS:** 
  - "Does the number +1234567890 have access?"
  - "Check the last connection for mobile 555-0199."
  - "Verify if this phone number is in the authorized list."
- **JSON_FORMAT:** `{"tool": "get_chatbot_user", "arguments": {"mobile_number": "+1234567890"}}`

---

### 25 TOOL: fetch_chat_history
- **TOOL_NAME:** `fetch_chat_history`
- **DESCRIPTION:** Retrieves the most recent messages from the current active conversation. Use this to resolve pronouns (e.g., "it", "him", "that") or to recall immediate previous instructions.
- **KEYWORDS:** chat history, previous messages, conversation log, context, memory, what was said, repeat that.
- **ARGUMENTS:** `{"telegram_id": int, "limit": int}`
- **EXAMPLE_QUESTIONS:** 
  - "What did I just say?"
  - "Repeat the last thing you told me."
  - "What was the price of the product we were talking about?"
  - "Check the previous messages for the customer ID."
- **JSON_FORMAT:** `{"tool": "fetch_chat_history", "arguments": {"telegram_id": 6596706525, "limit": 5}}`

---

