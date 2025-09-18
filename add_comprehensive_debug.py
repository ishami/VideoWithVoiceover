#!/usr/bin/env python3

with open('engine.py', 'r') as f:
    content = f.read()

# Add debug right after collecting all search results
content = content.replace(
    'video_urls = []',
    'print(f"[DEBUG] After all searches, media_urls has {len(media_urls)} items")\n                video_urls = []'
)

# Add debug after video processing
content = content.replace(
    'media_urls.extend(video_urls)',
    'media_urls.extend(video_urls)\n                    print(f"[DEBUG] After adding videos, media_urls has {len(media_urls)} items")'
)

# Add debug right before the condition check
content = content.replace(
    'if not media_urls:',
    'print(f"[DEBUG] Before checking if not media_urls: len={len(media_urls)}")\n                    if not media_urls:'
)

# Also add debug in the not media_urls branch
content = content.replace(
    'print(f"[engine] Warning: No media found for keyword: {kw}")',
    'print(f"[engine] Warning: No media found for keyword: {kw}")\n                        print(f"[DEBUG] Continuing to next keyword because media_urls is empty")'
)

with open('engine.py', 'w') as f:
    f.write(content)

print("Added comprehensive debugging")
