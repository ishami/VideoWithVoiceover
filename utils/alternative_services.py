# utils/alternative_services.py
import requests
import logging
import asyncio
import os
from pathlib import Path
from typing import Optional, List

try:
    import edge_tts

    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False


class AlternativeServices:
    def __init__(self):
        self.hugging_face_token = os.getenv("HUGGING_FACE_TOKEN")
        self.logger = logging.getLogger(__name__)

    async def generate_speech_edge_tts(self, text: str, filename: str):
        """Edge TTS implementation (primary TTS fallback)"""
        if not EDGE_TTS_AVAILABLE:
            self.logger.warning("Edge TTS not available")
            return None

        try:
            voice = "en-US-AriaNeural"
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(filename)

            # Verify file was created
            if os.path.exists(filename) and os.path.getsize(filename) > 0:
                return filename
            else:
                return None
        except Exception as e:
            self.logger.error(f"Edge TTS fallback failed: {e}")
            return None

    def generate_speech_comprehensive(self, text: str, filename: str):
        """Comprehensive TTS using best available method"""

        # Edge TTS is the primary and best working method
        if EDGE_TTS_AVAILABLE:
            try:
                result = asyncio.run(self.generate_speech_edge_tts(text, filename))
                if result:
                    self.logger.info("Edge TTS successful")
                    return result
            except Exception as e:
                self.logger.warning(f"Edge TTS failed: {e}")

        # If Edge TTS fails, create a silent audio file as fallback
        self.logger.warning("Edge TTS failed, creating silent audio fallback")
        return self.create_silent_audio(filename, duration=max(len(text) * 0.1, 2.0))

    def create_silent_audio(self, filename: str, duration: float = 5.0):
        """Create a silent audio file as absolute fallback"""
        try:
            import wave
            import struct

            # Audio parameters
            sample_rate = 22050
            channels = 1
            sample_width = 2

            # Calculate number of samples
            num_samples = int(duration * sample_rate)

            # Create wave file
            with wave.open(filename, 'w') as wav_file:
                wav_file.setnchannels(channels)
                wav_file.setsampwidth(sample_width)
                wav_file.setframerate(sample_rate)

                # Write silent samples
                for _ in range(num_samples):
                    wav_file.writeframes(struct.pack('<h', 0))

            if os.path.exists(filename) and os.path.getsize(filename) > 0:
                return filename
            else:
                return None

        except Exception as e:
            self.logger.error(f"Failed to create silent audio: {e}")
            return None

    def generate_keywords_fallback(self, title: str, prompt: str) -> List[str]:
        """Generate fallback keywords using simple text processing"""
        try:
            import re

            # Combine title and prompt
            text = f"{title} {prompt}".lower()

            # Remove common stop words
            stop_words = {
                'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
                'by', 'from', 'about', 'into', 'through', 'during', 'before', 'after',
                'above', 'below', 'up', 'down', 'out', 'off', 'over', 'under', 'again',
                'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why',
                'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other',
                'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
                'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don',
                'should', 'now', 'a', 'an', 'as', 'i', 'you', 'he', 'she', 'it',
                'we', 'they', 'them', 'their', 'what', 'which', 'who', 'whom',
                'this', 'that', 'these', 'those', 'am', 'is', 'are', 'was', 'were',
                'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
                'will', 'would', 'could', 'should', 'may', 'might', 'must', 'shall'
            }

            # Extract words (letters only, 3+ characters)
            words = re.findall(r'\b[a-z]{3,}\b', text)

            # Filter out stop words and duplicates
            keywords = []
            seen = set()
            for word in words:
                if word not in stop_words and word not in seen and len(word) > 2:
                    keywords.append(word)
                    seen.add(word)

            # Limit to 10 keywords
            return keywords[:10]

        except Exception as e:
            self.logger.error(f"Keyword fallback failed: {e}")
            return ['video', 'content', 'tutorial']  # Basic fallback

    def generate_text_huggingface(self, prompt: str):
        """Fallback to Hugging Face API with better models"""
        if not self.hugging_face_token:
            self.logger.warning("No Hugging Face token available")
            return None

        # Try multiple models in order of preference
        models = [
            "gpt2",  # Very common, almost always available
            "distilgpt2",  # Lightweight, reliable
            "microsoft/DialoGPT-small",  # More likely to be available
        ]

        for model in models:
            try:
                headers = {"Authorization": f"Bearer {self.hugging_face_token}"}
                api_url = f"https://api-inference.huggingface.co/models/{model}"

                # Simple payload
                payload = {"inputs": prompt}

                self.logger.info(f"Trying Hugging Face model: {model}")
                response = requests.post(api_url,
                                         headers=headers,
                                         json=payload,
                                         timeout=10)

                if response.status_code == 200:
                    self.logger.info(f"Hugging Face success with model: {model}")
                    return response.json()
                elif response.status_code == 503:
                    self.logger.info(f"Model {model} is loading, trying next...")
                    continue
                else:
                    self.logger.warning(f"Model {model} returned {response.status_code}, trying next...")
                    continue

            except Exception as e:
                self.logger.warning(f"Model {model} failed: {e}")
                continue

        self.logger.error("All Hugging Face models failed")
        return None

    def check_service_availability(self):
        """Check which alternative services are available"""
        return {
            'edge_tts': EDGE_TTS_AVAILABLE,
            'huggingface': bool(self.hugging_face_token),
            'pil': self._check_pil_available(),
            'silent_audio': True  # Always available as final fallback
        }

    def _check_pil_available(self):
        """Check if PIL/Pillow is available for image generation"""
        try:
            from PIL import Image
            return True
        except ImportError:
            return False