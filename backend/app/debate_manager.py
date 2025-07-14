# backend/app/debate_manager.py
import ollama
import asyncio
from typing import Dict, List, Tuple
from .chroma_handler import ChromaHandler
from . import logger
from .utils.topics import get_random_topic
from .models import OllamaWrapper

class DebateManager:
    def __init__(self):
        self.chroma = ChromaHandler()
        self.llm = OllamaWrapper() 
        self.active_models = set()
        self.model_config = {
            "pro": {
                "name": "mistral",
                "system_prompt": "You're a competitive debater. Present strong arguments with evidence."
            },
            "con": {
                "name": "deepseek-r1", 
                "system_prompt": "You're a critical analyst. Find flaws and counterarguments."
            },
            "judge": {
                "name": "gemma3",
                "system_prompt": "You're an impartial judge. Evaluate arguments technically."
            }
        }

    async def _load_model(self, role: str) -> str:
        """Safely load a model with memory management"""
        model = self.model_config[role]
        if model["name"] not in self.active_models:
            if len(self.active_models) >= 2:  # Never exceed 2 loaded models
                await self._unload_oldest_model()
            try:
                await ollama.pull(model["name"])
                self.active_models.add(model["name"])
                logger.info(f"Loaded model: {model['name']}")
            except Exception as e:
                logger.error(f"Model load failed: {str(e)}")
                raise
        return model["name"]

    async def _unload_oldest_model(self):
        """Unload least recently used model"""
        if self.active_models:
            model_to_unload = next(iter(self.active_models))
            try:
                await ollama.delete(model_to_unload)
                self.active_models.remove(model_to_unload)
                logger.info(f"Unloaded model: {model_to_unload}")
            except Exception as e:
                logger.error(f"Model unload failed: {str(e)}")

    async def run_debate(self, topic: str = None, rounds: int = 5) -> Dict:
        """Main debate orchestration"""
        try:
            # Initialize
            topic = topic or get_random_topic()
            transcript = []
            
            # Load initial models
            pro_model = await self._load_model("pro")
            con_model = await self._load_model("con")

            # Debate rounds
            for round_num in range(1, rounds + 1):
                round_data = await self._conduct_round(
                    topic, 
                    round_num, 
                    pro_model, 
                    con_model
                )
                transcript.append(round_data)
                self.chroma.log_debate_round(round_data)

            # Final judgment
            verdict = await self._get_verdict(transcript)
            return {"topic": topic, "transcript": transcript, "verdict": verdict}
            
        finally:
            # Cleanup
            await self._unload_all_models()

    async def _conduct_round(self, topic: str, round_num: int, pro_model: str, con_model: str) -> Dict:
        """Run one debate round"""
        # Alternate who speaks first
        if round_num % 2 == 1:
            speaker, opponent = "pro", "con"
        else:
            speaker, opponent = "con", "pro"

        # Generate arguments
        speaker_response = await self._generate_response(
            model_name=pro_model if speaker == "pro" else con_model,
            prompt=f"Debate Topic: {topic}\nYour Position: Argue FOR the topic" if speaker == "pro" else f"Debate Topic: {topic}\nYour Position: Argue AGAINST the topic",
            system=self.model_config[speaker]["system_prompt"]
        )

        opponent_response = await self._generate_response(
            model_name=pro_model if opponent == "pro" else con_model,
            prompt=f"Counter this argument: {speaker_response}",
            system=self.model_config[opponent]["system_prompt"]
        )

        return {
            "round": round_num,
            speaker: speaker_response,
            opponent: opponent_response
        }

    async def _generate_response(self, model_name: str, prompt: str, system: str) -> str:
        """Safe model generation with timeout"""
        try:
            response = await asyncio.wait_for(
                ollama.generate(
                    model=model_name,
                    prompt=prompt,
                    system=system,
                    options={
                        "temperature": 0.7,
                        "num_ctx": 2048
                    }
                ),
                timeout=60  # 1 minute timeout
            )
            return response["response"]
        except asyncio.TimeoutError:
            logger.warning(f"Model timeout: {model_name}")
            return "[Model response timed out]"
        except Exception as e:
            logger.error(f"Generation failed: {str(e)}")
            return "[Model error occurred]"

    async def _get_verdict(self, transcript: List[Dict]) -> str:
        """Load judge model for final decision"""
        try:
            judge_model = await self._load_model("judge")
            debate_summary = "\n".join(
                f"Round {r['round']}:\nPro: {r.get('pro', 'N/A')}\nCon: {r.get('con', 'N/A')}"
                for r in transcript
            )
            
            verdict = await self._generate_response(
                model_name=judge_model,
                prompt=f"Debate Transcript:\n{debate_summary}\n\nJudge the strongest arguments:",
                system=self.model_config["judge"]["system_prompt"]
            )
            return verdict
        finally:
            await self._unload_model("judge")

    async def _unload_all_models(self):
        """Cleanup all loaded models"""
        for model in list(self.active_models):
            try:
                await ollama.delete(model)
                self.active_models.remove(model)
            except Exception as e:
                logger.error(f"Failed to unload {model}: {str(e)}")