#!/usr/bin/env python3
import engine
import time
import threading
from pathlib import Path

print("Monitoring media download activity...")

# Create a test workspace
test_workspace = Path("/tmp/test_video_monitor")
test_workspace.mkdir(exist_ok=True)

# Monkey patch the download function to log activity
original_download = engine._download_url if hasattr(engine, '_download_url') else None

def logged_download(url, dest):
    print(f"\n[DOWNLOAD] Attempting to download: {url}")
    print(f"[DOWNLOAD] Destination: {dest}")
    if original_download:
        result = original_download(url, dest)
        print(f"[DOWNLOAD] Result: {'Success' if result else 'Failed'}")
        return result
    return False

if original_download:
    engine._download_url = logged_download

# Test the regeneration directly
print("\nTriggering regeneration...")
success, message = engine.save_script_and_regenerate(
    script="Test nature video. Beautiful landscapes. Amazing views.",
    user_id=1,
    project_id=1,
    workspace_dir=str(test_workspace)
)

print(f"Regeneration started: {success} - {message}")

# Wait a bit to see if downloads happen
print("\nWaiting for background activity...")
for i in range(10):
    time.sleep(1)
    print(".", end="", flush=True)
    
    # Check if manifest is ready
    if hasattr(engine, 'manifest_is_ready'):
        if engine.manifest_is_ready(user_id=1, project_id=1):
            print("\nManifest is ready!")
            break

print("\n\nChecking workspace contents:")
for item in test_workspace.rglob("*"):
    if item.is_file():
        print(f"  - {item.relative_to(test_workspace)}")
