import json
import asyncio
import datetime
from pathlib import Path

from app.ai.agent_orchestrator import ReActAgent, query_ai
from agent_mcp.client import mcp_manager
class TestLogger:
    """Clase para registrar logs de forma clara en consola y archivo."""
    def __init__(self, filename="integration_test_log.txt"):
        self.filename = filename
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.filename, "w", encoding="utf-8") as f:
            f.write(f"INICIO DE PRUEBAS DE INTEGRACIÓN\nFECHA: {timestamp}\n{'='*60}\n\n")

    def log(self, message):
        print(message)
        with open(self.filename, "a", encoding="utf-8") as f:
            f.write(message + "\n")

    def log_phase(self, phase_name):
        self.log(f"\n\n{'='*20} [FASE: {phase_name}] {'='*20}")

    def log_case(self, case_name):
        self.log(f"\n--- CASO DE PRUEBA: {case_name} ---")


async def test_phase_1_gatekeeper(logger, test_cases):
    """Prueba la función analyze_intent de forma aislada."""
    logger.log_phase("GATEKEEPER (ANALYZE_INTENT)")
    for case in test_cases:
        logger.log_case(case['name'])
        logger.log(f"Input: '{case['message']}'")
        agent = ReActAgent(telegram_id=999, message=case['message'])
        
        try:
            intent_data = await agent.analyze_intent()
            logger.log(f"Output JSON:\n{json.dumps(intent_data, indent=2)}")
            
            # Validación
            errors = []
            for key, expected_value in case['expected'].items():
                if key == "time_args_exist":
                    if expected_value and not intent_data.get("time_arguments"):
                        errors.append("Se esperaban argumentos de tiempo pero no se encontraron.")
                elif intent_data.get(key) != expected_value:
                    errors.append(f"Clave '{key}': Se esperaba '{expected_value}', se obtuvo '{intent_data.get(key)}'")
            
            logger.log(f"RESULTADO: {'✅ ÉXITO' if not errors else f'❌ FALLO: {", ".join(errors)}'}")
        except Exception as e:
            logger.log(f"RESULTADO: ❌ ERROR CRÍTICO - {e}")

async def test_phase_2_react_loop(logger, test_cases):
    """Prueba el método run del agente para verificar su razonamiento."""
    logger.log_phase("REACT LOOP (AGENT.RUN)")
    for case in test_cases:
        logger.log_case(case['name'])
        logger.log(f"Input: '{case['message']}'")
        logger.log(f"Objetivo: {case['description']}")
        agent = ReActAgent(telegram_id=999, message=case['message'])
        
        try:
            # Solo nos interesa el proceso interno, no el resultado final
            logger.log("Observando el proceso del agente (THOUGHTS y TOOL_CALLS):")
            async for chunk in agent.run():
                if "🧠" in chunk or "FINAL ANSWER" in chunk: # Filtramos para ver solo lo importante
                    logger.log(f"  -> {chunk.strip()}")
            logger.log("RESULTADO: ✅ PROCESO COMPLETADO (Revisar logs para calidad del razonamiento)")
        except Exception as e:
            logger.log(f"RESULTADO: ❌ ERROR CRÍTICO - {e}")


async def test_phase_3_pepe_analyst(logger, test_cases):
    """Prueba la función de traducción y formato _translate_to_pepe."""
    logger.log_phase("ANALISTA PEPE (_TRANSLATE_TO_PEPE)")
    for case in test_cases:
        logger.log_case(case['name'])
        logger.log(f"Input (Technical Report): '{case['technical_report']}'")
        agent = ReActAgent(telegram_id=999, message=case['original_message'])
        
        try:
            final_answer = await agent._translate_to_pepe(final_answer=case['technical_report'])
            logger.log(f"Output (Respuesta de Pepe):\n{final_answer}")
            
            missing_keywords = [kw for kw in case["expected_keywords"] if kw not in final_answer]
            logger.log(f"RESULTADO: {'✅ ÉXITO' if not missing_keywords else f'❌ FALLO: Pepe omitió los datos clave: {missing_keywords}'}")
        except Exception as e:
            logger.log(f"RESULTADO: ❌ ERROR CRÍTICO - {e}")


async def test_phase_4_full_conversation(logger, test_cases, telegram_id):
    """Ejecuta una conversación completa usando el orquestador query_ai."""
    logger.log_phase("ORQUESTADOR COMPLETO (QUERY_AI)")
    for turn_data in test_cases:
        logger.log_case(f"Turno {turn_data['turn']}")
        user_message = turn_data['user_message']
        logger.log(f"Input: '{user_message}'")
        
        try:
            logger.log("Respuesta del orquestador:")
            try:
                async for chunk in query_ai(message=user_message, telegram_id=telegram_id):
                    logger.log(f"  -> {chunk.strip()}")
            except Exception as e:
                logger.log(f"¡ORQUESTADOR CRASHEÓ! Error: {e}")
                import traceback
                logger.log(traceback.format_exc()) # Esto te dará la traza completa
            logger.log("RESULTADO: ✅ TURNO COMPLETADO")
        except Exception as e:
            logger.log(f"RESULTADO: ❌ ERROR CRÍTICO - {e}")
        
        await asyncio.sleep(2) # Pausa para simular una conversación real


async def main():
    """Función principal que carga los datos y ejecuta todas las fases de prueba."""
    logger = TestLogger()
    await mcp_manager.start()
    try:
        script_dir = Path(__file__).parent
        json_file_path = script_dir / "integration_test_data.json"
        with open(json_file_path, "r", encoding="utf-8") as f:
            test_data = json.load(f)
    except FileNotFoundError:
        logger.log(f"ERROR: No se encontró el archivo en la ruta esperada: '{json_file_path}'")
        return

    # Ejecutar cada fase de prueba con sus datos correspondientes
    await test_phase_1_gatekeeper(logger, test_data["phase_1_gatekeeper_tests"])
    await test_phase_2_react_loop(logger, test_data["phase_2_react_loop_tests"])
    await test_phase_3_pepe_analyst(logger, test_data["phase_3_pepe_analyst_tests"])
    await test_phase_4_full_conversation(logger, test_data["phase_4_full_conversation_test"], test_data["telegram_id"])

    logger.log("\n\n" + "="*60 + "\nPRUEBAS DE INTEGRACIÓN FINALIZADAS.\n" + "="*60)
    print(f"\nPruebas completadas. Revisa el archivo '{logger.filename}' para ver el análisis detallado.")


if __name__ == "__main__":
    asyncio.run(main())