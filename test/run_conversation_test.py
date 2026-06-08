import json
import asyncio
import datetime
import re
from pathlib import Path

# Importaciones de tu nueva estructura
from app.ai.agent_orchestrator import PepeOrchestrator
from app.ai.agent_routes.ai_data_fetch import DataFetchReActAgent
from app.ai.llm_service import call_openai_standard
from app.ai.context_service import get_gatekeeper_context
from agent_mcp.client import mcp_manager

BASE_DIR = Path(__file__).resolve().parent
JSON_DATA_PATH = BASE_DIR / "integration_test_data.json"
model = 1
class TestLogger:
    def __init__(self, filename="pepe_v2_integration_log.txt"):
        self.filename = filename
        with open(self.filename, "w", encoding="utf-8") as f:
            f.write(f"PEPE 2.0 - INTEGRATION TESTS\nDATE: {datetime.datetime.now()}\n{'='*60}\n")

    def log(self, message):
        print(message)
        with open(self.filename, "a", encoding="utf-8") as f:
            f.write(message + "\n")

async def test_phase_0_router(logger, test_cases):
    logger.log("\n>>> PHASE 0: MASTER ROUTER LOGIC")
    for case in test_cases:
        logger.log(f"\nTest: {case['name']} | Input: {case['message']}")
        history = case.get("history_simulated", "No history")
        prompt = get_gatekeeper_context(history=history, user_petition=case['message'])
        
        raw_res = await call_openai_standard([{"role": "user", "content": prompt}],model=model)
        json_match = re.search(r"\{.*\}", raw_res, re.DOTALL) # type: ignore
        
        if json_match:
            res = json.loads(json_match.group(0))
            success = all(res.get(k) == v for k, v in case['expected'].items())
            logger.log(f"Detected Route: {res.get('route')} | Clean Intent: {res.get('clean_intent')}")
            logger.log(f"RESULT: {'✅ PASS' if success else '❌ FAIL'}")
        else:
            logger.log("❌ FAIL: No JSON returned by Router")

async def test_phase_0_5_architect(logger, test_cases):
    logger.log("\n>>> PHASE 0.5: TECHNICAL ARCHITECT (PLANNING)")
    for case in test_cases:
        logger.log(f"\nTest: {case['name']} | Clean Intent: {case['clean_intent']}")

        agent = DataFetchReActAgent(clean_intent=case['clean_intent'], telegram_id=999,log_summary="")
        
        success = await agent.generate_plan()
        if success:
            logger.log(f"Plan: {json.dumps(agent.plan_data, indent=2)}")
            # Validar dominio
            domain_ok = agent.domain == case['expected']['domain']
            logger.log(f"Domain Validation: {'✅' if domain_ok else '❌'}")
        else:
            logger.log("❌ FAIL: Planning phase failed")

async def test_phase_4_full_sequence(logger, test_cases, telegram_id):
    logger.log("\n>>> PHASE 4: FULL ORCHESTRATION SEQUENCE")
    for turn in test_cases:
        logger.log(f"\n[TURN {turn['turn']}] User: {turn['user_message']}")
        orchestrator = PepeOrchestrator(telegram_id, turn['user_message'])
        
        async for chunk in orchestrator.route_request():
            # Filtramos para no llenar el log de pensamientos si no queremos, 
            # pero aquí los mostramos con prefijo
            if "🛡️" in chunk or "🧠" in chunk or "🏗️" in chunk:
                logger.log(f"  Step: {chunk}")
            else:
                logger.log(f"  Pepe: {chunk}")
        
        logger.log(f"Turn {turn['turn']} completed.")
        await asyncio.sleep(1)

async def main():
    logger = TestLogger()
    await mcp_manager.start()
    
    try:
        with open(JSON_DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # Ejecución de fases
        await test_phase_0_router(logger, data["phase_0_router_tests"])
        await test_phase_0_5_architect(logger, data["phase_0_5_architect_tests"])
        await test_phase_4_full_sequence(logger, data["phase_4_full_sequence"], data["telegram_id"])
        
    finally:
        await mcp_manager.stop()
        logger.log("\n" + "="*60 + "\nTESTING COMPLETE.")

if __name__ == "__main__":
    asyncio.run(main())