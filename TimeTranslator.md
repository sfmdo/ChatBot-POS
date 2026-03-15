Módulo: Reglas de Traducción de Tiempo (Time Translator)

Propósito: El Agente de IA NUNCA debe calcular fechas (YYYY-MM-DD) manualmente. Para cualquier consulta que requiera un rango de tiempo, el Agente debe delegar el cálculo al motor interno utilizando los siguientes parámetros predefinidos.

Modo 1: Periodos Absolutos (Términos de Negocio)
Si el usuario menciona un lapso de tiempo fijo o un término contable, el Agente debe enviar el parámetro period con uno de los siguientes valores exactos (String):

    hoy / ayer

    esta_semana / semana_pasada

    este_mes / mes_pasado

    q1, q2, q3, q4 (Trimestres del año actual)

    s1, s2 (Semestres del año actual)

    este_año / año_pasado

Modo 2: Periodos Relativos (Retroactivos)
Si el usuario pide información "hacia atrás" desde el día actual (ej. "los últimos 3 meses", "hace 5 días"), el Agente debe enviar dos parámetros:

    unit (String): Acepta únicamente dia, semana, mes, bimestre, trimestre, semestre, o año.

    quantity (Integer): El número de unidades a retroceder (ej. 3).

Ejemplos de Mapeo para el Agente:

    Usuario: "¿Cuánto vendimos el mes pasado?" -> Agente envía: {"period": "mes_pasado"}

    Usuario: "Dime los productos más vendidos de las últimas 2 semanas" -> Agente envía: {"unit": "semana", "quantity": 2}