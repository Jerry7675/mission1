# mission1/backend/app/api/debate.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.model_runner import run_debate_session

router = APIRouter(prefix="/debate", tags=["Debate"])

# Request model
class DebateRequest(BaseModel):
    topic: str
    rounds: Optional[int] = 3

# Response model
class DebateResponse(BaseModel):
    topic: str
    rounds: list
    verdict: str
    timestamp: float

@router.post("/start", response_model=DebateResponse)
def start_debate(request: DebateRequest):
    if not request.topic.strip():
        raise HTTPException(status_code=400, detail="Topic cannot be empty.")

    try:
        result = run_debate_session(request.topic, request.rounds)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
