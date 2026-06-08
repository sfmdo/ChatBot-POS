import re
import json
from typing import Dict,Any

def _parse_response(content: str) -> Dict[str, Any]:
        """Extrae la intención (Tool o Final Answer) de la respuesta del LLM."""
        if re.search(r"TOOL_CALL", content, re.IGNORECASE):
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                raw_json_string = json_match.group(0)
                print(f"\n--- RAW JSON FROM LLM ---\n{raw_json_string}\n-------------------------")
                try:
                    return {"type": "tool", "data": json.loads(raw_json_string)}
                except:
                    return {"type": "error", "data": "Invalid JSON format."}
        
        if re.search(r"FINAL\s*ANSWER", content, re.IGNORECASE):
            final_part = re.split(r"FINAL\s*ANSWER:?", content, flags=re.IGNORECASE)[-1]
            final_text = final_part.replace("**", "").strip().replace(":","").strip()
            return {"type": "final", "data": final_text}
        
        return {"type": "fallback", "data": content.strip()}