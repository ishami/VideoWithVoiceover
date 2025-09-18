import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import engine functions
from engine import _search_pixabay_images, _search_pexels_images, _search_unsplash, _download_url_with_extension

# Test keyword
keyword = "nature"
print(f"Testing media download for keyword: '{keyword}'")

# Search for images
print("\n1. Searching for images...")
pixabay_urls = _search_pixabay_images(keyword)
print(f"   Pixabay returned {len(pixabay_urls)} URLs")
if pixabay_urls:
    print(f"   First URL: {pixabay_urls[0]}")

pexels_urls = _search_pexels_images(keyword)
print(f"   Pexels returned {len(pexels_urls)} URLs")
if pexels_urls:
    print(f"   First URL: {pexels_urls[0]}")

unsplash_urls = _search_unsplash(keyword)
print(f"   Unsplash returned {len(unsplash_urls)} URLs")
if unsplash_urls:
    print(f"   First URL: {unsplash_urls[0]}")

# Try to download one image
if pixabay_urls:
    print("\n2. Attempting to download first Pixabay image...")
    test_dir = Path("test_media_download")
    test_dir.mkdir(exist_ok=True)
    
    url = pixabay_urls[0]
    result = _download_url_with_extension(url, test_dir, 'image', 'test_image')
    
    if result:
        print(f"   ✓ Download successful: {result}")
        print(f"   File size: {os.path.getsize(result)} bytes")
    else:
        print("   ❌ Download failed")

# Check if requests module is available in engine context
print("\n3. Checking requests module availability...")
import engine
print(f"   engine.requests: {engine.requests}")
print(f"   PIXABAY_API_KEY in engine: {'Yes' if engine.PIXABAY_API_KEY else 'No'}")
print(f"   PEXELS_API_KEY in engine: {'Yes' if engine.PEXELS_API_KEY else 'No'}")
print(f"   UNSPLASH_API_KEY in engine: {'Yes' if engine.UNSPLASH_API_KEY else 'No'}")
