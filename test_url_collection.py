#!/usr/bin/env python3
import engine
from pathlib import Path

# Directly test the search and see what happens
print("Testing URL collection...")

# Test Pixabay search
urls = engine._search_pixabay_images("nature")
print(f"Pixabay returned: {urls[:2]}")  # First 2 URLs

# Now let's trace through what should happen in _heavy_regenerate
# by looking at the actual code
print("\nChecking _heavy_regenerate flow...")

# Create a test workspace
test_ws = Path("/tmp/test_trace")
test_ws.mkdir(exist_ok=True)

# Try to follow the exact flow
keywords = ["nature", "landscape"]
media_urls_collected = []

for kw in keywords:
    print(f"\nProcessing keyword: {kw}")
    
    # This is what should happen in the code
    media_urls = []
    
    # Search Pixabay
    try:
        urls = engine._search_pixabay_images(kw)
        print(f"  Pixabay: {len(urls)} URLs")
        media_urls.extend(urls)
    except Exception as e:
        print(f"  Pixabay error: {e}")
    
    print(f"  Total media_urls after searches: {len(media_urls)}")
    media_urls_collected.extend(media_urls)

print(f"\nTotal URLs collected: {len(media_urls_collected)}")
print(f"First URL: {media_urls_collected[0] if media_urls_collected else 'None'}")
