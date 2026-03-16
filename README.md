# POS Agent - Telegram Bot

Este proyecto consiste en un bot de Telegram diseñado para interactuar con los datos de un sistema de Punto de Venta (https://github.com/Omescobell/Punto-de-Venta). Funciona como un asistente virtual que autentica a los empleados autorizados mediante un sistema de lista blanca y mantiene un registro de la conversación, aislando el contexto por cada usuario de manera segura.

Actualmente, el sistema gestiona la capa de **Autenticación (Lista Blanca)** y la **Memoria de Contexto**. La integración con el modelo de lenguaje de IA (Ollama) representa la siguiente fase del desarrollo.

## Características Principales

*   **Autenticación por Teléfono (Lista Blanca):** El bot omite el uso de contraseñas tradicionales, utilizando la validación nativa de contactos de Telegram y contrastándola directamente contra la API del POS.

*   **Gestión de Sesiones (24 Horas):** Para optimizar el rendimiento y evitar la saturación de la API externa, el bot genera una sesión local en SQLite con una vigencia de 24 horas.

*   **Aislamiento de Contexto:** Cada interacción se almacena y se vincula exclusivamente a la `telegram_id` del usuario. Esto garantiza la privacidad de los datos y previene la mezcla de contextos entre diferentes empleados al procesar respuestas con la IA.

*   **Smoke Testing Integrado:** Incorpora pruebas unitarias diseñadas para validar la disponibilidad y el correcto funcionamiento de los endpoints de la API del POS previos a la ejecución en producción.

## Arquitectura y Flujo de Operación

El sistema opera bajo dos flujos de ejecución principales:
**1. Flujo de Autenticación (`/start`)**

*   1. El usuario inicializa la conversación mediante el comando `/start`.

*   2. El bot despliega un teclado nativo solicitando compartir el contacto (`request_contact=True)`.

*   3. Al recibir el objeto de contacto, el sistema invoca la función `obtener_telefonos_autorizados()` hacia la API del POS.

*   4. Si el número de teléfono existe en la lista de autorización, se registra una sesión en la base de datos local (`pos_agent.db`) otorgando acceso por un periodo de 24 horas.

**2. Flujo de Mensajería y Validación (Middleware)**

*   1. El usuario envía un mensaje de texto.

*   2. El middleware intercepta la petición y verifica en la base de datos local si la `telegram_id` posee una sesión activa.

*   3. Acceso denegado: Se detiene la ejecución y se instruye al usuario a renovar su sesión mediante /start.

*   4. Acceso concedido: Se registra el mensaje en la tabla `mensajes`, se recupera el historial reciente de dicho usuario para construir el contexto, y se prepara el payload para su envío al motor de IA.

## Estructura del Proyecto
```Plaintext
├── app/
│   ├── bot/
│   │   └── handlers.py       # Controladores de Telegram (comandos, contactos y texto)
│   ├── models/
│   │   └── database.py       # Lógica de persistencia en SQLite local (Sesiones y Contexto)
│   └── services/
│       └── api_client.py     # Cliente HTTP para la API del POS
├── tests/
│   └── test_api.py           # Pruebas de humo (Smoke tests) para los endpoints externos
├── pos_agent.db              # Base de datos local SQLite (generada automáticamente)
├── main.py                   # Punto de entrada para la ejecución del bot
└── README.md
```

## Esquema de Base de Datos Local (`pos_agent.db`)

La base de datos SQLite gestiona la persistencia de sesiones y el historial conversacional:

*   **Tabla `usuarios`:** Almacena los identificadores de sesión. Campos principales: `telegram_id`(Primary Key), `telefono`, y `expira_el` (Timestamp de caducidad).

*   **Tabla `mensajes`:** Almacena el historial conversacional aislado. Campos principales: `telegram_id` (Foreign Key), `rol` ("user" o "assistant"), `contenido`, y `fecha`.