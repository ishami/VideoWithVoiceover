# utils/openai_wrapper.py
import logging
from functools import wraps
import time
from typing import Optional, Dict, Any
import os

try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class OpenAIFallbackHandler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.fallback_responses = {
            'text_generation': "I apologize, but I'm temporarily unable to generate content. Please try again later.",
            'image_generation': None,
            'transcription': "Audio transcription temporarily unavailable.",
            'voiceover': None,
            'video_generation': "Video generation service temporarily unavailable."
        }

    def with_fallback(self, operation_type: str, max_retries: int = 3):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not OPENAI_AVAILABLE:
                    self.logger.warning("OpenAI not available, using fallback")
                    return self._handle_generic_fallback(operation_type)

                for attempt in range(max_retries):
                    try:
                        return func(*args, **kwargs)

                    except Exception as e:
                        error_str = str(e).lower()

                        if 'rate limit' in error_str or 'too many requests' in error_str:
                            self.logger.warning(f"Rate limit hit on attempt {attempt + 1}: {e}")
                            if attempt < max_retries - 1:
                                wait_time = 2 ** attempt  # Exponential backoff
                                time.sleep(wait_time)
                                continue
                            return self._handle_rate_limit_fallback(operation_type)

                        elif 'invalid request' in error_str or 'bad request' in error_str:
                            self.logger.error(f"Invalid request: {e}")
                            return self._handle_invalid_request_fallback(operation_type)

                        elif 'authentication' in error_str or 'unauthorized' in error_str:
                            self.logger.error(f"Authentication error: {e}")
                            return self._handle_auth_fallback(operation_type)

                        elif 'quota' in error_str or 'insufficient_quota' in error_str or 'billing' in error_str:
                            self.logger.error(f"Quota exceeded: {e}")
                            return self._handle_quota_fallback(operation_type)

                        else:
                            self.logger.error(f"Unexpected error: {e}")
                            if attempt < max_retries - 1:
                                time.sleep(1)
                                continue
                            return self._handle_generic_fallback(operation_type)

                return self._handle_generic_fallback(operation_type)

            return wrapper

        return decorator

    def _handle_quota_fallback(self, operation_type: str):
        """Handle quota exceeded scenarios"""
        fallback_map = {
            'text_generation': self._text_fallback,
            'image_generation': self._image_fallback,
            'transcription': self._transcription_fallback,
            'voiceover': self._voiceover_fallback,
            'video_generation': self._video_generation_fallback
        }
        return fallback_map.get(operation_type, self._generic_fallback)()

    def _handle_rate_limit_fallback(self, operation_type: str):
        """Handle rate limit scenarios"""
        return self._handle_quota_fallback(operation_type)

    def _handle_invalid_request_fallback(self, operation_type: str):
        """Handle invalid request scenarios"""
        return self._handle_quota_fallback(operation_type)

    def _handle_auth_fallback(self, operation_type: str):
        """Handle authentication error scenarios"""
        return self._handle_quota_fallback(operation_type)

    def _handle_generic_fallback(self, operation_type: str):
        """Handle generic error scenarios"""
        return self._handle_quota_fallback(operation_type)

    def _text_fallback(self):
        # Use local models or cached responses
        return {
            'choices': [{
                'message': {
                    'content': self.fallback_responses['text_generation']
                }
            }]
        }

    def _image_fallback(self):
        # Return placeholder image or cached result
        return {
            'data': [{
                'url': '/static/images/placeholder.png'
            }]
        }

    def _transcription_fallback(self):
        # Use local speech-to-text or return cached result
        return {'text': self.fallback_responses['transcription']}

    def _voiceover_fallback(self):
        # Fall back to Edge TTS or cached audio
        return {'audio_url': '/static/audio/fallback.mp3'}

    def _video_generation_fallback(self):
        # Return error response for video generation
        return {
            'success': False,
            'message': self.fallback_responses['video_generation'],
            'fallback_used': True
        }

    def _generic_fallback(self):
        # Generic fallback response
        return {
            'success': False,
            'message': 'Service temporarily unavailable. Please try again later.',
            'fallback_used': True
        }


# Initialize the handler
fallback_handler = OpenAIFallbackHandler()