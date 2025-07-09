# mission1/backend/app/services/model_runner.py

import subprocess
import time
import asyncio
from app.utils.prompts import PROMPTS

def run_model(model_name: str, prompt: str) -> str:
    """
    Runs a local model using Ollama CLI and returns its output as a string.
    """
    try:
        result = subprocess.run(
            ["ollama", "run", model_name],
            input=prompt.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=180  # seconds
        )
        return result.stdout.decode()
    except subprocess.TimeoutExpired:
        return f"[ERROR] Model '{model_name}' timed out."
    except Exception as e:
        return f"[ERROR] {str(e)}"


def run_debate_session(topic: str, rounds: int = 3) -> dict:
    """
    Runs a full debate session between Mistral and Gemma, judged by DeepSeek.
    Returns the structured debate history and final verdict.
    """
    context = f"Debate Topic: {topic}\n"
    history = []

    for round_num in range(1, rounds + 1):
        # Agent A - Mistral
        prompt_a = f"{PROMPTS['mistral']}\n\nContext:\n{context}"
        response_a = run_model("mistral", prompt_a).strip()
        history.append({"agent": "Mistral", "round": round_num, "response": response_a})
        context += f"\nAgent A (Mistral): {response_a}\n"
        time.sleep(1)

        # Agent B - Gemma
        prompt_b = f"{PROMPTS['gemma']}\n\nContext:\n{context}"
        response_b = run_model("gemma", prompt_b).strip()
        history.append({"agent": "Gemma", "round": round_num, "response": response_b})
        context += f"\nAgent B (Gemma): {response_b}\n"
        time.sleep(1)

    # Judge - DeepSeek
    judge_prompt = f"{PROMPTS['deepseek']}\n\nDebate Transcript:\n{context}"
    verdict = run_model("deepseek", judge_prompt).strip()

    return {
        "topic": topic,
        "rounds": history,
        "verdict": verdict,
        "timestamp": time.time()
    }

class ModelSessionManager:
    def __init__(self):
        self.active_sessions = {}
        self.model_queue = asyncio.Queue()
    
    async def get_model_session(self, model_name: str):
        if model_name not in self.active_sessions:
            await self.load_model(model_name)
        return self.active_sessions[model_name]
    
    async def load_model(self, model_name: str):
        # Implement persistent model loading
        pass