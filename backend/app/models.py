# backend/app/models.py
import ollama
import asyncio
import logging
from typing import Dict, List, Optional, Any
from functools import wraps

logger = logging.getLogger(__name__)

def run_in_executor(func):
    """Decorator to run sync functions in executor for async compatibility"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args, **kwargs)
    return wrapper

class OllamaWrapper:
    def __init__(self, base_url: str = "http://127.0.0.1:11434"):
        self.base_url = base_url
        self.client = ollama.Client(host=base_url)
        logger.info(f"Initialized Ollama client with base_url: {base_url}")
    
    async def health_check(self) -> bool:
        """Check if Ollama service is running and accessible"""
        try:
            # Run the synchronous list() method in an executor
            response = await asyncio.get_event_loop().run_in_executor(
                None, self.client.list
            )
            logger.info("Ollama health check passed")
            return True
        except Exception as e:
            logger.error(f"Ollama health check failed: {str(e)}")
            return False
    
    async def get_available_models(self) -> List[str]:
        """Get list of available models"""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, self.client.list
            )
            return [model['name'] for model in response['models']]
        except Exception as e:
            logger.error(f"Failed to get models: {str(e)}")
            return []
    
    async def generate_response(
        self, 
        prompt: str, 
        model: str = "llama3.2:latest",
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """Generate response using Ollama"""
        try:
            def _generate():
                return self.client.generate(
                    model=model,
                    prompt=prompt,
                    options={
                        'temperature': temperature,
                        'num_predict': max_tokens
                    }
                )
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, _generate
            )
            return response['response']
            
        except Exception as e:
            logger.error(f"Generation failed: {str(e)}")
            raise Exception(f"Failed to generate response: {str(e)}")
    
    async def chat(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "llama3.2:latest",
        temperature: float = 0.7
    ) -> str:
        """Chat with model using conversation history"""
        try:
            def _chat():
                return self.client.chat(
                    model=model,
                    messages=messages,
                    options={'temperature': temperature}
                )
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, _chat
            )
            return response['message']['content']
            
        except Exception as e:
            logger.error(f"Chat failed: {str(e)}")
            raise Exception(f"Failed to chat: {str(e)}")

# Alternative implementation using AsyncClient (if you prefer)
class AsyncOllamaWrapper:
    def __init__(self, base_url: str = "http://127.0.0.1:11434"):
        self.base_url = base_url
        self.client = ollama.AsyncClient(host=base_url)
        logger.info(f"Initialized Async Ollama client with base_url: {base_url}")
    
    async def health_check(self) -> bool:
        """Check if Ollama service is running and accessible"""
        try:
            response = await self.client.list()
            logger.info("Ollama health check passed")
            return True
        except Exception as e:
            logger.error(f"Ollama health check failed: {str(e)}")
            return False
    
    async def get_available_models(self) -> List[str]:
        """Get list of available models"""
        try:
            response = await self.client.list()
            return [model['name'] for model in response['models']]
        except Exception as e:
            logger.error(f"Failed to get models: {str(e)}")
            return []
    
    async def generate_response(
        self, 
        prompt: str, 
        model: str = "llama3.2:latest",
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """Generate response using Ollama"""
        try:
            response = await self.client.generate(
                model=model,
                prompt=prompt,
                options={
                    'temperature': temperature,
                    'num_predict': max_tokens
                }
            )
            return response['response']
            
        except Exception as e:
            logger.error(f"Generation failed: {str(e)}")
            raise Exception(f"Failed to generate response: {str(e)}")
    
    async def chat(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "llama3.2:latest",
        temperature: float = 0.7
    ) -> str:
        """Chat with model using conversation history"""
        try:
            response = await self.client.chat(
                model=model,
                messages=messages,
                options={'temperature': temperature}
            )
            return response['message']['content']
            
        except Exception as e:
            logger.error(f"Chat failed: {str(e)}")
            raise Exception(f"Failed to chat: {str(e)}")


