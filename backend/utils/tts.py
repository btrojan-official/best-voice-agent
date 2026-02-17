import logging
import os
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "DODLEQrClDo8wCz460ld")


async def text_to_speech_stream(text: str, model_id: str = "eleven_turbo_v2") -> bytes:
    """
    Convert text to speech using ElevenLabs TTS API.
    Optimized for low latency with turbo model.

    Args:
        text: Text to convert to speech
        model_id: ElevenLabs model ID (eleven_turbo_v2 for low latency)

    Returns:
        Audio data as bytes (MP3 format)
    """
    try:
        if not ELEVENLABS_API_KEY:
            logger.warning("ELEVENLABS_API_KEY not configured, returning empty audio")
            return b""

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"

        headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}

        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True,
            },
            "optimize_streaming_latency": 3,
        }

        response = requests.post(url, headers=headers, json=payload, timeout=10)

        if response.status_code == 200:
            audio_bytes = response.content
            logger.info(f"Generated TTS audio: {len(audio_bytes)} bytes")
            return audio_bytes
        else:
            logger.error(f"TTS API error: {response.status_code} - {response.text}")
            return b""

    except Exception as e:
        logger.error(f"TTS error: {e}")
        return b""


def text_to_speech_file(
    text: str, output_path: str, model_id: str = "eleven_turbo_v2"
) -> bool:
    """
    Convert text to speech and save to file.

    Args:
        text: Text to convert
        output_path: Path to save audio file
        model_id: ElevenLabs model ID

    Returns:
        True if successful, False otherwise
    """
    try:
        import asyncio

        audio_data = asyncio.run(text_to_speech_stream(text, model_id))

        if audio_data:
            with open(output_path, "wb") as f:
                f.write(audio_data)
            logger.info(f"Saved TTS audio to {output_path}")
            return True

        return False

    except Exception as e:
        logger.error(f"File TTS error: {e}")
        return False
