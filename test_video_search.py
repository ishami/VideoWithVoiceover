#!/usr/bin/env python3
import engine

print("Testing video search functions...")

# Test Pixabay videos
try:
    videos = engine._search_pixabay_videos("nature")
    print(f"Pixabay videos: {len(videos)} results")
    if videos:
        print(f"  First video: {videos[0][:100]}...")
except Exception as e:
    print(f"Pixabay videos error: {e}")

# Test Pexels videos
try:
    videos = engine._search_pexels_videos("nature") 
    print(f"Pexels videos: {len(videos)} results")
    if videos:
        print(f"  First video: {videos[0][:100]}...")
except Exception as e:
    print(f"Pexels videos error: {e}")
