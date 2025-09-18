import sys
sys.path.insert(0, '.')

from engine import save_script_and_regenerate, get_user_workspace_path
import time
import os

# Test parameters
user_id = 1
project_id = 66
test_script = "This is a test script about singing birds. They are beautiful creatures. Nature is amazing."

# Get workspace path
workspace = get_user_workspace_path(user_id, project_id)
print(f"Workspace path: {workspace}")

# Check current media directory
media_dir = workspace / "media"
print(f"\nCurrent media files in {media_dir}:")
if media_dir.exists():
    files = list(media_dir.glob("*"))
    print(f"  Found {len(files)} files")
    for f in files[:5]:
        print(f"  - {f.name}")

# Trigger regeneration
print(f"\nTriggering regeneration for user {user_id}, project {project_id}...")
success, message = save_script_and_regenerate(test_script, user_id, project_id)
print(f"Result: {success}, Message: {message}")

# Wait a bit for the background thread to start
print("\nWaiting for regeneration to process...")
time.sleep(5)

# Check status
status_file = workspace / "status.txt"
if status_file.exists():
    print(f"Status: {status_file.read_text()}")

# Wait more and check media again
time.sleep(10)
print(f"\nChecking media files again...")
if media_dir.exists():
    files = list(media_dir.glob("*"))
    print(f"  Found {len(files)} files")
    for f in files[:5]:
        print(f"  - {f.name} ({f.stat().st_size} bytes)")
