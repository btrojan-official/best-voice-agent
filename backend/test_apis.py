#!/usr/bin/env python3
"""
Test script to verify API connections for OpenRouter, ElevenLabs, and Groq.
Run this script to ensure all API keys are configured correctly.
"""

import os
import sys
import tempfile
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TRANSCRIPTION_MODEL = os.getenv("TRANSCRIPTION_MODEL", "whisper-large-v3")


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_result(success, message):
    """Print a test result."""
    symbol = "✓" if success else "✗"
    status = "SUCCESS" if success else "FAILED"
    print(f"\n{symbol} {status}: {message}")


def test_openrouter():
    """Test OpenRouter API connection."""
    print_header("Testing OpenRouter API")
    
    if not OPENROUTER_API_KEY or OPENROUTER_API_KEY == "your_openrouter_api_key_here":
        print_result(False, "OPENROUTER_API_KEY not configured in .env")
        return False
    
    print(f"Using model: {OPENROUTER_MODEL}")
    print("Sending test prompt: 'Hello, respond with just OK'")
    
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": OPENROUTER_MODEL,
            "messages": [
                {"role": "user", "content": "Hello, respond with just OK"}
            ],
            "max_tokens": 10
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        reply = data["choices"][0]["message"]["content"]
        
        print(f"Response: {reply}")
        print_result(True, "OpenRouter API is working correctly")
        return True
    
    except requests.exceptions.RequestException as e:
        print_result(False, f"OpenRouter API error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text[:200]}")
        return False
    except Exception as e:
        print_result(False, f"Unexpected error: {e}")
        return False


def test_elevenlabs():
    """Test ElevenLabs API connection."""
    print_header("Testing ElevenLabs TTS API")
    
    if not ELEVENLABS_API_KEY or ELEVENLABS_API_KEY == "your_elevenlabs_api_key_here":
        print_result(False, "ELEVENLABS_API_KEY not configured in .env")
        return False
    
    if not ELEVENLABS_VOICE_ID or ELEVENLABS_VOICE_ID == "your_voice_id_here":
        print_result(False, "ELEVENLABS_VOICE_ID not configured in .env")
        return False
    
    print(f"Using voice ID: {ELEVENLABS_VOICE_ID}")
    print("Converting text: 'Hello, this is a test'")
    
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }
        
        payload = {
            "text": "Hello, this is a test",
            "model_id": "eleven_turbo_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        audio_size = len(response.content)
        print(f"Generated audio: {audio_size} bytes")
        
        print_result(True, "ElevenLabs TTS API is working correctly")
        return True
    
    except requests.exceptions.RequestException as e:
        print_result(False, f"ElevenLabs API error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text[:200]}")
        return False
    except Exception as e:
        print_result(False, f"Unexpected error: {e}")
        return False


def test_groq():
    """Test Groq Whisper API connection."""
    print_header("Testing Groq Whisper API")
    
    if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
        print_result(False, "GROQ_API_KEY not configured in .env")
        return False
    
    print(f"Using model: {TRANSCRIPTION_MODEL}")
    print("Creating test audio file...")
    
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            temp_path = temp_audio.name
            
            with open(temp_path, "wb") as f:
                f.write(b"RIFF")
                f.write((36).to_bytes(4, 'little'))
                f.write(b"WAVE")
                f.write(b"fmt ")
                f.write((16).to_bytes(4, 'little'))
                f.write((1).to_bytes(2, 'little'))
                f.write((1).to_bytes(2, 'little'))
                f.write((16000).to_bytes(4, 'little'))
                f.write((32000).to_bytes(4, 'little'))
                f.write((2).to_bytes(2, 'little'))
                f.write((16).to_bytes(2, 'little'))
                f.write(b"data")
                f.write((0).to_bytes(4, 'little'))
        
        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}"
        }
        
        with open(temp_path, "rb") as audio_file:
            files = {
                "file": ("test.wav", audio_file, "audio/wav"),
                "model": (None, TRANSCRIPTION_MODEL)
            }
            
            response = requests.post(url, headers=headers, files=files, timeout=30)
            response.raise_for_status()
        
        os.unlink(temp_path)
        
        data = response.json()
        text = data.get("text", "")
        
        print(f"Transcription result: {text if text else '(empty/silence detected)'}")
        print_result(True, "Groq Whisper API is working correctly")
        return True
    
    except requests.exceptions.RequestException as e:
        print_result(False, f"Groq API error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text[:200]}")
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)
        return False
    except Exception as e:
        print_result(False, f"Unexpected error: {e}")
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)
        return False


def main():
    """Run all API tests."""
    print_header("API Connection Test Suite")
    print("Testing API connectivity for Best Voice Agent")
    
    results = {
        "OpenRouter": test_openrouter(),
        "ElevenLabs": test_elevenlabs(),
        "Groq": test_groq()
    }
    
    print_header("Test Results Summary")
    
    for service, success in results.items():
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{service:20} {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 All API tests passed! Your setup is ready.")
        return 0
    else:
        print("\n⚠️  Some API tests failed. Please check your configuration.")
        print("Make sure all API keys are set correctly in your .env file.")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
