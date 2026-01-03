"""Audio transcription utilities using OpenAI Whisper API."""

import os
import tempfile
from openai import OpenAI


def transcribe_audio(audio_bytes: bytes) -> str:
    """
    Transcribe audio bytes to text using OpenAI Whisper API.

    Args:
        audio_bytes: Raw audio data in bytes format (webm format from browser)

    Returns:
        Transcribed text as a string, or empty string if transcription fails
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return ""

    temp_file_path = None
    try:
        # Save audio bytes to temporary file
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.webm', delete=False) as temp_file:
            temp_file.write(audio_bytes)
            temp_file_path = temp_file.name

        # Transcribe using Whisper API
        client = OpenAI(api_key=api_key)
        with open(temp_file_path, 'rb') as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )

        return transcript.strip()

    except Exception:
        return ""

    finally:
        # Clean up temp file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception:
                pass
