import sys
sys.path.insert(0, '.')

from engine import _download_url_with_extension
from pathlib import Path

# Test URL from Pixabay
test_url = "https://pixabay.com/get/g3c99f38b45781c2dd7eb1af73c32bd3e62a6eac9e2033474c3cc298c0e7075aaf3392d0643effd049340dfe0e274c53d40a059b31f87d55c645b874f474ab5d8_1280.jpg"

# Create test directory
test_dir = Path("test_download_dir")
test_dir.mkdir(exist_ok=True)

print(f"Attempting to download: {test_url}")
print(f"To directory: {test_dir}")

result = _download_url_with_extension(test_url, test_dir, 'image', 'test_bird_image')

if result:
    print(f"✓ Download successful: {result}")
    print(f"  File exists: {result.exists()}")
    print(f"  File size: {result.stat().st_size} bytes")
else:
    print("❌ Download failed - returned None")
