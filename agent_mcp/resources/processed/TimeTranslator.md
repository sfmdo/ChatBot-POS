# MODULE: BILINGUAL_TIME_MAPPER
# ROLE: SPANISH_INPUT -> INTERNAL_LOGIC -> ENGLISH_API
# RULE: AI MUST NEVER CALCULATE DATES. MAP SPANISH QUERIES TO THESE PARAMETERS.

## MODE_1: PERIODS (Parameter: `period`)
- "hoy" (today) -> `{"period": "hoy"}`
- "ayer" (yesterday) -> `{"period": "ayer"}`
- "esta semana" (this week) -> `{"period": "esta_semana"}`
- "semana pasada" (last week) -> `{"period": "semana_pasada"}`
- "este mes" (this month) -> `{"period": "este_mes"}`
- "mes pasado" (last month) -> `{"period": "mes_pasado"}`
- "trimestres" (quarters) -> `{"period": "q1"}`...`{"period": "q4"}`
- "semestres" (semesters) -> `{"period": "s1"}`, `{"period": "s2"}`
- "este año" (this year) -> `{"period": "este_año"}`
- "año pasado" (last year) -> `{"period": "año_pasado"}`

## MODE_2: RETROACTIVE_LOOKBACK (Parameters: `unit`, `quantity`)
- Unit Mapping: 
  "días" -> `dia`, "semanas" -> `semana`, "meses" -> `mes`, "años" -> `año`.
- Example Logic:
  "últimos 3 meses" -> `{"unit": "mes", "quantity": 3}`
  "hace 2 semanas" -> `{"unit": "semana", "quantity": 2}`

## FEW_SHOT_BILINGUAL
- User: "¿Cuánto vendimos ayer?" -> `get_sales_summary(period="ayer")`
- User: "Top 5 productos del mes pasado" -> `get_product_ranking(limit=5, period="mes_pasado")`