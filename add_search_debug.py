#!/usr/bin/env python3

# Read engine.py
with open('engine.py', 'r') as f:
    lines = f.readlines()

# Find and modify the search functions to add debug logging
output_lines = []
for i, line in enumerate(lines):
    output_lines.append(line)
    
    # Add debug at the start of each search function
    if line.strip().startswith('def _search_pixabay_images(q: str)'):
        # Insert debug after the function definition
        if i + 1 < len(lines):
            output_lines.append(f'    print(f"[DEBUG] _search_pixabay_images called with q={{q}}, API_KEY={{PIXABAY_API_KEY[:8] if PIXABAY_API_KEY else \'NONE\'}}..., requests={{requests}}")\n')
    
    elif line.strip().startswith('def _search_pexels_images(q: str)'):
        if i + 1 < len(lines):
            output_lines.append(f'    print(f"[DEBUG] _search_pexels_images called with q={{q}}, API_KEY={{PEXELS_API_KEY[:8] if PEXELS_API_KEY else \'NONE\'}}..., requests={{requests}}")\n')
    
    elif line.strip().startswith('def _search_unsplash(q: str)'):
        if i + 1 < len(lines):
            output_lines.append(f'    print(f"[DEBUG] _search_unsplash called with q={{q}}, API_KEY={{UNSPLASH_API_KEY[:8] if UNSPLASH_API_KEY else \'NONE\'}}..., requests={{requests}}")\n')

# Write back
with open('engine.py', 'w') as f:
    f.writelines(output_lines)

print("Debug logging added to search functions")
