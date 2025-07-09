# mission1/backend/app/services/tts_service.py

import subprocess
import os
from tempfile import NamedTemporaryFile

def text_to_speech(text: str, speaker_wav_path: str = None) -> str:
    """
    Generates a WAV file using Coqui TTS from the given text.
    Optionally uses a reference speaker WAV for voice cloning (if supported).
    Returns the path to the generated WAV file.
    """
    try:
        with NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            output_path = tmp.name

        command = [
            "tts",
            "--text", text,
            "--out_path", output_path
        ]

        if speaker_wav_path:
            command += ["--speaker_wav", speaker_wav_path]

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        if result.returncode != 0:
            raise RuntimeError(result.stderr.decode())

        return output_path

    except Exception as e:
        raise RuntimeError(f"[TTS ERROR] {str(e)}")
