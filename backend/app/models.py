# backend/app/models.py
import ollama
import asyncio
from typing import Optional
from . import logger

class OllamaWrapper:
    def __init__(self):
        self.timeout = 60  # seconds
        self.retries = 3

    async def generate(self, model: str, prompt: str, system: Optional[str] = None) -> str:
        for attempt in range(self.retries):
            try:
                response = await asyncio.wait_for(
                    ollama.generate(
                        model=model,
                        prompt=prompt,
                        system=system,
                        options={
                            'temperature': 0.7,
                            'num_ctx': 2048
                        }
                    ),
                    timeout=self.timeout
                )
                return response['response']
            except asyncio.TimeoutError:
                logger.warning(f"Attempt {attempt + 1}: Model timeout - {model}")
                if attempt == self.retries - 1:
                    return f"[Timeout error in {model}]"
            except Exception as e:
                logger.error(f"Attempt {attempt + 1}: Generation failed - {str(e)}")
                if attempt == self.retries - 1:
                    return f"[Error in {model}: {str(e)}]"
                await asyncio.sleep(1)  # Wait before retry

    async def health_check(self) -> bool:
        try:
            await asyncio.wait_for(
                ollama.list(),
                timeout=5
            )
            return True
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False