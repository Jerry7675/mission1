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
                "name": "mistral:7b",
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
               
                client = ollama.AsyncClient()
                progress_response = await client.pull(model["name"])
                
               
                
                self.active_models.add(model["name"])
                logger.info(f"Loaded model: {model['name']}")
            except Exception as e:
                logger.error(f"Model load failed: {str(e)}")
                # Fallback to available models
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
        """Get list of available models"""
        try:
            client = ollama.AsyncClient()
            models = await client.list()
            return [model['name'] for model in models.get('models', [])]
        except Exception as e:
            logger.error(f"Failed to get available models: {str(e)}")
            return []

    async def _unload_oldest_model(self):
        """Unload least recently used model"""
        if self.active_models:
            model_to_unload = next(iter(self.active_models))
            try:
                client = ollama.AsyncClient()
                await client.delete(model_to_unload)
                self.active_models.remove(model_to_unload)
                logger.info(f"Unloaded model: {model_to_unload}")
            except Exception as e:
                logger.error(f"Model unload failed: {str(e)}")

    async def run_debate(self, topic: str = None, rounds: int = 5) -> Dict:
        """Main debate orchestration with improved error handling"""
        try:
            # Initialize
            topic = topic or get_random_topic()
            transcript = []
            
            # Check if Ollama is running
            if not await self.llm.health_check():
                raise RuntimeError("Ollama service is not running. Please start with: ollama serve")
            
            # Load initial models
            pro_model = await self._load_model("pro")
            con_model = await self._load_model("con")

            # Debate rounds
            for round_num in range(1, rounds + 1):
                logger.info(f"Starting round {round_num}")
                round_data = await self._conduct_round(
                    topic, 
                    round_num, 
                    pro_model, 
                    con_model
                )
                transcript.append(round_data)
                
                # Log to ChromaDB with better error handling
                try:
                    self.chroma.log_debate_round(round_data)
                except Exception as e:
                    logger.warning(f"Failed to log round to ChromaDB: {str(e)}")

            # Final judgment
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
            # Cleanup
            await self._unload_all_models()

    async def _conduct_round(self, topic: str, round_num: int, pro_model: str, con_model: str) -> Dict:
        """Run one debate round with improved structure"""
        try:
            # Alternate who speaks first
            if round_num % 2 == 1:
                first_speaker, second_speaker = "pro", "con"
                first_model, second_model = pro_model, con_model
            else:
                first_speaker, second_speaker = "con", "pro"
                first_model, second_model = con_model, pro_model

            # Generate first argument
            first_prompt = f"Debate Topic: {topic}\nRound {round_num}\nYour Position: {'Argue FOR the topic' if first_speaker == 'pro' else 'Argue AGAINST the topic'}\nPresent your argument:"
            
            first_response = await self._generate_response(
                model_name=first_model,
                prompt=first_prompt,
                system=self.model_config[first_speaker]["system_prompt"]
            )

            # Generate counter-argument
            counter_prompt = f"Debate Topic: {topic}\nRound {round_num}\nOpponent's Argument: {first_response}\nYour Position: {'Argue FOR the topic' if second_speaker == 'pro' else 'Argue AGAINST the topic'}\nCounter this argument:"
            
            second_response = await self._generate_response(
                model_name=second_model,
                prompt=counter_prompt,
                system=self.model_config[second_speaker]["system_prompt"]
            )

            return {
                "round_number": round_num,
                "content": f"Round {round_num}: {first_speaker.upper()}: {first_response}\n{second_speaker.upper()}: {second_response}",
                "pro": first_response if first_speaker == "pro" else second_response,
                "con": first_response if first_speaker == "con" else second_response
            }
            
        except Exception as e:
            logger.error(f"Round {round_num} failed: {str(e)}")
            return {
                "round_number": round_num,
                "content": f"Round {round_num} failed: {str(e)}",
                "pro": "[Error occurred]",
                "con": "[Error occurred]"
            }

    async def _generate_response(self, model_name: str, prompt: str, system: str) -> str:
        """Safe model generation with timeout and retry logic"""
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
                        "num_predict": 512  # Limit response length
                    }
                ),
                timeout=60  # 1 minute timeout
            )
            return response.get("response", "[No response generated]")
        except asyncio.TimeoutError:
            logger.warning(f"Model timeout: {model_name}")
            return "[Model response timed out]"
        except Exception as e:
            logger.error(f"Generation failed for {model_name}: {str(e)}")
            return f"[Model error: {str(e)}]"

    async def _get_verdict(self, transcript: List[Dict]) -> str:
        """Load judge model for final decision"""
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
        """Cleanup all loaded models"""
        client = ollama.AsyncClient()
        for model in list(self.active_models):
            try:
                await client.delete(model)
                self.active_models.remove(model)
                logger.info(f"Unloaded model: {model}")
            except Exception as e:
                logger.error(f"Failed to unload {model}: {str(e)}")

    async def _unload_model(self, role: str):
        """Unload specific model by role"""
        model_name = self.model_config[role]["name"]
        if model_name in self.active_models:
            try:
                client = ollama.AsyncClient()
                await client.delete(model_name)
                self.active_models.remove(model_name)
                logger.info(f"Unloaded {role} model: {model_name}")
            except Exception as e:
                logger.error(f"Failed to unload {role} model {model_name}: {str(e)}")