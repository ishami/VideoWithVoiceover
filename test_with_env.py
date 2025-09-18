import os
import sys

# Set environment variables first
os.environ['PIXABAY_API_KEY'] = "44812949-ba98a63acdbb20b31f0281193"
os.environ['PEXELS_API_KEY'] = "e4agaHhuOEpih3K562pmje6YJiy2jSQ37bYJU1nm5nw6NmeualG8afvG"
os.environ['UNSPLASH_API_KEY'] = "ATMcaMHzCfB789pGt8m6L5Z3YyvdgndRqiBNaxwmbf8"

# Remove engine from sys.modules if already loaded
if 'engine' in sys.modules:
    del sys.modules['engine']

# Now import engine
sys.path.insert(0, '.')
import engine

print(f"engine.PIXABAY_API_KEY: {engine.PIXABAY_API_KEY[:8] if engine.PIXABAY_API_KEY else 'NOT SET'}...")
print(f"engine.PEXELS_API_KEY: {engine.PEXELS_API_KEY[:8] if engine.PEXELS_API_KEY else 'NOT SET'}...")
print(f"engine.UNSPLASH_API_KEY: {engine.UNSPLASH_API_KEY[:8] if engine.UNSPLASH_API_KEY else 'NOT SET'}...")

# Test search
print("\nTesting search with nature keyword:")
results = engine._search_pixabay_images("nature")
print(f"Pixabay results: {len(results)}")
if results:
    print(f"First result: {results[0][:80]}...")
