#!/usr/bin/env python3
import engine

print("Checking API keys in engine module:")
print(f"PIXABAY_API_KEY: {engine.PIXABAY_API_KEY[:10]}..." if engine.PIXABAY_API_KEY else "PIXABAY_API_KEY: None")
print(f"PEXELS_API_KEY: {engine.PEXELS_API_KEY[:10]}..." if engine.PEXELS_API_KEY else "PEXELS_API_KEY: None")
print(f"UNSPLASH_API_KEY: {engine.UNSPLASH_API_KEY[:10]}..." if engine.UNSPLASH_API_KEY else "UNSPLASH_API_KEY: None")

# Test search functions directly
print("\nTesting search functions:")
results = engine._search_pixabay_images("nature")
print(f"Pixabay results: {len(results)} images")

results = engine._search_pexels_images("nature")  
print(f"Pexels results: {len(results)} images")

results = engine._search_unsplash("nature")
print(f"Unsplash results: {len(results)} images")
