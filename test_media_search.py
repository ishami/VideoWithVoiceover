import os
import requests

def test_pixabay():
    api_key = os.getenv("PIXABAY_API_KEY")
    if not api_key:
        print("❌ PIXABAY_API_KEY not found in environment")
        return False
    
    print(f"✓ PIXABAY_API_KEY found: {api_key[:8]}...")
    
    # Test API
    url = "https://pixabay.com/api/"
    params = {
        "key": api_key,
        "q": "nature",
        "per_page": 3,
        "image_type": "photo"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            hits = data.get("hits", [])
            print(f"✓ Pixabay API works! Found {len(hits)} images")
            for hit in hits[:2]:
                print(f"  - {hit.get('largeImageURL', 'No URL')}")
            return True
        else:
            print(f"❌ Pixabay API error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Pixabay request failed: {e}")
        return False

def test_pexels():
    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key:
        print("❌ PEXELS_API_KEY not found in environment")
        return False
    
    print(f"✓ PEXELS_API_KEY found: {api_key[:8]}...")
    
    # Test API
    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": api_key}
    params = {
        "query": "nature",
        "per_page": 3
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            photos = data.get("photos", [])
            print(f"✓ Pexels API works! Found {len(photos)} photos")
            for photo in photos[:2]:
                print(f"  - {photo.get('src', {}).get('original', 'No URL')}")
            return True
        else:
            print(f"❌ Pexels API error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Pexels request failed: {e}")
        return False

def test_unsplash():
    api_key = os.getenv("UNSPLASH_ACCESS_KEY") or os.getenv("UNSPLASH_API_KEY")
    if not api_key:
        print("❌ UNSPLASH_ACCESS_KEY/UNSPLASH_API_KEY not found in environment")
        return False
    
    print(f"✓ UNSPLASH_API_KEY found: {api_key[:8]}...")
    
    # Test API
    url = "https://api.unsplash.com/search/photos"
    headers = {"Authorization": f"Client-ID {api_key}"}
    params = {
        "query": "nature",
        "per_page": 3
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            print(f"✓ Unsplash API works! Found {len(results)} photos")
            for photo in results[:2]:
                print(f"  - {photo.get('urls', {}).get('regular', 'No URL')}")
            return True
        else:
            print(f"❌ Unsplash API error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Unsplash request failed: {e}")
        return False

def check_workspace():
    upload_folder = os.getenv("UPLOAD_FOLDER", "uploads")
    print(f"\n📁 Upload folder: {upload_folder}")
    
    if os.path.exists(upload_folder):
        print("✓ Upload folder exists")
        # List recent workspaces
        workspaces = [d for d in os.listdir(upload_folder) if d.startswith("workspace_")]
        if workspaces:
            print(f"Found {len(workspaces)} workspace(s):")
            for ws in sorted(workspaces)[-3:]:  # Show last 3
                ws_path = os.path.join(upload_folder, ws)
                media_dir = os.path.join(ws_path, "media")
                if os.path.exists(media_dir):
                    media_files = os.listdir(media_dir)
                    print(f"  - {ws}: {len(media_files)} media files")
                else:
                    print(f"  - {ws}: no media directory")
    else:
        print("❌ Upload folder does not exist")

def check_requests_module():
    try:
        import requests
        print("✓ requests module is available")
        return True
    except ImportError:
        print("❌ requests module is NOT available")
        return False

if __name__ == "__main__":
    print("🔍 Testing Media Search APIs...\n")
    
    print("=" * 50)
    print("Checking environment variables:")
    print(f"PIXABAY_API_KEY: {'Set' if os.getenv('PIXABAY_API_KEY') else 'Not set'}")
    print(f"PEXELS_API_KEY: {'Set' if os.getenv('PEXELS_API_KEY') else 'Not set'}")
    print(f"UNSPLASH_ACCESS_KEY: {'Set' if os.getenv('UNSPLASH_ACCESS_KEY') else 'Not set'}")
    print(f"UNSPLASH_API_KEY: {'Set' if os.getenv('UNSPLASH_API_KEY') else 'Not set'}")
    
    print("\n" + "=" * 50)
    check_requests_module()
    
    print("\n" + "=" * 50)
    test_pixabay()
    print("\n" + "=" * 50)
    test_pexels()
    print("\n" + "=" * 50)
    test_unsplash()
    print("\n" + "=" * 50)
    check_workspace()
