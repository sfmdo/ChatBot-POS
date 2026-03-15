import unittest
from datetime import date
from app.utils.time_translator import TimeTranslator

class TestTimeTranslator(unittest.TestCase):
    
    def setUp(self):
        self.ref_date = date(2026, 3, 14)

    # PRUEBAS DE PERIODOS ABSOLUTOS

    def test_absolute_hoy(self):
        req = {"period": "hoy"}
        res = TimeTranslator.process_request(req, self.ref_date)
        self.assertEqual(res["start_date"], "2026-03-14")
        self.assertEqual(res["end_date"], "2026-03-14")

    def test_absolute_este_mes(self):
        req = {"period": "este_mes"}
        res = TimeTranslator.process_request(req, self.ref_date)
        self.assertEqual(res["start_date"], "2026-03-01")
        self.assertEqual(res["end_date"], "2026-03-31")

    def test_absolute_q1(self):
        # Q1 siempre debe ser del 1 de Enero al 31 de Marzo del año actual
        req = {"period": "q1"}
        res = TimeTranslator.process_request(req, self.ref_date)
        self.assertEqual(res["start_date"], "2026-01-01")
        self.assertEqual(res["end_date"], "2026-03-31")
        
    def test_absolute_año_pasado(self):
        req = {"period": "año_pasado"}
        res = TimeTranslator.process_request(req, self.ref_date)
        self.assertEqual(res["start_date"], "2025-01-01")
        self.assertEqual(res["end_date"], "2025-12-31")

    # PRUEBAS DE PERIODOS RELATIVOS

    def test_relative_ultimos_5_dias(self):
        req = {"unit": "dia", "quantity": 5}
        res = TimeTranslator.process_request(req, self.ref_date)
        # 14 de marzo menos 5 días = 9 de marzo
        self.assertEqual(res["start_date"], "2026-03-09")
        self.assertEqual(res["end_date"], "2026-03-14")

    def test_relative_ultimos_2_meses(self):
        req = {"unit": "mes", "quantity": 2}
        res = TimeTranslator.process_request(req, self.ref_date)
        # 14 de marzo menos 2 meses = 14 de enero
        self.assertEqual(res["start_date"], "2026-01-14")
        self.assertEqual(res["end_date"], "2026-03-14")

    def test_relative_ultimo_trimestre_duracion(self):
        req = {"unit": "trimestre", "quantity": 1}
        res = TimeTranslator.process_request(req, self.ref_date)
        # 14 de marzo menos 3 meses (1 trimestre) = 14 de diciembre del año pasado
        self.assertEqual(res["start_date"], "2025-12-14")
        self.assertEqual(res["end_date"], "2026-03-14")

    # PRUEBAS DE MANEJO DE ERRORES

    def test_invalid_absolute_period(self):
        req = {"period": "navidad"}
        res = TimeTranslator.process_request(req, self.ref_date)
        self.assertTrue("error" in res)
        self.assertIn("desconocido", res["error"])

    def test_invalid_relative_unit(self):
        req = {"unit": "decada", "quantity": 1}
        res = TimeTranslator.process_request(req, self.ref_date)
        self.assertTrue("error" in res)
        self.assertIn("desconocida", res["error"])

    def test_malformed_request(self):
        # Faltan claves válidas
        req = {"rango": "ayer"} 
        res = TimeTranslator.process_request(req, self.ref_date)
        self.assertTrue("error" in res)
        self.assertEqual(res["error"], "Formato de petición de tiempo no reconocido.")

if __name__ == '__main__':
    unittest.main()