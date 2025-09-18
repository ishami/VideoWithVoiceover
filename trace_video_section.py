#!/usr/bin/env python3

with open('engine.py', 'r') as f:
    content = f.read()

# Add debug after video searches
content = content.replace(
    'pixabay_videos = _search_pixabay_videos(kw)',
    'pixabay_videos = _search_pixabay_videos(kw)\n                        print(f"[DEBUG] Pixabay videos: {len(pixabay_videos)}")'
)

content = content.replace(
    'pexels_videos = _search_pexels_videos(kw)',
    'pexels_videos = _search_pexels_videos(kw)\n                        print(f"[DEBUG] Pexels videos: {len(pexels_videos)}")'
)

# Add debug to see if video combination happens
content = content.replace(
    'for url in pixabay_videos + pexels_videos:',
    'print(f"[DEBUG] Processing {len(pixabay_videos + pexels_videos)} video URLs")\n                    for url in pixabay_videos + pexels_videos:'
)

# Add a marker right before media download should happen
content = content.replace(
    'print(f"[DEBUG] Before checking if not media_urls: len={len(media_urls)}")',
    'print(f"[DEBUG] RIGHT BEFORE DOWNLOAD CHECK - media_urls: {len(media_urls)}")\n                    print(f"[DEBUG] Before checking if not media_urls: len={len(media_urls)}")'
)

with open('engine.py', 'w') as f:
    f.write(content)

print("Added video section tracing")
