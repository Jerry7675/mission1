import asyncio
from app.debate_manager import DebateManager

async def test_debate():
    manager = DebateManager()
    result = await manager.run_debate(topic="Should AI be regulated?", rounds=2)
    print(f"Debate Topic: {result['topic']}")
    for round in result["transcript"]:
        print(f"\nRound {round['round']}:")
        print(f"Pro: {round.get('pro', 'N/A')}")
        print(f"Con: {round.get('con', 'N/A')}")
    print(f"\nVerdict: {result['verdict']}")

asyncio.run(test_debate())