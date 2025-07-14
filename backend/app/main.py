from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from app.api import audio, debate
import os

app = FastAPI()

# Include your API routers
app.include_router(debate.router, prefix="/api/debate")
app.include_router(audio.router, prefix="/api/audio")

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back the received message
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        print("Client disconnected")

# Serve frontend files in production
if os.path.exists("../frontend/dist"):
    app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)