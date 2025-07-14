# backend/app/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from .debate_manager import DebateManager
from .models import OllamaWrapper
import asyncio
import logging
from pathlib import Path
from . import __version__, logger

app = FastAPI(
    title="AI Debate Platform",
    version=__version__,
    description="Platform for AI models to debate topics"
)

# Initialize components
manager = DebateManager()
llm = OllamaWrapper()

@app.on_event("startup")
async def startup_event():
    if not await llm.health_check():
        logger.error("Ollama service not running! Start with: ollama serve")
        raise RuntimeError("Ollama service required")

@app.websocket("/ws/debate")
async def websocket_debate(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            
            # Handle different request types
            if data.get("type") == "health_check":
                healthy = await llm.health_check()
                await websocket.send_json({"status": "healthy" if healthy else "unhealthy"})
            
            elif data.get("type") == "start_debate":
                topic = data.get("topic")
                rounds = data.get("rounds", 3)
                
                result = await manager.run_debate(
                    topic=topic,
                    rounds=rounds
                )
                
                await websocket.send_json({
                    "type": "result",
                    "data": result
                })
                
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })

# Serve frontend files (if needed)
frontend_dir = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="static")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy" if await llm.health_check() else "unhealthy",
        "version": __version__
    }