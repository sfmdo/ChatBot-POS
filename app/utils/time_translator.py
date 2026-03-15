# app/utils/time_translator.py
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from typing import Dict, Optional, Tuple, Any, Callable

class TimeTranslator:
    """
    Manejador Central de Periodos de Tiempo.
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
                return {"error": "Formato de petición de tiempo no reconocido."}

            return {
                "start_date": start.isoformat(),
                "end_date": end.isoformat()
            }
        except ValueError as e:
            return {"error": str(e)}

    @staticmethod
    def _translate_absolute(period: str, ref_date: date) -> Tuple[date, date]:
        """Traductor optimizado mediante un Diccionario de Funciones (Strategy Pattern)."""
        period = period.lower()
        
        strategies: Dict[str, Callable[[date], Tuple[date, date]]] = {
            "hoy": lambda d: (d, d),
            "ayer": lambda d: (d - timedelta(days=1), d - timedelta(days=1)),
            "esta_semana": lambda d: (d - timedelta(days=d.weekday()), d - timedelta(days=d.weekday()) + timedelta(days=6)),
            "semana_pasada": lambda d: (d - timedelta(days=d.weekday() + 7), d - timedelta(days=d.weekday() + 1)),
            "este_mes": lambda d: (d.replace(day=1), (d.replace(day=1) + relativedelta(months=1)) - timedelta(days=1)),
            "mes_pasado": lambda d: ((d.replace(day=1) - relativedelta(months=1)), d.replace(day=1) - timedelta(days=1)),
            "q1": lambda d: (date(d.year, 1, 1), date(d.year, 3, 31)),
            "q2": lambda d: (date(d.year, 4, 1), date(d.year, 6, 30)),
            "q3": lambda d: (date(d.year, 7, 1), date(d.year, 9, 30)),
            "q4": lambda d: (date(d.year, 10, 1), date(d.year, 12, 31)),
            "s1": lambda d: (date(d.year, 1, 1), date(d.year, 6, 30)),
            "s2": lambda d: (date(d.year, 7, 1), date(d.year, 12, 31)),
            "este_año": lambda d: (date(d.year, 1, 1), date(d.year, 12, 31)),
            "año_pasado": lambda d: (date(d.year - 1, 1, 1), date(d.year - 1, 12, 31))
        }

        action = strategies.get(period)
        if not action:
            raise ValueError(f"Periodo absoluto desconocido: {period}")
            
        return action(ref_date)

    @staticmethod
    def _calculate_relative(unit: str, quantity: int, ref_date: date) -> Tuple[date, date]:
        """Calculador relativo optimizado con Diccionario."""
        unit = unit.lower()
        
        strategies: Dict[str, Callable[[int, date], date]] = {
            "dia": lambda q, d: d - timedelta(days=q),
            "semana": lambda q, d: d - timedelta(weeks=q),
            "mes": lambda q, d: d - relativedelta(months=q),
            "bimestre": lambda q, d: d - relativedelta(months=q * 2),
            "trimestre": lambda q, d: d - relativedelta(months=q * 3),
            "semestre": lambda q, d: d - relativedelta(months=q * 6),
            "año": lambda q, d: d - relativedelta(years=q)
        }

        action = strategies.get(unit)
        if not action:
            raise ValueError(f"Unidad de tiempo relativa desconocida: {unit}")

        start_date = action(quantity, ref_date)
        return start_date, ref_date