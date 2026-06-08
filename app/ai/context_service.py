import datetime
from pathlib import Path
from enum import Enum

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class PromptRoutes(Enum):
    GATEKEEPER = "app/ai/prompts/gatekeeper.md"
    DATA_RETRIEVAL = "app/aiprompts/data_retrieval.md"
    PEPE_ANALYST = "app/aiprompts/pepe_analyst.md"
    PEPE_REJECTION = "app/aiprompts/pepe_rejection.md"
    DATA_PLANING = "app/aiprompts/data_planing.md"
    CONTEXT_ANALYST = "app/aiprompts/pepe_context_analyst.md"
    GENERAL_CHAT = "app/ai/prompts/pepe_chat.md"
    PEPE_CONTEXT_ANALYST = "app/ai/prompts/pepe_context_analyst.md"

def get_prompt(route):
    """
    Lee el archivo markdown del prompt.
    'route' es un miembro del Enum PromptRoutes.
    """
    relative_path = route.value if hasattr(route, 'value') else route
    absolute_path = BASE_DIR / relative_path

    try:
        with open(absolute_path, 'r', encoding='utf-8') as mdprompt:
            return mdprompt.read()
    except FileNotFoundError:
        print(f"ERROR: No se encontró el archivo en: {absolute_path}")
        raise

def get_data_retrieval_context():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    system_prompt = get_prompt(PromptRoutes.DATA_RETRIEVAL)
    return f"{system_prompt} \n## SESSION DATA - Timestamp: {now}"

def get_pepe_analyst_context(language: str, user_request: str, technical_info: str):
    system_prompt = get_prompt(PromptRoutes.PEPE_ANALYST)
    return f"""
{system_prompt}\n
### INPUT DATA
- **USER REQUEST**: {user_request}
- **TECHNICAL REPORT TO ANALYZE**: {technical_info}

### FINAL RESPONSE PROTOCOL
- Output ONLY the final response exactly as the user will read it on Telegram.
- WHEN YOU FINILIZE YOUR ANALYSIS, USE THE **FINAL RESPONSE**: AND THEN GIVE THE FINAL ANSWER TO THE USER
- Language: **{language}**
"""

def get_gatekeeper_context(history: str, user_petition: str) -> str:
    system_prompt = get_prompt(PromptRoutes.GATEKEEPER)
    return f"""
{system_prompt}
### REAL INPUT TO ANALYZE:

**CHAT HISTORY**:
{history}

**CURRENT USER REQUEST**:
{user_petition}

Analyze the request and output the strict JSON below:
(DO NOT wrap the output in markdown blocks like ```json. ONLY output the raw JSON brackets).
"""

def get_data_planing_context():
    system_context = get_prompt(PromptRoutes.DATA_PLANING)
    return system_context

def get_pepe_rejection_context():
    system_context = get_prompt(PromptRoutes.PEPE_REJECTION)
    return f"""
{system_context}\n
**FINAL ANSWER:**
(Generate the executive, friendly, and professional response in the requested language).
"""

def get_pepe_chat_context(language: str):
    system_prompt = get_prompt(PromptRoutes.GENERAL_CHAT)
    return f"{system_prompt}\n**INSTRUCTION**: GIVE THE FINAL ANSER IN THIS LANGUAGE:{language}"

def get_pepe_drill_down_context(history: str, language: str):
    """
    Carga el prompt base de análisis y le inyecta los inputs dinámicos 
    del historial y el idioma.
    """
    system_prompts = get_prompt(PromptRoutes.PEPE_CONTEXT_ANALYST)
    
    inputs_section = f"""
### INPUTS TO ANALYZE:
- **BUSINESS LOGS**:
{history}
- **FINAL ANSWER LANGUAGE**: {language}
---
**INSTRUCTION**: Use the logs above to answer the user request. Output your analysis followed by the label **FINAL ANSWER:** in the specified language.
"""
    return f"{system_prompts}\n{inputs_section}"