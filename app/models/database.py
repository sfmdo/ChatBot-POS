import sqlite3
from datetime import datetime, timedelta

DB_PATH = "pos_agent.db"

def obtener_conexion():
    return sqlite3.connect(DB_PATH)

def crear_tablas():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            telegram_id INTEGER PRIMARY KEY,
            telefono TEXT,
            expira_el TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mensajes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            rol TEXT, -- Puede ser 'user' (usuario) o 'assistant' (Ollama)
            contenido TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(telegram_id) REFERENCES usuarios(telegram_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS verificaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            telefono TEXT,
            codigo TEXT,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_expiracion TIMESTAMP,
            usado BOOLEAN DEFAULT 0,
            FOREIGN KEY(telegram_id) REFERENCES usuarios(telegram_id)
        )
    ''')

    conexion.commit()
    conexion.close()

def guardar_mensaje(telegram_id, rol, contenido):
    """Guarda un mensaje en la base de datos."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "INSERT INTO mensajes (telegram_id, rol, contenido) VALUES (?, ?, ?)",
        (telegram_id, rol, contenido)
    )
    conexion.commit()
    conexion.close()

def obtener_contexto_usuario(telegram_id, limite=10):
    """Obtiene los últimos N mensajes de un usuario para enviárselos a Ollama."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    cursor.execute('''
        SELECT rol, contenido FROM (
            SELECT rol, contenido, fecha 
            FROM mensajes 
            WHERE telegram_id = ? 
            ORDER BY fecha DESC 
            LIMIT ?
        ) ORDER BY fecha ASC
    ''', (telegram_id, limite))
    
    mensajes = cursor.fetchall()
    conexion.close()
    
    contexto = [{"role": fila[0], "content": fila[1]} for fila in mensajes]
    return contexto

def verificar_y_registrar_usuario(telegram_id, telefono):
    """
    Se ejecuta en el /start. 
    Guarda la vinculación y le da 24 horas de acceso.
    """
    fecha_expira = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
    
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO usuarios (telegram_id, telefono, expira_el)
        VALUES (?, ?, ?)
    ''', (telegram_id, telefono, fecha_expira))
    
    conexion.commit()
    conexion.close()
    print(f"Usuario {telegram_id} vinculado con el teléfono {telefono}")

def registrar_verificacion_usuario(telegram_id, telefono):
    """
    Guarda o actualiza el acceso del usuario por 24 horas.
    Se llama cuando el usuario comparte su contacto exitosamente.
    """
    from datetime import datetime, timedelta
    fecha_expira = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
    
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO usuarios (telegram_id, telefono, expira_el)
        VALUES (?, ?, ?)
    ''', (telegram_id, telefono, fecha_expira))
    
    conexion.commit()
    conexion.close()

def verificar_acceso_activo(telegram_id):
    """
    El 'cadenero'. Revisa si el ID de Telegram tiene permiso vigente.
    Retorna True si tiene acceso, False si no.
    """
    from datetime import datetime
    
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    cursor.execute('SELECT expira_el FROM usuarios WHERE telegram_id = ?', (telegram_id,))
    resultado = cursor.fetchone()
    conexion.close()
    
    if not resultado:
        return False
    
    fecha_expira_str = resultado[0]
    fecha_expira = datetime.strptime(fecha_expira_str, '%Y-%m-%d %H:%M:%S')
    
    if datetime.now() > fecha_expira:
        return False
        
    return True

crear_tablas()