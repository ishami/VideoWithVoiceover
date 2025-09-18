#!/usr/bin/env python3

with open('engine.py', 'r') as f:
    content = f.read()

# Add logging at the start of each search function
replacements = [
    ('def _search_pixabay_images(q: str) -> list[str]:\n',
     'def _search_pixabay_images(q: str) -> list[str]:\n    print(f"[DEBUG] _search_pixabay_images called with query: {q}, API_KEY present: {bool(PIXABAY_API_KEY)}")\n'),
    
    ('def _search_pexels_images(q: str) -> list[str]:\n',
     'def _search_pexels_images(q: str) -> list[str]:\n    print(f"[DEBUG] _search_pexels_images called with query: {q}, API_KEY present: {bool(PEXELS_API_KEY)}")\n'),
    
    ('def _search_unsplash(q: str) -> list[str]:\n',
     'def _search_unsplash(q: str) -> list[str]:\n    print(f"[DEBUG] _search_unsplash called with query: {q}, API_KEY present: {bool(UNSPLASH_API_KEY)}")\n'),
]

for old, new in replacements:
    content = content.replace(old, new)

with open('engine.py', 'w') as f:
    f.write(content)

print("Added entry logging to search functions")
