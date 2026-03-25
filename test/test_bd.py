import unittest
import os
import sqlite3
from datetime import datetime, timedelta

import app.models.database as db

class TestDatabase(unittest.TestCase):
    # Cambiar a valores reales
    TEST_TELEGRAM_ID = 6596706525
    TEST_PHONE = "523313473397"
    TEST_DB_PATH = "test_pos_agent.db"

    def setUp(self):
        """Se ejecuta ANTES de cada prueba. Prepara el terreno limpio."""
        db.DB_PATH = self.TEST_DB_PATH
        
        if os.path.exists(self.TEST_DB_PATH):
            os.remove(self.TEST_DB_PATH)
            
        db.create_tables()

    def tearDown(self):
        """Se ejecuta DESPUÉS de cada prueba. Limpia la basura."""
        if os.path.exists(self.TEST_DB_PATH):
            os.remove(self.TEST_DB_PATH)

    def test_verify_new_user_access(self):
        """Un usuario que no está registrado no debería tener acceso."""
        has_access = db.verify_active_access(self.TEST_TELEGRAM_ID)
        self.assertFalse(has_access, "El cadenero dejó pasar a alguien que no está registrado")

    def test_register_and_grant_access(self):
        """Al registrar un usuario, el cadenero debe dejarlo pasar."""
        db.verify_and_register_user(self.TEST_TELEGRAM_ID, self.TEST_PHONE)
        has_access = db.verify_active_access(self.TEST_TELEGRAM_ID)
        self.assertTrue(has_access, "El cadenero no dejó pasar a un usuario recién registrado")

    def test_expired_access(self):
        """Si pasaron las 24 horas, el cadenero debe bloquearlo."""
        db.verify_and_register_user(self.TEST_TELEGRAM_ID, self.TEST_PHONE)

        connection = db.get_connection()
        cursor = connection.cursor()
        past_date = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('UPDATE users SET expires_at = ? WHERE telegram_id = ?', 
                    (past_date, self.TEST_TELEGRAM_ID))
        connection.commit()
        connection.close()
        
        has_access = db.verify_active_access(self.TEST_TELEGRAM_ID)
        self.assertFalse(has_access, "El cadenero dejó pasar a un usuario con suscripción vencida")

    def test_save_and_get_message_context(self):
        """Verifica que el historial de chat se guarde y recupere en orden cronológico."""
        db.verify_and_register_user(self.TEST_TELEGRAM_ID, self.TEST_PHONE)
        
        db.save_message(self.TEST_TELEGRAM_ID, "user", "Hola Pepe")
        db.save_message(self.TEST_TELEGRAM_ID, "assistant", "¡Hola! ¿En qué te ayudo?")
        db.save_message(self.TEST_TELEGRAM_ID, "user", "¿Qué clima hace?")
        
        context = db.get_user_context(self.TEST_TELEGRAM_ID, limit=2)
        
        self.assertEqual(len(context), 2, "No respetó el límite de mensajes de la memoria")
        
        self.assertEqual(context[0]["role"], "assistant")
        self.assertEqual(context[0]["content"], "¡Hola! ¿En qué te ayudo?")
        
        self.assertEqual(context[1]["role"], "user")
        self.assertEqual(context[1]["content"], "¿Qué clima hace?")

    def test_isolated_user(self):
        """Verifica que un usuario no lea los mensajes de otro."""
        OTHER_ID = 111222333
        
        db.verify_and_register_user(self.TEST_TELEGRAM_ID, self.TEST_PHONE)
        db.verify_and_register_user(OTHER_ID, "00000000")

        db.save_message(self.TEST_TELEGRAM_ID, "user", "Secreto de mi negocio")
        db.save_message(OTHER_ID, "user", "Hola soy otro men")
        
        main_context = db.get_user_context(self.TEST_TELEGRAM_ID)
        
        self.assertEqual(len(main_context), 1)
        self.assertEqual(main_context[0]["content"], "Secreto de mi negocio")

if __name__ == '__main__':
    unittest.main()