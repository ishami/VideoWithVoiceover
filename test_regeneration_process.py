import os
import sys
sys.path.insert(0, '.')

# Ensure environment variables are set for this test
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY', '')
os.environ['PIXABAY_API_KEY'] = os.getenv('PIXABAY_API_KEY', '')
os.environ['PEXELS_API_KEY'] = os.getenv('PEXELS_API_KEY', '')
os.environ['UNSPLASH_API_KEY'] = os.getenv('UNSPLASH_API_KEY', '')

from engine import save_script_and_regenerate, get_user_workspace_path
import time

user_id = 1
project_id = 66
test_script = "Birds are singing in the trees. Nature is beautiful and peaceful. The melody fills the morning air."

print(f"Testing regeneration for user {user_id}, project {project_id}")
workspace = get_user_workspace_path(user_id, project_id)
print(f"Workspace: {workspace}")

# Check current media
media_dir = workspace / "media"
if media_dir.exists():
    files = list(media_dir.glob("*"))
    print(f"\nCurrent media files: {len(files)}")

# Trigger regeneration
print("\nTriggering regeneration...")
success, message = save_script_and_regenerate(test_script, user_id, project_id)
print(f"Result: {success}, Message: {message}")

# Monitor progress
for i in range(30):
    time.sleep(2)
    status_file = workspace / "status.txt"
    if status_file.exists():
        status = status_file.read_text().strip()
        print(f"[{i*2}s] Status: {status}")
        if "complete" in status.lower() or "error" in status.lower():
            break

# Check final state
print("\nFinal check:")
clips_file = workspace / "clips.json"
if clips_file.exists():
    import json
    clips = json.loads(clips_file.read_text())
    print(f"Media clips: {len(clips.get('media_clips', []))}")
    print(f"Music clips: {len(clips.get('music_clips', []))}")

final_video = workspace / "final" / "video.mp4"
if final_video.exists():
    print(f"✓ Final video created: {final_video} ({final_video.stat().st_size} bytes)")
else:
    print("✗ No final video found")
