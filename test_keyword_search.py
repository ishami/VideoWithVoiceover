import sys
sys.path.insert(0, '.')

from engine import _search_pixabay_images, _search_pexels_images, _search_unsplash

# Test various keywords
test_keywords = ["singing birds", "birds", "singing", "bird", "nature", "animal"]

for keyword in test_keywords:
    print(f"\n=== Testing keyword: '{keyword}' ===")
    
    pixabay = _search_pixabay_images(keyword)
    print(f"Pixabay: {len(pixabay)} results")
    if pixabay:
        print(f"  First: {pixabay[0][:80]}...")
    
    pexels = _search_pexels_images(keyword)
    print(f"Pexels: {len(pexels)} results")
    if pexels:
        print(f"  First: {pexels[0][:80]}...")
    
    unsplash = _search_unsplash(keyword)
    print(f"Unsplash: {len(unsplash)} results")
    if unsplash:
        print(f"  First: {unsplash[0][:80]}...")
