import sys
sys.path.insert(0, '.')

import engine

# Check if requests module and API keys are available in engine
print("=== Checking engine module state ===")
print(f"engine.requests: {engine.requests}")
print(f"engine.PIXABAY_API_KEY: {engine.PIXABAY_API_KEY[:8] if engine.PIXABAY_API_KEY else 'NOT SET'}...")
print(f"engine.PEXELS_API_KEY: {engine.PEXELS_API_KEY[:8] if engine.PEXELS_API_KEY else 'NOT SET'}...")
print(f"engine.UNSPLASH_API_KEY: {engine.UNSPLASH_API_KEY[:8] if engine.UNSPLASH_API_KEY else 'NOT SET'}...")

# Test search functions with debug
print("\n=== Testing Pixabay search with debug ===")
try:
    import requests
    
    # Manual search test
    if engine.requests and engine.PIXABAY_API_KEY:
        print("Requests and API key available, testing manual search...")
        r = requests.get("https://pixabay.com/api/",
                        params={"key": engine.PIXABAY_API_KEY,
                                "q": "nature", "image_type": "photo", "per_page": 6})
        print(f"Response status: {r.status_code}")
        print(f"Response content preview: {str(r.text)[:200]}...")
        data = r.json()
        hits = data.get("hits", [])
        print(f"Found {len(hits)} hits")
        if hits:
            print(f"First hit: {hits[0].get('largeImageURL', 'No URL')}")
    else:
        print(f"Condition failed: requests={engine.requests}, API_KEY={bool(engine.PIXABAY_API_KEY)}")
        
except Exception as e:
    import traceback
    print(f"Error: {e}")
    traceback.print_exc()

# Test the actual function
print("\n=== Testing engine._search_pixabay_images ===")
result = engine._search_pixabay_images("nature")
print(f"Result: {result}")
