import os
import json
import random
import logging
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class PrecomputedAudioManager:
    """
    Manages precomputed audio files for greetings and acknowledgment prompts.
    These are used to reduce latency and improve conversation flow.
    """
    
    def __init__(self, audio_dir: str = "data/audio"):
        self.audio_dir = Path(audio_dir)
        self.audio_cache: Dict[str, bytes] = {}
        self.acknowledgments: List[Dict[str, str]] = [
            {"text": "Hmm...", "file": "hmm.mp3"},
            {"text": "Let me think...", "file": "let_me_think.mp3"},
            {"text": "Okay...", "file": "okay.mp3"},
            {"text": "Interesting...", "file": "interesting.mp3"},
            {"text": "Yhmm...", "file": "yhmm.mp3"},
            {"text": "I see...", "file": "i_see.mp3"},
            {"text": "Alright...", "file": "alright.mp3"},
            {"text": "Got it...", "file": "got_it.mp3"},
        ]
        self.greeting_data: Optional[Dict[str, any]] = None
        self._load_greeting_config()
        self._ensure_audio_directory()
    
    def _ensure_audio_directory(self):
        """Ensure audio directory exists."""
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        acknowledgments_dir = self.audio_dir / "acknowledgments"
        acknowledgments_dir.mkdir(exist_ok=True)
        
    def _load_greeting_config(self):
        """Load greeting configuration from JSON."""
        config_path = self.audio_dir / "greeting.json"
        try:
            if config_path.exists():
                with open(config_path, "r") as f:
                    self.greeting_data = json.load(f)
                    logger.info("Loaded greeting configuration")
        except Exception as e:
            logger.error(f"Error loading greeting config: {e}")
    
    def save_greeting_config(self, text: str, audio_file: str):
        """Save greeting configuration to JSON."""
        config_path = self.audio_dir / "greeting.json"
        self.greeting_data = {
            "text": text,
            "file": audio_file
        }
        try:
            with open(config_path, "w") as f:
                json.dump(self.greeting_data, f, indent=2)
            logger.info("Saved greeting configuration")
        except Exception as e:
            logger.error(f"Error saving greeting config: {e}")
    
    def get_greeting(self) -> Optional[Dict[str, any]]:
        """
        Get precomputed greeting data.
        
        Returns:
            Dictionary with 'text' and 'audio' (bytes) if available, None otherwise
        """
        if not self.greeting_data:
            return None
        
        greeting_file = self.audio_dir / self.greeting_data["file"]
        if not greeting_file.exists():
            logger.warning(f"Greeting audio file not found: {greeting_file}")
            return None
        
        try:
            # Load from cache or file
            cache_key = f"greeting_{self.greeting_data['file']}"
            if cache_key in self.audio_cache:
                audio_data = self.audio_cache[cache_key]
            else:
                with open(greeting_file, "rb") as f:
                    audio_data = f.read()
                self.audio_cache[cache_key] = audio_data
            
            return {
                "text": self.greeting_data["text"],
                "audio": audio_data
            }
        except Exception as e:
            logger.error(f"Error loading greeting audio: {e}")
            return None
    
    def get_random_acknowledgment(self) -> Dict[str, any]:
        """
        Get a random acknowledgment prompt with its audio.
        
        Returns:
            Dictionary with 'text', 'audio' (bytes or None), and 'file' name
        """
        ack = random.choice(self.acknowledgments)
        ack_file = self.audio_dir / "acknowledgments" / ack["file"]
        
        result = {
            "text": ack["text"],
            "file": ack["file"],
            "audio": None
        }
        
        if ack_file.exists():
            try:
                # Load from cache or file
                cache_key = f"ack_{ack['file']}"
                if cache_key in self.audio_cache:
                    result["audio"] = self.audio_cache[cache_key]
                else:
                    with open(ack_file, "rb") as f:
                        audio_data = f.read()
                    self.audio_cache[cache_key] = audio_data
                    result["audio"] = audio_data
            except Exception as e:
                logger.error(f"Error loading acknowledgment audio {ack['file']}: {e}")
        else:
            logger.debug(f"Acknowledgment audio not found: {ack_file}, will generate on-the-fly")
        
        return result
    
    def save_acknowledgment_audio(self, text: str, audio_data: bytes):
        """
        Save acknowledgment audio to file.
        
        Args:
            text: Acknowledgment text
            audio_data: Audio bytes (MP3 format)
        """
        # Find matching acknowledgment
        for ack in self.acknowledgments:
            if ack["text"].lower() == text.lower():
                ack_file = self.audio_dir / "acknowledgments" / ack["file"]
                try:
                    with open(ack_file, "wb") as f:
                        f.write(audio_data)
                    # Update cache
                    cache_key = f"ack_{ack['file']}"
                    self.audio_cache[cache_key] = audio_data
                    logger.info(f"Saved acknowledgment audio: {ack['file']}")
                except Exception as e:
                    logger.error(f"Error saving acknowledgment audio: {e}")
                break
    
    def save_greeting_audio(self, text: str, audio_data: bytes):
        """
        Save greeting audio to file.
        
        Args:
            text: Greeting text
            audio_data: Audio bytes (MP3 format)
        """
        greeting_file = self.audio_dir / "greeting.mp3"
        try:
            with open(greeting_file, "wb") as f:
                f.write(audio_data)
            # Update cache
            self.audio_cache[f"greeting_greeting.mp3"] = audio_data
            # Save config
            self.save_greeting_config(text, "greeting.mp3")
            logger.info("Saved greeting audio")
        except Exception as e:
            logger.error(f"Error saving greeting audio: {e}")


# Global instance
precomputed_audio_manager = PrecomputedAudioManager()
