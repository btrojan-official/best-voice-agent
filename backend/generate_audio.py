#!/usr/bin/env python3
"""
Script to generate precomputed audio files for greetings and acknowledgments.
This reduces latency during conversations by having audio ready to play.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from utils.tts import text_to_speech_stream
from utils.precomputed_audio import precomputed_audio_manager


async def generate_greeting():
    """Generate and save the greeting audio."""
    greeting_text = "Hello! Thank you for contacting customer support. How can I help you today?"
    print(f"Generating greeting: '{greeting_text}'")
    
    audio_data = await text_to_speech_stream(greeting_text)
    if audio_data:
        precomputed_audio_manager.save_greeting_audio(greeting_text, audio_data)
        print(f"✓ Greeting saved ({len(audio_data)} bytes)")
    else:
        print("✗ Failed to generate greeting audio")


async def generate_acknowledgments():
    """Generate and save all acknowledgment audios."""
    acknowledgments = [
        "Let me think...",
        "Okay...",
        "Interesting...",
        "I see...",
        "Alright...",
        "Got it...",
    ]
    
    for ack_text in acknowledgments:
        print(f"Generating acknowledgment: '{ack_text}'")
        audio_data = await text_to_speech_stream(ack_text)
        if audio_data:
            precomputed_audio_manager.save_acknowledgment_audio(ack_text, audio_data)
            print(f"✓ '{ack_text}' saved ({len(audio_data)} bytes)")
        else:
            print(f"✗ Failed to generate '{ack_text}'")
        
        # Small delay to avoid rate limiting
        await asyncio.sleep(0.5)


async def main():
    """Main function to generate all precomputed audio."""
    print("=" * 60)
    print("Generating Precomputed Audio Files")
    print("=" * 60)
    print()
    
    # Check if ElevenLabs API key is configured
    if not os.getenv("ELEVENLABS_API_KEY"):
        print("ERROR: ELEVENLABS_API_KEY not found in environment variables")
        print("Please set it in your .env file")
        sys.exit(1)
    
    print("Step 1: Generating greeting audio...")
    await generate_greeting()
    print()
    
    print("Step 2: Generating acknowledgment audios...")
    await generate_acknowledgments()
    print()
    
    print("=" * 60)
    print("✓ All precomputed audio files generated successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
