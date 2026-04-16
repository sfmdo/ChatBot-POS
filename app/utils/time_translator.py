from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from typing import Dict, Optional, Tuple, Any, Callable

class TimeTranslator:
    """
    Central Time Period Handler optimized for English LLM Reasoning.
    """
    
    @staticmethod
    def process_request(request_data: Dict[str, Any], reference_date: Optional[date] = None) -> Dict[str, str]:
        if reference_date is None:
            reference_date = date.today()

        try:
            if "period" in request_data:
                start, end = TimeTranslator._translate_absolute(request_data["period"], reference_date)
            elif "unit" in request_data and "quantity" in request_data:
                start, end = TimeTranslator._calculate_relative(request_data["unit"], request_data["quantity"], reference_date)
            else:
                return {"error": "Unrecognized time request format. Use 'period' or 'unit'/'quantity'."}

            return {
                "start_date": start.isoformat(),
                "end_date": end.isoformat()
            }
        except ValueError as e:
            return {"error": str(e)}

    @staticmethod
    def _translate_absolute(period: str, ref_date: date) -> Tuple[date, date]:
        period = period.lower().strip()
        
        strategies: Dict[str, Callable[[date], Tuple[date, date]]] = {
            "today": lambda d: (d, d),
            "yesterday": lambda d: (d - timedelta(days=1), d - timedelta(days=1)),
            "this_week": lambda d: (d - timedelta(days=d.weekday()), d - timedelta(days=d.weekday()) + timedelta(days=6)),
            "last_week": lambda d: (d - timedelta(days=d.weekday() + 7), d - timedelta(days=d.weekday() + 1)),
            "this_month": lambda d: (d.replace(day=1), (d.replace(day=1) + relativedelta(months=1)) - timedelta(days=1)),
            "last_month": lambda d: ((d.replace(day=1) - relativedelta(months=1)), d.replace(day=1) - timedelta(days=1)),
            "this_year": lambda d: (date(d.year, 1, 1), date(d.year, 12, 31)),
            "last_year": lambda d: (date(d.year - 1, 1, 1), date(d.year - 1, 12, 31)),
            
            "q1": lambda d: (date(d.year, 1, 1), date(d.year, 3, 31)),
            "q2": lambda d: (date(d.year, 4, 1), date(d.year, 6, 30)),
            "q3": lambda d: (date(d.year, 7, 1), date(d.year, 9, 30)),
            "q4": lambda d: (date(d.year, 10, 1), date(d.year, 12, 31)),
        }

        action = strategies.get(period)
        if not action:
            raise ValueError(f"Unknown absolute period: {period}. Valid: {list(strategies.keys())}")
            
        return action(ref_date)

    @staticmethod
    def _calculate_relative(unit: str, quantity: int, ref_date: date) -> Tuple[date, date]:
        unit = unit.lower().strip()
        
        strategies: Dict[str, Callable[[int, date], date]] = {
            "day": lambda q, d: d - timedelta(days=q),
            "week": lambda q, d: d - timedelta(weeks=q),
            "month": lambda q, d: d - relativedelta(months=q),
            "year": lambda q, d: d - relativedelta(years=q),
            "quarter": lambda q, d: d - relativedelta(months=q * 3)
        }

        action = strategies.get(unit)
        if not action:
            raise ValueError(f"Unknown relative unit: {unit}. Valid: {list(strategies.keys())}")

        start_date = action(quantity, ref_date)
        return start_date, ref_date