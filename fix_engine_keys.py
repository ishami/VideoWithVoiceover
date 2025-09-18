#!/usr/bin/env python3
import re

# Read the engine.py file
with open('engine.py', 'r') as f:
    content = f.read()

# Find the API key loading section
old_pattern = r'PIXABAY_API_KEY\s*=\s*os\.getenv$"PIXABAY_API_KEY",\s*""$\s*\nPEXELS_API_KEY\s*=\s*os\.getenv$"PEXELS_API_KEY",\s*""$\s*\nUNSPLASH_API_KEY\s*=\s*os\.getenv$"UNSPLASH_API_KEY",\s*""$'

# Replace with direct values as fallback
new_code = '''PIXABAY_API_KEY  = os.getenv("PIXABAY_API_KEY",  "") or "44812949-ba98a63acdbb20b31f0281193"
PEXELS_API_KEY   = os.getenv("PEXELS_API_KEY",   "") or "e4agaHhuOEpih3K562pmje6YJiy2jSQ37bYJU1nm5nw6NmeualG8afvG"
UNSPLASH_API_KEY = os.getenv("UNSPLASH_API_KEY", "") or "ATMcaMHzCfB789pGt8m6L5Z3YyvdgndRqiBNaxwmbf8"'''

# Replace the pattern
content = re.sub(old_pattern, new_code, content, flags=re.MULTILINE)

# Write back
with open('engine.py', 'w') as f:
    f.write(content)

print("Engine.py updated with fallback API keys")
