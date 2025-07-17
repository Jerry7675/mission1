from fastapi import APIRouter, UploadFile, File, HTTPException
import whisper
import tempfile
import shutil
import os

router = APIRouter()


model = whisper.load_model("medium")  

@router.post("/api/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    if not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an audio file.")

    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_file_path = tmp_file.name

        # Run whisper transcription
        result = model.transcribe(tmp_file_path)

        # Clean up temp file
        os.remove(tmp_file_path)

        return {
            "text": result.get("text", ""),
            "language": result.get("language", ""),
           
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
