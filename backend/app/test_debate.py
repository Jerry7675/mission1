# test_debate.py
import asyncio
from app.debate_manager import DebateManager

async def test_debate():
    dm = DebateManager()
    result = await dm.run_debate(topic="Should AI be regulated?", rounds=2)

    print(f"\nDebate Topic: {result['topic']}")
    
    for round in result["transcript"]:
        print(f"\n--- Round {round['round_number']} ---")
        print("Pro:", round["pro"])
        print("Con:", round["con"])
        print("Content:\n", round["content"])

    print("\nFinal Verdict:")
    print(result["verdict"])

if __name__ == "__main__":
    asyncio.run(test_debate())
