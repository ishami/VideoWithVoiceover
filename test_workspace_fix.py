#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/myapp/apps/VideoWithVoiceover')

from engine import get_user_workspace_path

# Test the function
print("Testing get_user_workspace_path...")
workspace = get_user_workspace_path(1, 62)
print(f"Result: {workspace}")
print(f"Absolute path: {workspace.absolute()}")
print(f"Expected: /home/myapp/apps/VideoWithVoiceover/workspace/user_1/project_62")
print(f"Correct: {str(workspace.absolute()) == '/home/myapp/apps/VideoWithVoiceover/workspace/user_1/project_62'}")

# Check if it creates the directory
print(f"\nDirectory exists: {workspace.exists()}")
print(f"Is directory: {workspace.is_dir()}")

# Check media and music subdirs
media_dir = workspace / "media"
music_dir = workspace / "music"
print(f"\nMedia dir would be: {media_dir}")
print(f"Music dir would be: {music_dir}")
