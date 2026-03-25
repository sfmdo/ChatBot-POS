import sqlite3
from datetime import datetime, timedelta

DB_PATH = "pos_agent.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def create_tables():
    connection = get_connection()
    cursor = connection.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            phone TEXT,
            expires_at TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            role TEXT, -- Puede ser 'user' (usuario) o 'assistant' (Ollama)
            content TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(telegram_id) REFERENCES users(telegram_id)
        )
    ''')
    
    cursor.execute('''
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

    connection.commit()
    connection.close()

def save_message(telegram_id, role, content):
    """Guarda un mensaje en la base de datos."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO messages (telegram_id, role, content) VALUES (?, ?, ?)",
        (telegram_id, role, content)
    )
    connection.commit()
    connection.close()

def get_user_context(telegram_id, limit=10):
    """Obtiene los últimos N mensajes de un usuario formateados para Ollama."""
    connection = get_connection()
    cursor = connection.cursor()
    
    cursor.execute('''
        SELECT role, content FROM (
            SELECT role, content, id 
            FROM messages 
            WHERE telegram_id = ? 
                AND content != ''
            ORDER BY id DESC 
            LIMIT ?
        ) ORDER BY id ASC
    ''', (telegram_id, limit))
    
    rows = cursor.fetchall()
    connection.close()
    
    context = [
        {
            "role": str(row[0]).lower().strip(),
            "content": str(row[1]) if row[1] else ""
        } 
        for row in rows
    ]
    return context

def verify_and_register_user(telegram_id, phone):
    """
    Se ejecuta en el /start. 
    Guarda la vinculación y le da 24 horas de acceso.
    """
    expiry_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
    
    connection = get_connection()
    cursor = connection.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO users (telegram_id, phone, expires_at)
        VALUES (?, ?, ?)
    ''', (telegram_id, phone, expiry_date))
    
    connection.commit()
    connection.close()
    print(f"Usuario {telegram_id} vinculado con el teléfono {phone}")

def register_user_verification(telegram_id, phone):
    """
    Guarda o actualiza el acceso del usuario por 24 horas.
    Se llama cuando el usuario comparte su contacto exitosamente.
    """
    from datetime import datetime, timedelta
    expiry_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
    
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users (telegram_id, phone, expires_at)
        VALUES (?, ?, ?)
    ''', (telegram_id, phone, expiry_date))
    
    connection.commit()
    connection.close()

def verify_active_access(telegram_id):
    """
    Revisa si el ID de Telegram tiene permiso vigente.
    Retorna True si tiene acceso, False si no.
    """
    from datetime import datetime
    
    connection = get_connection()
    cursor = connection.cursor()
    
    cursor.execute('SELECT expires_at FROM users WHERE telegram_id = ?', (telegram_id,))
    result = cursor.fetchone()
    connection.close()
    
    if not result:
        return False
    
    expiry_date_str = result[0]
    expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d %H:%M:%S')
    
    if datetime.now() > expiry_date:
        return False
        
    return True

create_tables()