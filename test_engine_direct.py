#!/usr/bin/env python3
import engine
import os

print("Testing engine.generate_clips function...")

# Create test directories
test_base = "/tmp/test_video"
os.makedirs(test_base, exist_ok=True)

# Test parameters
params = {
    "video_title": "Test Nature Video",
    "script": "Nature is beautiful. Mountains are tall. Rivers flow gently.",
    "target_language": "en",
    "voice": "en-US-AvaMultilingualNeural",
    "platform": "YouTube",
    "genre": "Soundtrack",
    "base_dir": test_base
}

# Check if generate_clips exists
if hasattr(engine, 'generate_clips'):
    print("Found generate_clips function")
    try:
        result = engine.generate_clips(**params)
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error calling generate_clips: {e}")
        import traceback
        traceback.print_exc()
else:
    print("generate_clips function not found")
    
# Check what functions are available in engine
print("\nAvailable engine functions:")
for attr in dir(engine):
    if callable(getattr(engine, attr)) and not attr.startswith('_'):
        print(f"  - {attr}")
