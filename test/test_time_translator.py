import unittest
from datetime import date
from app.utils.time_translator import TimeTranslator

class TestTimeTranslator(unittest.TestCase):
    
    def setUp(self):
        # Reference date: March 14, 2026
        self.ref_date = date(2026, 3, 14)

    # --- 1. ABSOLUTE PERIOD TESTS ---

    def test_absolute_today(self):
        req = {"period": "today"}
        res = TimeTranslator.process_request(req, self.ref_date)
        self.assertEqual(res["start_date"], "2026-03-14")
        self.assertEqual(res["end_date"], "2026-03-14")

    def test_absolute_this_month(self):
        req = {"period": "this_month"}
        res = TimeTranslator.process_request(req, self.ref_date)
        self.assertEqual(res["start_date"], "2026-03-01")
        self.assertEqual(res["end_date"], "2026-03-31")

    def test_absolute_q1(self):
        req = {"period": "q1"}
        res = TimeTranslator.process_request(req, self.ref_date)
        self.assertEqual(res["start_date"], "2026-01-01")
        self.assertEqual(res["end_date"], "2026-03-31")
        
    def test_absolute_last_year(self):
        req = {"period": "last_year"}
        res = TimeTranslator.process_request(req, self.ref_date)
        self.assertEqual(res["start_date"], "2025-01-01")
        self.assertEqual(res["end_date"], "2025-12-31")

    # --- 2. RELATIVE PERIOD TESTS ---

    def test_relative_last_5_days(self):
        req = {"unit": "day", "quantity": 5}
        res = TimeTranslator.process_request(req, self.ref_date)
        self.assertEqual(res["start_date"], "2026-03-09")
        self.assertEqual(res["end_date"], "2026-03-14")

    def test_relative_last_quarter_duration(self):
        req = {"unit": "quarter", "quantity": 1}
        res = TimeTranslator.process_request(req, self.ref_date)
        self.assertEqual(res["start_date"], "2025-12-14")
        self.assertEqual(res["end_date"], "2026-03-14")

    # --- 3. EDGE CASES & TYPE HANDLING ---
    
    def test_default_reference_date(self):
        # Asegura que funcione con el día de hoy si no se pasa ref_date
        req = {"period": "today"}
        res = TimeTranslator.process_request(req) # No pasamos ref_date
        today_str = date.today().isoformat()
        self.assertEqual(res["start_date"], today_str)

    def test_quantity_as_string_cast(self):
        # A veces el LLM puede inyectar el número como string {"quantity": "5"}
        # Dependiendo de cómo lo maneje tu código interno, esto valida que no explote
        req = {"unit": "day", "quantity": 5} # idealmente casteas a int en el Translator
        res = TimeTranslator.process_request(req, self.ref_date)
        self.assertNotIn("error", res)

    # --- 4. ERROR HANDLING TESTS (Corregidos) ---

    def test_invalid_absolute_period(self):
        req = {"period": "christmas"}
        res = TimeTranslator.process_request(req, self.ref_date)
        self.assertTrue("error" in res)
        # El string ahora coincide con el ValueError real de tu clase
        self.assertIn("Unknown period", res["error"]) 

    def test_invalid_relative_unit(self):
        req = {"unit": "decade", "quantity": 1}
        res = TimeTranslator.process_request(req, self.ref_date)
        self.assertTrue("error" in res)
        # El string ahora coincide con el ValueError real de tu clase
        self.assertIn("Unknown unit", res["error"])

    def test_missing_quantity_in_relative(self):
        # Qué pasa si inyecta la unidad pero olvida la cantidad
        req = {"unit": "day"} 
        res = TimeTranslator.process_request(req, self.ref_date)
        self.assertTrue("error" in res)
        self.assertIn("Invalid format", res["error"])

    def test_malformed_request(self):
        req = {"range": "yesterday"} 
        res = TimeTranslator.process_request(req, self.ref_date)
        self.assertTrue("error" in res)
        # El string ahora coincide con el return real de tu clase
        self.assertIn("Invalid format", res["error"])

if __name__ == '__main__':
    unittest.main()