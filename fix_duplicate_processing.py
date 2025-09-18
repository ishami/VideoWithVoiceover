#!/usr/bin/env python3

with open('engine.py', 'r') as f:
    content = f.read()

# Add a processing lock to prevent duplicate runs
if "processing_locks = {}" not in content:
    # Add at the top after imports
    import_section_end = content.find("# ─────────────")
    if import_section_end > 0:
        content = content[:import_section_end] + "processing_locks = {}  # Track active processing per project\n\n" + content[import_section_end:]

# Modify _heavy_regenerate_wrapper to check lock
old_wrapper_start = "def _heavy_regenerate_wrapper(script: str, user_id: Optional[int], project_id: Optional[int]) -> None:"
new_wrapper_start = """def _heavy_regenerate_wrapper(script: str, user_id: Optional[int], project_id: Optional[int]) -> None:
    # Check if already processing
    lock_key = f"{user_id}_{project_id}"
    if lock_key in processing_locks:
        print(f"[engine] Already processing for project {project_id}, skipping duplicate")
        return
    
    processing_locks[lock_key] = True"""

content = content.replace(old_wrapper_start + '\n    """', new_wrapper_start + '\n    """')

# Add lock cleanup in finally block
old_finally = """finally:
        if user_id is not None and project_id is not None:"""

new_finally = """finally:
        # Clean up processing lock
        lock_key = f"{user_id}_{project_id}"
        processing_locks.pop(lock_key, None)
        
        if user_id is not None and project_id is not None:"""

content = content.replace(old_finally, new_finally)

with open('engine.py', 'w') as f:
    f.write(content)

print("Added processing lock to prevent duplicates")
