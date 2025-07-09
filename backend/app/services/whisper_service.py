# mission1/backend/app/services/whisper_service.py

import subprocess
import os
from fastapi import UploadFile
from tempfile import NamedTemporaryFile

WHISPER_MODEL = "base"  # You can change to tiny, small, medium, or large


def transcribe_audio(file: UploadFile) -> str:
    """
    Saves the uploaded audio file and transcribes it using Whisper CLI.
    Returns transcribed text.
    """
    try:
        suffix = os.path.splitext(file.filename)[-1]
        with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(file.file.read())
            tmp_path = tmp.name

        result = subprocess.run(
            ["whisper", tmp_path, "--model", WHISPER_MODEL, "--language", "en", "--fp16", "False", "--output_format", "txt"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        transcript_path = tmp_path.replace(suffix, ".txt")
        with open(transcript_path, "r") as f:
            text = f.read()

        return text.strip()

    except Exception as e:
        return f"[ERROR] {str(e)}"
    finally:
        # Clean up temp files
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        if os.path.exists(transcript_path):
            os.remove(transcript_path)
