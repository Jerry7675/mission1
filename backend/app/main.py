# mission1/backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import debate, audio
from app.db.database import engine
from app.db import schemas
from app.api import debate, audio, websocket




# Create DB tables
schemas.Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(title="Debate Engine API")

# Allow all origins during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(debate.router)
app.include_router(audio.router)
app.include_router(websocket.router)