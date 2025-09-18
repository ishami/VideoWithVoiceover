#!/usr/bin/env python3
import engine
import time
import threading
from pathlib import Path

print("Monitoring media download activity with correct function...")

# Create a test workspace
test_workspace = Path("/tmp/test_video_monitor2")
test_workspace.mkdir(exist_ok=True)

# Monkey patch the correct download function
original_download = engine._download_url_with_extension if hasattr(engine, '_download_url_with_extension') else None

def logged_download(url, folder, expected_type='auto', base_name=None):
    print(f"\n[DOWNLOAD] URL: {url}")
    print(f"[DOWNLOAD] Folder: {folder}")
    print(f"[DOWNLOAD] Expected type: {expected_type}")
    print(f"[DOWNLOAD] Base name: {base_name}")
    
    if original_download:
        try:
            result = original_download(url, folder, expected_type, base_name)
            print(f"[DOWNLOAD] Result: {result}")
            return result
        except Exception as e:
            print(f"[DOWNLOAD] ERROR: {e}")
            import traceback
            traceback.print_exc()
            return None
    return None

if original_download:
    engine._download_url_with_extension = logged_download
else:
    print("WARNING: _download_url_with_extension not found!")

# Test the regeneration directly
print("\nTriggering regeneration...")
success, message = engine.save_script_and_regenerate(
    script="Beautiful nature scenery. Mountains and lakes. Peaceful forests.",
    user_id=1,
    project_id=1,
    workspace_dir=str(test_workspace)
)

print(f"Regeneration started: {success} - {message}")

# Wait longer to see downloads
print("\nWaiting for background activity...")
for i in range(20):
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
        size = item.stat().st_size
        print(f"  - {item.relative_to(test_workspace)} ({size} bytes)")

# Also check if there are any error logs
print("\nChecking for download errors in workspace:")
error_files = list(test_workspace.glob("*error*"))
if error_files:
    for ef in error_files:
        print(f"Error file: {ef}")
