# mission1/backend/app/api/websocket.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.model_runner import run_model
from app.utils.prompts import PROMPTS
import asyncio
from app.db.database import get_db
from app.db.schemas import DebateSession, DebateRound

async def save_debate_to_db(topic: str, rounds: list, verdict: str):
    db = next(get_db())
    session = DebateSession(topic=topic, verdict=verdict)
    db.add(session)
    db.commit()
    # Save rounds...

router = APIRouter()

@router.websocket("/ws/debate")
async def debate_websocket(websocket: WebSocket):
    await websocket.accept()

    try:
        # Receive debate topic and number of rounds from frontend
        init_data = await websocket.receive_json()
        topic = init_data.get("topic", "Should AI be regulated?")
        rounds = init_data.get("rounds", 3)

        context = f"Debate Topic: {topic}\n"

        for i in range(1, rounds + 1):
            # Agent A - Mistral
            prompt_a = f"{PROMPTS['mistral']}\n\nContext:\n{context}"
            response_a = run_model("mistral", prompt_a).strip()
            context += f"\nAgent A (Mistral): {response_a}\n"
            await websocket.send_json({"agent": "Mistral", "round": i, "response": response_a})
            await asyncio.sleep(1)

            # Agent B - Gemma
            prompt_b = f"{PROMPTS['gemma']}\n\nContext:\n{context}"
            response_b = run_model("gemma", prompt_b).strip()
            context += f"\nAgent B (Gemma): {response_b}\n"
            await websocket.send_json({"agent": "Gemma", "round": i, "response": response_b})
            await asyncio.sleep(1)

        # Judge - DeepSeek
        judge_prompt = f"{PROMPTS['deepseek']}\n\nDebate Transcript:\n{context}"
        verdict = run_model("deepseek", judge_prompt).strip()
        await websocket.send_json({"agent": "Judge", "verdict": verdict})

    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        await websocket.send_json({"error": str(e)})
