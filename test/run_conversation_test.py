import json
import asyncio
import re
import logging
from pathlib import Path

# Importaciones de tu arquitectura real
from app.ai.agent_orchestrator import PepeOrchestrator
from app.ai.agent_routes.ai_data_fetch import DataFetchReActAgent
from agent_mcp.client import mcp_manager

# Configuración de Logging para ver los prints de las clases
BASE_DIR = Path(__file__).resolve().parent
JSON_DATA_PATH = BASE_DIR / "integration_test_data.json"

logging.basicConfig(level=logging.INFO, format='%(message)s')

async def test_phase_0_router(logger, test_cases, telegram_id):
    print("\n" + "="*60 + "\n>>> TESTING PHASE 0: MASTER ROUTER\n" + "="*60)
    for case in test_cases:
        print(f"\nCASO: {case['name']}")
        
        orch = PepeOrchestrator(telegram_id, case['message'])
        
        async for chunk in orch.route_request():
                print(f"  Pepe (Final): {chunk}")

async def test_phase_0_5_architect(logger, test_cases, telegram_id):
    print("\n" + "="*60 + "\n>>> TESTING PHASE 0.5: TECHNICAL ARCHITECT\n" + "="*60)
    for case in test_cases:
        print(f"\nCASO: {case['name']}")
        agent = DataFetchReActAgent(
            clean_intent=case['clean_intent'], 
            telegram_id=telegram_id, 
        )
        success = await agent.generate_plan()
        
        if success:
            print(f"Plan generado para el dominio: {agent.domain}")
        else:
            print(f"Error: La fase de planeación falló.")

async def test_phase_4_full_sequence(logger, test_cases, telegram_id):
    print("\n" + "="*60 + "\n>>> TESTING PHASE 4: FULL CONVERSATION\n" + "="*60)
    for turn in test_cases:
        print(f"\n[TURNO {turn['turn']}] User: {turn['user_message']}")
        
        orch = PepeOrchestrator(telegram_id, turn['user_message'])
        

        async for chunk in orch.route_request():
            print(f"  {chunk}")
        
        await asyncio.sleep(1)

async def main():
    await mcp_manager.start()
    
    try:
        with open(JSON_DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        tid = data["telegram_id"]

        await test_phase_0_router(None, data["phase_0_router_tests"], tid)

        await test_phase_0_5_architect(None, data["phase_0_5_architect_tests"], tid)

        await test_phase_4_full_sequence(None, data["phase_4_full_flow_sequence"], tid)
        
    finally:
        await mcp_manager.stop()
        print("\n" + "="*60 + "\nTESTING COMPLETE.")

if __name__ == "__main__":
    asyncio.run(main())