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
                "system_prompt": (
                    "You're the CHAMPION of this topic. Your job: argue FOR it with unstoppable passion, logic, and tailored style.\n\n"
                    "🧠 FORMAT ADAPTATION RULES:\n"
                    "• If the topic is EDUCATIONAL or TECHNICAL: be clear, informative, and structured. Use facts, examples, and real-world applications.\n"
                    "• If the topic is FUN or LIGHTHEARTED: be witty, confident, and creative. Use humor and engaging language.\n"
                    "• If the topic is CONTROVERSIAL: stay respectful but fierce. Use strong arguments without attacking individuals.\n\n"
                    "🧾 GENERAL FORMAT:\n"
                    "• Punchy 1-line opener\n"
                    "• 3–5 bulletproof points\n"
                    "• Killer closing line\n"
                    "• Use confident tone and active voice\n\n"
                    "EXAMPLE STYLE:\n"
                    "'This topic is UNSTOPPABLE and here's why:'\n"
                    "• Point 1 with reason\n"
                    "• Point 2 with example\n"
                    "• Point 3 that crushes opposition\n"
                    "'Case closed.'"
                )
            },
            "con": {
                "name": "gemma2:9b",
                "system_prompt": (
                    "You're the DESTROYER of flawed ideas. Your job: argue AGAINST the topic with logic, precision, and adaptive tone.\n\n"
                    "🧠 FORMAT ADAPTATION RULES:\n"
                    "• If the topic is EDUCATIONAL or TECHNICAL: critique weaknesses with evidence and analysis.\n"
                    "• If the topic is FUN or LIGHTHEARTED: use playful sarcasm or wit to expose flaws.\n"
                    "• If the topic is CONTROVERSIAL: highlight real-world risks, avoid personal attacks.\n\n"
                    "🧾 GENERAL FORMAT:\n"
                    "• Sharp 1-line opener\n"
                    "• 3–5 strong rebuttals or criticisms\n"
                    "• Mic-drop closing statement\n"
                    "• Use confident, critical tone\n\n"
                    "EXAMPLE STYLE:\n"
                    "'Hold up – this idea has serious issues:'\n"
                    "• Weak point with fact\n"
                    "• Risk with consequence\n"
                    "• Fatal flaw that ends the debate\n"
                    "'It just doesn’t hold up.'"
                )
            },
            "judge": {
                "name": "deepseek-r1:7b",
                "system_prompt": (
                    "You're the MASTER JUDGE of this intellectual battle. Analyze both sides fairly, adapting tone to the topic’s nature.\n\n"
                    "🧠 FORMAT ADAPTATION RULES:\n"
                    "• For EDUCATIONAL/TECHNICAL debates: prioritize clarity, data usage, and reasoning.\n"
                    "• For FUN or CREATIVE debates: highlight cleverness and style.\n"
                    "• For CONTROVERSIAL topics: weigh emotional impact, logic, and respect.\n\n"
                    "🧾 VERDICT FORMAT:\n"
                    "• 1-2 line recap of the fight\n"
                    "• Score both sides: Logic, Evidence, Impact (1–10)\n"
                    "• Highlight best arguments\n"
                    "• Declare a winner and explain why\n"
                    "• Final score summary\n\n"
                    "EXAMPLE:\n"
                    "'ROUND SUMMARY:'\n"
                    "Pro brought: [key points]\n"
                    "Con countered: [main rebuttals]\n\n"
                    "SCORES:\n"
                    "Pro: Logic 8/10, Evidence 7/10, Impact 9/10 = 24/30\n"
                    "Con: Logic 6/10, Evidence 8/10, Impact 7/10 = 21/30\n\n"
                    "'WINNER: Pro — because their argument hit hardest and held together.'"
                )
            },
           
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

            for round_num in range(1, rounds + 1):
                logger.info(f"Streaming round {round_num}")
                round_data = await self._conduct_round(topic, round_num)
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

    async def run_debate(self, topic: str = None, rounds: int = 5) -> Dict:
        transcript = []
        try:
            for round_num in range(1, rounds + 1):
                logger.info(f"Starting round {round_num}")
                round_data = await self._conduct_round(topic, round_num)
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

    async def _load_model(self, role: str) -> str:
        model = self.model_config[role]
        if model["name"] not in self.active_models:
            if len(self.active_models) >= 1:
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

    async def _unload_model(self, model_name: str):
        if model_name in self.active_models:
            logger.info(f"Unloading model: {model_name}")
            self.active_models.remove(model_name)
            

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
            logger.info(f"Unloading oldest model: {model}")
            self.active_models.remove(model)
           

    async def _conduct_round(self, topic: str, round_num: int) -> Dict:
        try:
            first, second = ("pro", "con") if round_num % 2 == 1 else ("con", "pro")

            intro_line = f" Round {round_num} | Topic: {topic}\n"
            prompt_1 = f"{intro_line}You're speaking first. Argue {'FOR' if first == 'pro' else 'AGAINST'} this topic compellingly:"

            # Load, generate, unload first model
            model_first = await self._load_model(first)
            raw_response_1 = await self._generate_response(model_first, prompt_1, self.model_config[first]["system_prompt"])
            response_1 = self._clean_response(raw_response_1)
            await self._unload_model(model_first)

            prompt_2 = f"{intro_line}Your opponent said:\n\"{response_1}\"\nNow it's your turn. Present a strong counter:"
            model_second = await self._load_model(second)
            raw_response_2 = await self._generate_response(model_second, prompt_2, self.model_config[second]["system_prompt"])
            response_2 = self._clean_response(raw_response_2)
            await self._unload_model(model_second)

            return {
                "round_number": round_num,
                "content": f"{first.upper()}: {response_1}\n{second.upper()}: {response_2}",
                "pro": response_1 if first == "pro" else response_2,
                "con": response_1 if first == "con" else response_2,
                "metadata": {
                    "topic": topic,
                    "round": round_num,
                    "pro_model": self.model_config["pro"]["name"],
                    "con_model": self.model_config["con"]["name"],
                    "first_speaker": first,
                    "second_speaker": second
                }
            }

        except Exception as e:
            logger.error(f"Round {round_num} ")
            return {
                "round_number": round_num,
                "content": f"Error during round {round_num}: {str(e)}",
                "metadata": {"topic": topic, "round": round_num, }
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
                        "num_ctx": 4026,
                        "num_predict": 920
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
            await self._unload_model(judge_model)
            return self._clean_response(verdict_raw)
        except Exception as e:
            logger.error(f"Verdict generation failed: {str(e)}")
            return "Unable to decide winner."
