"""
Environment initialization module
This MUST be imported before any other modules to ensure env vars are set
"""
import os

# Force set environment variables
# These will be loaded before engine.py imports
_API_KEYS = {
    'PIXABAY_API_KEY': "44812949-ba98a63acdbb20b31f0281193",
    'PEXELS_API_KEY': "e4agaHhuOEpih3K562pmje6YJiy2jSQ37bYJU1nm5nw6NmeualG8afvG",
    'UNSPLASH_API_KEY': "ATMcaMHzCfB789pGt8m6L5Z3YyvdgndRqiBNaxwmbf8",
    'OPENAI_API_KEY': "sk-proj-rjJGSlP9rRzc4jNMpt0BT3BlbkFJLMLQHqpdBOaoSow6zM7d"
}

for key, value in _API_KEYS.items():
    if not os.getenv(key):
        os.environ[key] = value

print(f"[env_init] Environment variables initialized")
print(f"[env_init] PIXABAY_API_KEY: {os.getenv('PIXABAY_API_KEY')[:8]}...")
print(f"[env_init] PEXELS_API_KEY: {os.getenv('PEXELS_API_KEY')[:8]}...")
print(f"[env_init] UNSPLASH_API_KEY: {os.getenv('UNSPLASH_API_KEY')[:8]}...")
