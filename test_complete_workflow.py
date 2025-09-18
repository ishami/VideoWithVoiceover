#!/usr/bin/env python3
import engine
import os
from pathlib import Path

print("Testing complete media download workflow...")

# Test search functions
print("\n1. Testing search functions:")
for search_func, name in [
    (engine._search_pixabay_images, "Pixabay Images"),
    (engine._search_pexels_images, "Pexels Images"),
    (engine._search_unsplash, "Unsplash"),
    (engine._search_pixabay_videos, "Pixabay Videos"),
    (engine._search_pexels_videos, "Pexels Videos")
]:
    try:
        results = search_func("nature")
        print(f"   ✓ {name}: {len(results)} results")
    except Exception as e:
        print(f"   ✗ {name}: {e}")

# Test complete regeneration
print("\n2. Testing complete regeneration workflow:")
test_workspace = Path("/tmp/test_complete")
test_workspace.mkdir(exist_ok=True)

success, message = engine.save_script_and_regenerate(
    script="Beautiful nature scenes. Majestic mountains. Crystal clear lakes.",
    user_id=1,
    project_id=2,
    workspace_dir=str(test_workspace)
)

print(f"   Regeneration: {success} - {message}")

# Wait for completion
import time
print("\n3. Waiting for completion...")
for i in range(15):
    time.sleep(1)
    if engine.manifest_is_ready(user_id=1, project_id=2):
        print("   ✓ Manifest ready!")
        break
    print(".", end="", flush=True)

print("\n\n4. Final workspace contents:")
for root, dirs, files in os.walk(test_workspace):
    level = root.replace(str(test_workspace), '').count(os.sep)
    indent = ' ' * 2 * level
    print(f'{indent}{os.path.basename(root)}/')
    sub_indent = ' ' * 2 * (level + 1)
    for file in files[:5]:  # Show first 5 files per directory
        size = os.path.getsize(os.path.join(root, file))
        print(f'{sub_indent}{file} ({size:,} bytes)')
    if len(files) > 5:
        print(f'{sub_indent}... and {len(files)-5} more files')

# Check manifest
manifest_path = test_workspace / "clips.json"
if manifest_path.exists():
    import json
    with open(manifest_path) as f:
        manifest = json.load(f)
    print(f"\n5. Manifest summary:")
    print(f"   Media clips: {len(manifest.get('media_clips', []))}")
    print(f"   Music clips: {len(manifest.get('music_clips', []))}")
