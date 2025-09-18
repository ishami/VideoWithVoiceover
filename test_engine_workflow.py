#!/usr/bin/env python3
import engine
import json
from pathlib import Path

print("Exploring engine workflow...")

# Check for the main entry point
if hasattr(engine, 'save_main_tab'):
    print("\nFound save_main_tab - this appears to be the entry point")
    
# Check for script saving
if hasattr(engine, 'save_script_and_regenerate'):
    print("\nFound save_script_and_regenerate")
    # Check its signature
    import inspect
    sig = inspect.signature(engine.save_script_and_regenerate)
    print(f"Parameters: {sig}")

# Look for the actual search functions in the module
print("\nSearching for media search functions:")
for name in dir(engine):
    if 'search' in name.lower() or 'download' in name.lower():
        print(f"  - {name}")

# Check if there's a manifest file structure
print("\nChecking for manifest handling:")
if hasattr(engine, 'manifest_is_ready'):
    sig = inspect.signature(engine.manifest_is_ready)
    print(f"manifest_is_ready signature: {sig}")

# Test the search functions directly
print("\n" + "="*50)
print("Direct search function test:")
print("="*50)

# The search functions we found earlier
search_results = {}
try:
    results = engine._search_pixabay_images("test")
    print(f"✓ Pixabay search works: {len(results)} results")
    search_results['pixabay'] = results[:2]  # Just first 2
except Exception as e:
    print(f"✗ Pixabay search failed: {e}")

try:
    results = engine._search_pexels_images("test")
    print(f"✓ Pexels search works: {len(results)} results")
    search_results['pexels'] = results[:2]
except Exception as e:
    print(f"✗ Pexels search failed: {e}")

try:
    results = engine._search_unsplash("test")
    print(f"✓ Unsplash search works: {len(results)} results")
    search_results['unsplash'] = results[:2]
except Exception as e:
    print(f"✗ Unsplash search failed: {e}")

# Save results for inspection
with open("search_results.json", "w") as f:
    json.dump(search_results, f, indent=2)
    print("\nSearch results saved to search_results.json")
