import os
import requests

# Test if requests module works
print("Testing requests module...")
try:
    response = requests.get("https://httpbin.org/get", timeout=5)
    print(f"✓ Requests works: Status {response.status_code}")
except Exception as e:
    print(f"❌ Requests failed: {e}")

# Test API keys
print("\nChecking API keys...")
print(f"PIXABAY_API_KEY: {'Set' if os.getenv('PIXABAY_API_KEY') else 'Not set'}")
print(f"PEXELS_API_KEY: {'Set' if os.getenv('PEXELS_API_KEY') else 'Not set'}")
print(f"UNSPLASH_API_KEY: {'Set' if os.getenv('UNSPLASH_API_KEY') else 'Not set'}")

# Test Pixabay search
pixabay_key = os.getenv('PIXABAY_API_KEY')
if pixabay_key:
    print("\nTesting Pixabay search...")
    try:
        r = requests.get("https://pixabay.com/api/",
                        params={"key": pixabay_key,
                                "q": "nature", "image_type": "photo", "per_page": 3})
        data = r.json()
        hits = data.get("hits", [])
        print(f"✓ Found {len(hits)} images")
        if hits:
            url = hits[0].get('largeImageURL')
            print(f"  First image URL: {url}")
            
            # Try to download
            print("\nTesting download...")
            headers = {'User-Agent': 'Mozilla/5.0'}
            dl_response = requests.get(url, headers=headers, timeout=10)
            print(f"  Download response: {dl_response.status_code}")
            print(f"  Content length: {len(dl_response.content)} bytes")
    except Exception as e:
        print(f"❌ Error: {e}")

# Check keywords file
print("\nChecking keywords file...")
keywords_path = "uploads/workspace_u1_p66/keywords.txt"
if os.path.exists(keywords_path):
    with open(keywords_path, 'r') as f:
        content = f.read()
    print(f"Keywords file exists, content: '{content}'")
    print(f"Content length: {len(content)} characters")
    print(f"Content bytes: {content.encode()}")
    print(f"ASCII values: {[ord(c) for c in content]}")
else:
    print("Keywords file not found")
