import os
import requests
from dotenv import load_dotenv
import numpy as np

load_dotenv()

# Load credentials from .env
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "sk_0c313606b4c0d22918babd4a087bd6750a73569bb95fb8f7")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "DODLEQrClDo8wCz460ld")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "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")


def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe audio using ElevenLabs Speech-to-Text API.
    
    Args:
        audio_path: Path to audio file (mp3, wav, etc.)
    
    Returns:
        Transcribed text as string
    """
    url = "https://api.elevenlabs.io/v1/audio-native"
    
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    with open(audio_path, "rb") as audio_file:
        files = {"audio": audio_file}
        response = requests.post(url, headers=headers, files=files)
    
    response.raise_for_status()
    return response.json()["text"]


def text_to_speech(text: str, model_id: str = "eleven_monolingual_v1") -> np.ndarray:
    """
    Convert text to speech using ElevenLabs TTS API.
    
    Args:
        text: Input text to synthesize
        model_id: ElevenLabs model ID
    
    Returns:
        Audio waveform as numpy array (raw PCM data)
    """
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    
    # Convert raw audio bytes to numpy array
    audio_bytes = response.content
    audio_array = np.frombuffer(audio_bytes, dtype=np.uint8)
    
    return audio_array


def query_openrouter(
    prompt: str,
    model: str = "anthropic/claude-3.5-sonnet",
    max_tokens: int = 1024,
    temperature: float = 0.7
) -> str:
    """
    Query a model via OpenRouter API.
    
    Args:
        prompt: User prompt/message
        model: Model identifier (e.g., "anthropic/claude-3.5-sonnet")
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature
    
    Returns:
        Model's response text
    """
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    
    return response.json()["choices"][0]["message"]["content"]


def test_pipeline(test_text: str = "Hello, this is a test of the audio pipeline!"):
    """
    Test both TTS and OpenRouter capabilities.
    
    Pipeline:
    1. Generate speech from test text (TTS)
    2. Query OpenRouter with a test prompt
    3. Print results and audio shape
    """
    print("=" * 60)
    print("TESTING AUDIO & AI PIPELINE")
    print("=" * 60)
    
    # Test TTS
    print("\n[1/2] Testing Text-to-Speech...")
    print(f"Input text: '{test_text}'")
    
    try:
        audio_waveform = text_to_speech(test_text)
        print(f"✓ TTS successful!")
        print(f"  Audio shape: {audio_waveform.shape}")
        print(f"  Audio dtype: {audio_waveform.dtype}")
        print(f"  Audio size: {len(audio_waveform)} bytes")
    except Exception as e:
        print(f"✗ TTS failed: {e}")
        audio_waveform = None
    
    # Test OpenRouter
    print("\n[2/2] Testing OpenRouter query...")
    test_prompt = "Explain what a neural network is in one sentence."
    print(f"Prompt: '{test_prompt}'")
    
    try:
        response = query_openrouter(test_prompt)
        print(f"✓ OpenRouter successful!")
        print(f"  Response: {response}")
    except Exception as e:
        print(f"✗ OpenRouter failed: {e}")
    
    print("\n" + "=" * 60)
    print("PIPELINE TEST COMPLETE")
    print("=" * 60)
    
    return audio_waveform


if __name__ == "__main__":
    test_pipeline()