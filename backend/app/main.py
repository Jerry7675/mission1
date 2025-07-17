# backend/app/main.py

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from typing import List
import json
from . import transcribe

from . import __version__, logger
from .debate_manager import DebateManager
from .models import OllamaWrapper
from .chroma_handler import ChromaHandler

app = FastAPI(
    title="AI Debate Platform",
    version=__version__,
    description="Platform for AI models to debate topics",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS setup for frontend/backend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TIP: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core service instances
manager = DebateManager()
llm = OllamaWrapper()
chroma = ChromaHandler()

app.include_router(transcribe.router)

@app.on_event("startup")
async def startup_event():
    if not await llm.health_check():
        logger.error("Ollama service not running! Start it via: ollama serve")
        raise RuntimeError("Ollama service required")

    try:
        chroma.client.heartbeat()
    except Exception as e:
        logger.error(f"ChromaDB not reachable: {str(e)}")
        raise

@app.websocket("/ws/debate")
async def websocket_debate(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON format"})
                continue

            if message.get("action") == "start_debate":
                topic = message.get("topic")
                rounds = min(5, int(message.get("rounds", 5)))

                try:
                    async for event in manager.stream_debate(topic=topic, rounds=rounds):
                        await websocket.send_json(event)
                except Exception as e:
                    logger.error(f"Debate failed: {str(e)}")
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })

            elif message.get("action") == "get_history":
                try:
                    debates = chroma.get_transcript(num_rounds=10)
                    await websocket.send_json({
                        "type": "history",
                        "data": debates
                    })
                except Exception as e:
                    logger.error(f"Failed to get history: {str(e)}")
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })

    except WebSocketDisconnect:
        logger.info("WebSocket: Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.send_json({
            "type": "error",
            "message": f"Server error: {str(e)}"
        })

@app.get("/api/health")
async def health_check():
    """Basic API health and model status check"""
    return {
        "status": "healthy" if await llm.health_check() else "unhealthy",
        "version": __version__,
        "models_loaded": list(manager.active_models)
    }

@app.get("/api/history")
async def get_history(limit: int = 5):
    """Return last N debate rounds"""
    try:
        return chroma.get_transcript(num_rounds=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve frontend if built
frontend_dir = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="static")
    logger.info(f"Serving frontend from {frontend_dir}")
else:
    logger.warning("Frontend not found. Running in API-only mode.")

@app.get("/")
async def root():
    return {"message": "AI Debate Platform API - see /api/docs"}
