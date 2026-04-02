import aiosqlite
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

DB_PATH = "pos_agent.db"

@asynccontextmanager
async def get_connection():
    """
    Retorna una conexión asíncrona usando un manejador de contexto.
    Asegura que la conexión se cierre correctamente y activa WAL.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        yield db  

async def create_tables():
    """Inicializa las tablas de forma asíncrona."""
    async with get_connection() as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                phone TEXT,
                expires_at TIMESTAMP
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                role TEXT,
                content TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(telegram_id) REFERENCES users(telegram_id)
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS verifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                phone TEXT,
                code TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                is_used BOOLEAN DEFAULT 0,
                FOREIGN KEY(telegram_id) REFERENCES users(telegram_id)
            )
        ''')
        await db.commit()

async def save_message(telegram_id: int, role: str, content: str):
    """Guarda un mensaje de forma asíncrona."""
    async with get_connection() as db:
        await db.execute(
            "INSERT INTO messages (telegram_id, role, content) VALUES (?, ?, ?)",
            (telegram_id, role, content)
        )
        await db.commit()

async def get_user_context(telegram_id: int, limit: int = 10):
    """Obtiene los últimos N mensajes formateados para la IA."""
    async with get_connection() as db:
        async with db.execute('''
            SELECT role, content FROM (
                SELECT role, content, id 
                FROM messages 
                WHERE telegram_id = ? 
                    AND content != ''
                ORDER BY id DESC 
                LIMIT ?
            ) ORDER BY id ASC
        ''', (telegram_id, limit)) as cursor:
            rows = await cursor.fetchall()
    
    return [
        {
            "role": str(row[0]).lower().strip(),
            "content": str(row[1]) if row[1] else ""
        } 
        for row in rows
    ]

async def verify_and_register_user(telegram_id: int, phone: str):
    """Vincula al usuario y le da 24 horas de acceso."""
    expiry_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
    
    async with get_connection() as db:
        await db.execute('''
            INSERT OR REPLACE INTO users (telegram_id, phone, expires_at)
            VALUES (?, ?, ?)
        ''', (telegram_id, phone, expiry_date))
        await db.commit()
    print(f"Usuario {telegram_id} vinculado con el teléfono {phone}")

async def verify_active_access(telegram_id: int) -> bool:
    """Revisa si el acceso sigue vigente."""
    async with get_connection() as db:
        async with db.execute(
            'SELECT expires_at FROM users WHERE telegram_id = ?', 
            (telegram_id,)
        ) as cursor:
            result = await cursor.fetchone()
    
    if not result:
        return False
    
    expiry_date = datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S')
    return datetime.now() <= expiry_date