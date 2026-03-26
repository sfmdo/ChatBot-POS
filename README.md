# POS Agent - Telegram Bot

This project is an intelligent Telegram bot assistant designed to interface with a Point of Sale (POS) system ([GitHub Repository](https://github.com/Omescobell/Punto-de-Venta)). It acts as a virtual bridge, allowing authorized employees to query sales, inventory, and customer data using natural language processed by a local LLM (Ollama).

## Key Features

*   **Native Authentication (Whitelist):** No passwords required. The bot validates the user's Telegram contact against the POS authorized phone list.
*   **Session Management:** Local SQLite persistence creates 24-hour sessions to minimize external API calls.
*   **Context Isolation:** Conversation history is strictly bound to the `telegram_id`, ensuring data privacy between different employees.
*   **MCP Integration (Model Context Protocol):** Uses a modular architecture to expose POS tools and resources to the LLM.
*   **Automated Time Translation:** A dedicated logic layer prevents the LLM from hallucinating dates, translating business terms (e.g., "last month") into structured API parameters.
*   **Integrated Testing:** Includes smoke tests for API integration, database integrity, and time translation logic.

---

## Project Structure

```bash
├── app
│   ├── bot
│   │   ├── client.py         # Telegram Client setup
│   │   └── handlers.py       # Command and message controllers
│   ├── mcp                   # Model Context Protocol layer
│   │   ├── mcp_resources.py  # Static/Dynamic resources for the LLM
│   │   ├── mcp_server.py     # MCP Server implementation
│   │   ├── mcp_tools.py      # Tool definitions for the LLM
│   │   └── resources         # Documentation for LLM prompting
│   ├── models
│   │   └── database.py       # SQLite persistence (English schema)
│   ├── rag                   # Future RAG implementation
│   ├── services              # POS API Clients
│   │   ├── analytics_api.py
│   │   ├── api_client.py     # Base HTTP Client
│   │   ├── chatbot_users_api.py
│   │   ├── customers_api.py
│   │   ├── ia_service.py     # Ollama/LLM interface
│   │   ├── orders_api.py
│   │   ├── products_api.py
│   │   └── suppliers_api.py
│   └── utils
│       └── time_translator.py # Date logic handler
├── ia_config
│   └── Modelfile             # Ollama configuration
├── main.py                   # Entry point
├── test                      # Test Suite
│   ├── test_api_integraion.py
│   ├── test_bd.py
│   ├── test_qwen.py
│   └── test_time_translator.py
└── pyproject.toml
```

## 🗄 Local Database Schema (`pos_agent.db`)

*   **`users` Table:** Manages sessions.
    *   `telegram_id` (PK), `phone`, `expires_at`.
*   **`messages` Table:** Isolated conversation logs.
    *   `telegram_id` (FK), `role` ("user"/"assistant"), `content`, `created_at`.

---

## ⚙️ Configuration

To run this project, you need to create a `.env` file in the root directory and populate it with the following variables:

```env
# Telegram Bot Token (from @BotFather)
TELEGRAM_TOKEN=your_telegram_bot_token_here

# POS API Credentials (for backend authentication)
BOT_API_EMAIL=your_email@example.com
BOT_API_PASSWORD=your_secure_password

# External API URLs
POS_API_URL=http://your-pos-api-url.com
OLLAMA_BASE_URL=http://localhost:11434

# AI Model Configuration
OLLAMA_MODEL=pepe_model_name
```

### Setup Instructions:
1.  **Telegram:** Obtain your token from BotFather.
2.  **POS API:** Ensure the `BOT_API_EMAIL` is registered in your POS system with the necessary permissions.
3.  **Ollama:** Ensure the Ollama service is running and the model specified in `OLLAMA_MODEL` is pulled (`ollama pull <model_name>`).

---

## Time Translator Module

**Purpose:** The AI Agent must **NEVER** calculate dates (YYYY-MM-DD) manually. To avoid errors, the Agent delegates calculations to the internal engine using these predefined parameters:

### Mode 1: Absolute Periods (Business Terms)
If the user mentions fixed timeframes, the Agent sends the `period` parameter with these exact strings:
- `hoy` (today) / `ayer` (yesterday)
- `esta_semana` (this week) / `semana_pasada` (last week)
- `este_mes` (this month) / `mes_pasado` (last month)
- `q1, q2, q3, q4` (Current year quarters)
- `s1, s2` (Current year semesters)
- `este_año` (this year) / `año_pasado` (last year)

### Mode 2: Relative Periods (Retroactive)
If the user asks for "look-back" info (e.g., "last 3 months"), the Agent sends:
- **`unit` (String):** `dia`, `semana`, `mes`, `bimestre`, `trimestre`, `semestre`, or `año`.
- **`quantity` (Integer):** The number of units to go back.

---

## POS Service Catalog (MCP Tools)

The LLM uses these tools to interact with the POS system:

### 1. Analytics Module (`analytics_api`)
*   `get_sales_summary(start_date, end_date)`: Financial performance, average ticket, and peak hours.
*   `get_product_ranking(limit, criterion, start_date, end_date)`: Top/Bottom selling products (`criterion`: "most", "least", "both").
*   `get_low_stock(threshold)`: Products at or below the inventory threshold.
*   `get_dead_inventory(reference_date)`: Stocked items with no sales since the reference date.
*   `get_sales_velocity(identifier, period_days)`: Daily sales rate and estimated "days until out of stock."
*   `get_inventory_valuation(product_identifier)`: Total cost, potential revenue, and profit margin.

### 2. Orders & Tickets (`orders_api`)
*   `get_order_detail(order_id)`: Itemized breakdown, taxes (VAT), and discounts for a specific transaction.
*   `search_recent_orders(ticket_folio, status, limit)`: Search by folio or status (PENDING, PAID, CANCELLED).

### 3. Chatbot Users (`chatbot_users_api`)
*   `get_all_chatbot_users()`: List of all authorized names and phone numbers.
*   `get_chatbot_user(mobile_number)`: Access verification and last interaction timestamp.

### 4. Products & Promotions (`products_api`)
*   `get_all_products()`: Complete catalog including SKU, price, and "available to sell" stock.
*   `get_all_promotions()`: List active discounts (e.g., Black Friday) and validity dates.
*   `get_promotions_by_product(product_id)`: Check specific discounts for a single item.

### 5. Customers & Loyalty (`customers_api`)
*   `get_all_customers()`: List of customers, "Frequent Flyer" status, and loyalty points.
*   `get_customer_points_history(customer_id)`: Audit log of EARN and REDEEM point events.
*   `get_customer_credit_history(customer_id)`: Store credit ledger (CHARGE and PAYMENT events).