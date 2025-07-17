import ollama
import asyncio
from typing import Dict, List, AsyncGenerator
from .chroma_handler import ChromaHandler
from . import logger
import re

class DebateManager:
    def __init__(self):
        self.chroma = ChromaHandler()
        self.active_models = set()
        self.model_config = {
            "pro": {
                "name": "mistral:7b",
                "system_prompt": "You're a passionate debater. Construct persuasive, evidence-backed arguments defending your position with charisma and facts."
            },
            "con": {
                "name": "gemma2:9b",
                "system_prompt": "You're a sharp analyst. Refute arguments convincingly with logic, flaws, and counterexamples."
            },
            "judge": {
                "name": "deepseek-r1:7b",
                "system_prompt": "You are a fair judge. Critically evaluate the strength of both arguments and declare a clear winner with justification."
            }
        }

    def _clean_response(self, text: str) -> str:
        if not text:
            return "No response."
        # Strip common internal cues like "Think:" or hallucinated prefixes
        text = re.sub(r"(?i)^think:.*?\n", "", text)
        text = re.sub(r"(?i)^assistant: ?", "", text)
        return text.strip()

    async def stream_debate(self, topic: str = None, rounds: int = 5) -> AsyncGenerator[dict, None]:
        transcript = []
        try:
            client = ollama.AsyncClient()
            await client.show(self.model_config["pro"]["name"])  # Health check

            pro_model = await self._load_model("pro")
            con_model = await self._load_model("con")

            for round_num in range(1, rounds + 1):
                logger.info(f"Streaming round {round_num}")
                round_data = await self._conduct_round(topic, round_num, pro_model, con_model)
                transcript.append(round_data)

                try:
                    self.chroma.log_debate_round(round_data, metadata=round_data["metadata"])
                except Exception as e:
                    logger.warning(f"ChromaDB logging failed: {str(e)}")

                yield {"type": "round_update", "data": round_data}

            verdict = await self._get_verdict(topic, transcript)
            yield {"type": "verdict", "data": {"topic": topic, "verdict": verdict}}

        except Exception as e:
            logger.error(f"Debate failed: {str(e)}")
            yield {"type": "error", "message": str(e)}
        finally:
            await self._unload_all_models()

    async def run_debate(self, topic: str = None, rounds: int = 5) -> Dict:
        transcript = []
        try:
            pro_model = await self._load_model("pro")
            con_model = await self._load_model("con")

            for round_num in range(1, rounds + 1):
                logger.info(f"Starting round {round_num}")
                round_data = await self._conduct_round(topic, round_num, pro_model, con_model)
                transcript.append(round_data)

                try:
                    self.chroma.log_debate_round(round_data, metadata=round_data["metadata"])
                except Exception as e:
                    logger.warning(f"ChromaDB logging failed: {str(e)}")

            verdict = await self._get_verdict(topic, transcript)
            return {"topic": topic, "transcript": transcript, "verdict": verdict}
        except Exception as e:
            logger.error(f"Debate failed: {str(e)}")
            return {"topic": topic, "transcript": [], "verdict": f"Debate failed: {str(e)}", "error": True}
        finally:
            await self._unload_all_models()

    async def _load_model(self, role: str) -> str:
        model = self.model_config[role]
        if model["name"] not in self.active_models:
            if len(self.active_models) >= 2:
                await self._unload_oldest_model()
            try:
                client = ollama.AsyncClient()
                await client.pull(model["name"])
                self.active_models.add(model["name"])
                logger.info(f"Loaded model: {model['name']}")
            except Exception as e:
                logger.error(f"Model load failed: {str(e)}")
                available = await self._get_available_models()
                fallback = available[0] if available else None
                if fallback:
                    self.model_config[role]["name"] = fallback
                    self.active_models.add(fallback)
                    return fallback
                raise
        return model["name"]

    async def _get_available_models(self) -> List[str]:
        try:
            client = ollama.AsyncClient()
            models = await client.list()
            return [m['name'] for m in models.get("models", [])]
        except Exception as e:
            logger.error(f"Fetching models failed: {str(e)}")
            return []

    async def _unload_oldest_model(self):
        if self.active_models:
            model = next(iter(self.active_models))
            self.active_models.remove(model)
            logger.info(f"Retaining model (skipping unload): {model}")

    async def _unload_all_models(self):
        for model in list(self.active_models):
            logger.info(f"Unloading model (simulated): {model}")
            self.active_models.remove(model)

    async def _conduct_round(self, topic: str, round_num: int, pro_model: str, con_model: str) -> Dict:
        try:
            first, second = ("pro", "con") if round_num % 2 == 1 else ("con", "pro")
            model_first = pro_model if first == "pro" else con_model
            model_second = con_model if second == "con" else pro_model

            intro_line = f"🔥 Round {round_num} | Topic: {topic}\n"
            prompt_1 = f"{intro_line}You're speaking first. Argue {'FOR' if first == 'pro' else 'AGAINST'} this topic compellingly:"
            raw_response_1 = await self._generate_response(model_first, prompt_1, self.model_config[first]["system_prompt"])
            response_1 = self._clean_response(raw_response_1)

            prompt_2 = f"{intro_line}Your opponent said:\n\"{response_1}\"\nNow it's your turn. Present a strong {'counter' if second != first else 'follow-up'}:"
            raw_response_2 = await self._generate_response(model_second, prompt_2, self.model_config[second]["system_prompt"])
            response_2 = self._clean_response(raw_response_2)

            return {
                "round_number": round_num,
                "content": f"{first.upper()}: {response_1}\n{second.upper()}: {response_2}",
                "pro": response_1 if first == "pro" else response_2,
                "con": response_1 if first == "con" else response_2,
                "metadata": {
                    "topic": topic,
                    "round": round_num,
                    "pro_model": pro_model,
                    "con_model": con_model,
                    "first_speaker": first,
                    "second_speaker": second
                }
            }

        except Exception as e:
            logger.error(f"Round {round_num} error: {str(e)}")
            return {
                "round_number": round_num,
                "content": f"Error during round {round_num}: {str(e)}",
                "metadata": {"topic": topic, "round": round_num, "error": str(e)}
            }

    async def _generate_response(self, model_name: str, prompt: str, system: str) -> str:
        try:
            client = ollama.AsyncClient()
            result = await asyncio.wait_for(
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
            return result.get("response", "[No response]")
        except asyncio.TimeoutError:
            logger.warning(f"{model_name} timed out.")
            return "[Timed out]"
        except Exception as e:
            logger.error(f"{model_name} failed: {str(e)}")
            return f"[Error: {str(e)}]"

    async def _get_verdict(self, topic: str, transcript: List[Dict]) -> str:
        try:
            judge_model = await self._load_model("judge")
            rounds_summary = "\n".join(
                f"Round {r['round_number']}:\nPro: {r.get('pro', '')}\nCon: {r.get('con', '')}"
                for r in transcript
            )
            final_prompt = (
                f"Debate Topic: {topic}\n{rounds_summary}\n\n"
                "Judge: Who argued more effectively across all rounds? Justify your answer and clearly state the winner."
            )
            verdict_raw = await self._generate_response(judge_model, final_prompt, self.model_config["judge"]["system_prompt"])
            return self._clean_response(verdict_raw)
        except Exception as e:
            logger.error(f"Verdict generation failed: {str(e)}")
            return "Unable to decide winner."
