# backend/app/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .debate_manager import DebateManager
from .models import OllamaWrapper
from .chroma_handler import ChromaHandler
import asyncio
import logging
from pathlib import Path
from typing import Dict, List
import json
from . import __version__, logger

app = FastAPI(
    title="AI Debate Platform",
    version=__version__,
    description="Platform for AI models to debate topics",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize core components
manager = DebateManager()
llm = OllamaWrapper()
chroma = ChromaHandler()

@app.on_event("startup")
async def startup_event():
    """Validate services on startup"""
    if not await llm.health_check():
        logger.error("Ollama service not running! Start with: ollama serve")
        raise RuntimeError("Ollama service required")
    
    try:
        chroma.client.heartbeat()  # Simple ChromaDB check
    except Exception as e:
        logger.error(f"ChromaDB connection failed: {str(e)}")
        raise

@app.websocket("/ws/debate")
async def websocket_debate(websocket: WebSocket):
    """WebSocket endpoint for real-time debates"""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON"})
                continue

            if message.get("action") == "start_debate":
                # Start new debate
                topic = message.get("topic")
                rounds = min(5, int(message.get("rounds", 3)))
                
                try:
                    result = await manager.run_debate(
                        topic=topic,
                        rounds=rounds
                    )
                    
                    # Send progress updates
                    for round_data in result["transcript"]:
                        await websocket.send_json({
                            "type": "round_update",
                            "data": round_data
                        })
                    
                    # Final verdict
                    await websocket.send_json({
                        "type": "verdict",
                        "data": {
                            "topic": result["topic"],
                            "verdict": result["verdict"]
                        }
                    })
                    
                except Exception as e:
                    logger.error(f"Debate failed: {str(e)}")
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })

            elif message.get("action") == "get_history":
                # Retrieve past debates
                debates = chroma.get_transcript(num_rounds=10)
                await websocket.send_json({
                    "type": "history",
                    "data": debates
                })

    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.send_json({
            "type": "error",
            "message": f"Server error: {str(e)}"
        })

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy" if await llm.health_check() else "unhealthy",
        "version": __version__,
        "models_loaded": list(manager.active_models)
    }

@app.get("/api/history")
async def get_history(limit: int = 5):
    """Get debate history"""
    try:
        return chroma.get_transcript(num_rounds=limit)
    except Exception as e:
        raise HTTPException(500, detail=str(e))

# Serve frontend files if they exist
frontend_dir = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="static")
    logger.info(f"Serving frontend from {frontend_dir}")
else:
    logger.warning("Frontend build not found - API-only mode")

@app.get("/")
async def root():
    return {"message": "AI Debate Platform API - see /api/docs"}