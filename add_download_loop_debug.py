#!/usr/bin/env python3

with open('engine.py', 'r') as f:
    content = f.read()

# Add debug before the download loop
content = content.replace(
    'if not media_urls:',
    'print(f"[DEBUG] About to check media_urls: {len(media_urls)} URLs")\n                    if not media_urls:'
)

# Add debug at the start of the download loop
content = content.replace(
    'for i, url in enumerate(media_urls):',
    'print(f"[DEBUG] Starting download loop for {len(media_urls)} media URLs")\n                    for i, url in enumerate(media_urls):'
)

# Add debug for platform check
content = content.replace(
    'if _is_media_suitable_for_platform(url, platform_key):',
    'suitable = _is_media_suitable_for_platform(url, platform_key)\n                        print(f"[DEBUG] URL {url[:50]}... suitable for {platform_key}: {suitable}")\n                        if suitable:'
)

with open('engine.py', 'w') as f:
    f.write(content)

print("Added download loop debugging")
