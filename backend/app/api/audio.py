# mission1/backend/app/api/audio.py

from fastapi import APIRouter, UploadFile, File, HTTPException, Response, Form
from app.services.whisper_service import transcribe_audio
from app.services.tts_service import text_to_speech
import os
import asyncio

router = APIRouter(prefix="/audio", tags=["Audio"])

@router.post("/transcribe")
def transcribe(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")

    try:
        transcript = transcribe_audio(file)
        return {"transcript": transcript}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/speak")
def speak(text: str = Form(...)):
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    try:
        wav_path = text_to_speech(text)
        with open(wav_path, "rb") as audio_file:
            audio_data = audio_file.read()

        # Clean up temp file
        os.remove(wav_path)

        return Response(content=audio_data, media_type="audio/wav")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# Add to audio.py
class AudioQueue:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.current_speaker = None
    
    async def add_to_queue(self, agent: str, text: str):
        await self.queue.put({"agent": agent, "text": text})