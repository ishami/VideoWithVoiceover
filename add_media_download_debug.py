#!/usr/bin/env python3

with open('engine.py', 'r') as f:
    lines = f.readlines()

# Find where media_urls.extend is called and add debugging after it
new_lines = []
for i, line in enumerate(lines):
    new_lines.append(line)
    
    # Add debug after media URL extensions
    if 'media_urls.extend(' in line and 'print' not in lines[i+1]:
        indent = len(line) - len(line.lstrip())
        new_lines.append(' ' * indent + 'print(f"[DEBUG] Extended media_urls, now has {len(media_urls)} URLs")\n')
    
    # Add debug after collecting all URLs for a keyword
    if 'video_urls = []' in line:
        indent = len(line) - len(line.lstrip())
        new_lines.append(' ' * indent + 'print(f"[DEBUG] Total media_urls before videos: {len(media_urls)}")\n')

with open('engine.py', 'w') as f:
    f.writelines(new_lines)

print("Added media download debugging")
