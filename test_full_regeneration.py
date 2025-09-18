import sys
sys.path.insert(0, '.')

from engine import (_search_pixabay_images, _search_pexels_images, _search_unsplash, 
                    _download_url_with_extension, get_user_workspace_path)
from pathlib import Path
import time

# Test parameters
user_id = 1
project_id = 66

# Get workspace
workspace = get_user_workspace_path(user_id, project_id)
media_dir = workspace / "media"
media_dir.mkdir(exist_ok=True)

print(f"Workspace: {workspace}")
print(f"Media directory: {media_dir}")

# Read keywords
keywords_file = workspace / "keywords.txt"
if keywords_file.exists():
    keywords = [k.strip() for k in keywords_file.read_text().split(",") if k.strip()]
    print(f"\nKeywords from file: {keywords}")
else:
    keywords = ["nature", "birds"]
    print(f"\nUsing default keywords: {keywords}")

# Search and download media
media_paths = []
for kw in keywords:
    print(f"\n--- Processing keyword: '{kw}' ---")
    
    # Search images
    print(f"Searching Pixabay for '{kw}'...")
    pixabay_urls = _search_pixabay_images(kw)
    print(f"  Found {len(pixabay_urls)} Pixabay images")
    
    print(f"Searching Pexels for '{kw}'...")
    pexels_urls = _search_pexels_images(kw)
    print(f"  Found {len(pexels_urls)} Pexels images")
    
    print(f"Searching Unsplash for '{kw}'...")
    unsplash_urls = _search_unsplash(kw)
    print(f"  Found {len(unsplash_urls)} Unsplash images")
    
    # Combine all URLs
    all_urls = pixabay_urls[:2] + pexels_urls[:2] + unsplash_urls[:2]
    print(f"\nTotal URLs to download: {len(all_urls)}")
    
    # Download media
    for i, url in enumerate(all_urls[:3]):  # Limit to 3 for testing
        print(f"\nDownloading {i+1}/{min(3, len(all_urls))}: {url[:80]}...")
        base_filename = f"media_{len(media_paths) + 1}_{kw.replace(' ', '_')}"
        
        try:
            result = _download_url_with_extension(url, media_dir, 'image', base_filename)
            if result:
                media_paths.append(str(result))
                print(f"  ✓ Saved as: {result}")
            else:
                print(f"  ❌ Download failed")
        except Exception as e:
            print(f"  ❌ Error: {e}")

print(f"\n=== Summary ===")
print(f"Total media downloaded: {len(media_paths)}")
print(f"Media files:")
for p in media_paths:
    print(f"  - {p}")

# Check media directory
print(f"\nActual files in {media_dir}:")
files = list(media_dir.glob("*"))
print(f"Found {len(files)} files:")
for f in files[:10]:
    print(f"  - {f.name} ({f.stat().st_size} bytes)")
