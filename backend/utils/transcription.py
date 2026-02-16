import os
import io
import tempfile
import logging
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "whisper-large-v3")


async def transcribe_audio_stream(audio_bytes: bytes) -> Optional[str]:
    """
    Transcribe audio bytes using Groq Whisper API (fast and free).
    Falls back to a simple placeholder if API is not configured.
    
    Args:
        audio_bytes: Raw audio data
    
    Returns:
        Transcribed text or None if failed
    """
    try:
        groq_api_key = os.getenv("GROQ_API_KEY")
        
        if not groq_api_key:
            logger.warning("GROQ_API_KEY not configured, using placeholder transcription")
            return "[Transcription placeholder - configure GROQ_API_KEY for real transcription]"
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(audio_bytes)
            temp_path = temp_file.name
        
        try:
            url = "https://api.groq.com/openai/v1/audio/transcriptions"
            
            headers = {
                "Authorization": f"Bearer {groq_api_key}"
            }
            
            with open(temp_path, "rb") as audio_file:
                files = {
                    "file": audio_file,
                    "model": (None, GROQ_MODEL)
                }
                
                response = requests.post(url, headers=headers, files=files, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                text = result.get("text", "").strip()
                logger.info(f"Transcribed audio: {text[:100]}...")
                return text
            else:
                logger.error(f"Transcription API error: {response.status_code} - {response.text}")
                return None
        
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return None


def transcribe_audio_file(audio_path: str) -> Optional[str]:
    """
    Transcribe audio file using Groq Whisper API.
    
    Args:
        audio_path: Path to audio file
    
    Returns:
        Transcribed text or None if failed
    """
    try:
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()
        
        import asyncio
        return asyncio.run(transcribe_audio_stream(audio_bytes))
    
    except Exception as e:
        logger.error(f"File transcription error: {e}")
        return None
