# backend/app/debate_manager.py
import ollama
import asyncio
from typing import Dict, List
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
                "name": "mistral:7b",
                "system_prompt": "You're a competitive debater. Present strong arguments with evidence."
            },
            "con": {
                "name": "gemma2:9b", 
                "system_prompt": "You're a critical analyst. Find flaws and counterarguments."
            },
            "judge": {
                "name": "deepseek-r1:7b",  
                "system_prompt": "You're an impartial judge. Evaluate arguments technically."
            }
        }

    async def _load_model(self, role: str) -> str:
        model = self.model_config[role]
        if model["name"] not in self.active_models:
            if len(self.active_models) >= 2:
                await self._unload_oldest_model()  # still skips actual deletion
            try:
                client = ollama.AsyncClient()
                await client.pull(model["name"])
                self.active_models.add(model["name"])
                logger.info(f"Loaded model: {model['name']}")
            except Exception as e:
                logger.error(f"Model load failed: {str(e)}")
                available_models = await self._get_available_models()
                if available_models:
                    fallback_model = available_models[0]
                    logger.info(f"Using fallback model: {fallback_model}")
                    self.model_config[role]["name"] = fallback_model
                    self.active_models.add(fallback_model)
                    return fallback_model
                raise
        return model["name"]

    async def _get_available_models(self) -> List[str]:
        try:
            client = ollama.AsyncClient()
            models = await client.list()
            return [model['name'] for model in models.get('models', [])]
        except Exception as e:
            logger.error(f"Failed to get available models: {str(e)}")
            return []

    async def _unload_oldest_model(self):
        if self.active_models:
            model_to_unload = next(iter(self.active_models))
            logger.info(f"Skipping deletion to retain model: {model_to_unload}")
            self.active_models.remove(model_to_unload)

    async def run_debate(self, topic: str = None, rounds: int = 5) -> Dict:
        try:
            topic = topic or get_random_topic()
            transcript = []
            if not await self.llm.health_check():
                raise RuntimeError("Ollama service is not running. Please start with: ollama serve")

            pro_model = await self._load_model("pro")
            con_model = await self._load_model("con")

            for round_num in range(1, rounds + 1):
                logger.info(f"Starting round {round_num}")
                round_data = await self._conduct_round(
                    topic, round_num, pro_model, con_model
                )
                transcript.append(round_data)
                try:
                    self.chroma.log_debate_round(round_data, metadata=round_data["metadata"])
                except Exception as e:
                    logger.warning(f"Failed to log round to ChromaDB: {str(e)}")

            verdict = await self._get_verdict(transcript)
            return {"topic": topic, "transcript": transcript, "verdict": verdict}
        except Exception as e:
            logger.error(f"Debate failed: {str(e)}")
            return {
                "topic": topic or "Unknown",
                "transcript": [],
                "verdict": f"Debate failed: {str(e)}",
                "error": True
            }
        finally:
            await self._unload_all_models()

    async def _conduct_round(self, topic: str, round_num: int, pro_model: str, con_model: str) -> Dict:
        try:
            if round_num % 2 == 1:
                first_speaker, second_speaker = "pro", "con"
                first_model, second_model = pro_model, con_model
            else:
                first_speaker, second_speaker = "con", "pro"
                first_model, second_model = con_model, pro_model

            first_prompt = f"Debate Topic: {topic}\nRound {round_num}\nYour Position: {'Argue FOR the topic' if first_speaker == 'pro' else 'Argue AGAINST the topic'}\nPresent your argument:"
            first_response = await self._generate_response(first_model, first_prompt, self.model_config[first_speaker]["system_prompt"])

            counter_prompt = f"Debate Topic: {topic}\nRound {round_num}\nOpponent's Argument: {first_response}\nYour Position: {'Argue FOR the topic' if second_speaker == 'pro' else 'Argue AGAINST the topic'}\nCounter this argument:"
            second_response = await self._generate_response(second_model, counter_prompt, self.model_config[second_speaker]["system_prompt"])

            return {
                "round_number": round_num,
                "content": f"Round {round_num}: {first_speaker.upper()}: {first_response}\n{second_speaker.upper()}: {second_response}",
                "pro": first_response if first_speaker == "pro" else second_response,
                "con": first_response if first_speaker == "con" else second_response,
                "metadata": {
                    "round": round_num,
                    "topic": topic,
                    "pro_model": pro_model,
                    "con_model": con_model,
                    "first_speaker": first_speaker,
                    "second_speaker": second_speaker
                }
            }
        except Exception as e:
            logger.error(f"Round {round_num} failed: {str(e)}")
            return {
                "round_number": round_num,
                "content": f"Round {round_num} failed: {str(e)}",
                "pro": "[Error occurred]",
                "con": "[Error occurred]",
                "metadata": {
                    "round": round_num,
                    "topic": topic,
                    "error": str(e)
                }
            }

    async def _generate_response(self, model_name: str, prompt: str, system: str) -> str:
        try:
            client = ollama.AsyncClient()
            response = await asyncio.wait_for(
                client.generate(
                    model=model_name,
                    prompt=prompt,
                    system=system,
                    options={
                        "temperature": 0.7,
                        "num_ctx": 2048,
                        "num_predict": 512
                    }
                ),
                timeout=60
            )
            return response.get("response", "[No response generated]")
        except asyncio.TimeoutError:
            logger.warning(f"Model timeout: {model_name}")
            return "[Model response timed out]"
        except Exception as e:
            logger.error(f"Generation failed for {model_name}: {str(e)}")
            return f"[Model error: {str(e)}]"

    async def _get_verdict(self, transcript: List[Dict]) -> str:
        try:
            judge_model = await self._load_model("judge")
            debate_summary = "\n".join(
                f"Round {r['round_number']}:\nPro: {r.get('pro', 'N/A')}\nCon: {r.get('con', 'N/A')}"
                for r in transcript
            )
            verdict = await self._generate_response(
                model_name=judge_model,
                prompt=f"Debate Transcript:\n{debate_summary}\n\nJudge the strongest arguments and declare a winner:",
                system=self.model_config["judge"]["system_prompt"]
            )
            return verdict
        except Exception as e:
            logger.error(f"Verdict generation failed: {str(e)}")
            return "Unable to generate verdict due to technical issues"

    async def _unload_all_models(self):
        for model in list(self.active_models):
            logger.info(f"Skipping unload of: {model}")
            self.active_models.remove(model)
