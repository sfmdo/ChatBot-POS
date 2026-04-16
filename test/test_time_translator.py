import unittest
from datetime import date
from app.utils.time_translator import TimeTranslator

class TestTimeTranslator(unittest.TestCase):
    
    def setUp(self):
        # Reference date: March 14, 2026
        self.ref_date = date(2026, 3, 14)

    # ABSOLUTE PERIOD TESTS (English Keys)

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
        # Q1 should be Jan 1st to March 31st of the current year
        req = {"period": "q1"}
        res = TimeTranslator.process_request(req, self.ref_date)
        self.assertEqual(res["start_date"], "2026-01-01")
        self.assertEqual(res["end_date"], "2026-03-31")
        
    def test_absolute_last_year(self):
        req = {"period": "last_year"}
        res = TimeTranslator.process_request(req, self.ref_date)
        self.assertEqual(res["start_date"], "2025-01-01")
        self.assertEqual(res["end_date"], "2025-12-31")

    # RELATIVE PERIOD TESTS (English Units)

    def test_relative_last_5_days(self):
        req = {"unit": "day", "quantity": 5}
        res = TimeTranslator.process_request(req, self.ref_date)
        # March 14 minus 5 days = March 9
        self.assertEqual(res["start_date"], "2026-03-09")
        self.assertEqual(res["end_date"], "2026-03-14")

    def test_relative_last_2_months(self):
        req = {"unit": "month", "quantity": 2}
        res = TimeTranslator.process_request(req, self.ref_date)
        # March 14 minus 2 months = Jan 14
        self.assertEqual(res["start_date"], "2026-01-14")
        self.assertEqual(res["end_date"], "2026-03-14")

    def test_relative_last_quarter_duration(self):
        req = {"unit": "quarter", "quantity": 1}
        res = TimeTranslator.process_request(req, self.ref_date)
        # March 14 minus 3 months (1 quarter) = Dec 14, 2025
        self.assertEqual(res["start_date"], "2025-12-14")
        self.assertEqual(res["end_date"], "2026-03-14")

    # ERROR HANDLING TESTS (English Messages)

    def test_invalid_absolute_period(self):
        req = {"period": "christmas"}
        res = TimeTranslator.process_request(req, self.ref_date)
        self.assertTrue("error" in res)
        self.assertIn("Unknown absolute period", res["error"])

    def test_invalid_relative_unit(self):
        req = {"unit": "decade", "quantity": 1}
        res = TimeTranslator.process_request(req, self.ref_date)
        self.assertTrue("error" in res)
        self.assertIn("Unknown relative unit", res["error"])

    def test_malformed_request(self):
        # Missing valid keys
        req = {"range": "yesterday"} 
        res = TimeTranslator.process_request(req, self.ref_date)
        self.assertTrue("error" in res)
        self.assertIn("Unrecognized time request format", res["error"])

if __name__ == '__main__':
    unittest.main()