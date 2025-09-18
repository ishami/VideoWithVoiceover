#!/usr/bin/env python3

with open('engine.py', 'r') as f:
    content = f.read()

# Find and add debugging after each search call
import re

# Add debug after media URL collection
pattern = r'(media_urls = .*?\n)'
replacement = r'\1                    print(f"[DEBUG] Collected {len(media_urls)} media URLs")\n'
content = re.sub(pattern, replacement, content)

# Also add debug to show the actual search aggregation
pattern = r'(media_urls\s*=\s*
$$

$$)'
replacement = r'media_urls = []\n                    print(f"[DEBUG] Initialized media_urls for keyword: {kw}")'
content = re.sub(pattern, replacement, content)

# Add debug after extend/append operations
pattern = r'(media_urls\.extend$.*?$)'
replacement = r'\1\n                        print(f"[DEBUG] After extend: {len(media_urls)} URLs")'
content = re.sub(pattern, replacement, content)

with open('engine.py', 'w') as f:
    f.write(content)

print("Added URL collection debugging")
