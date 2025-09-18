#!/usr/bin/env python3

with open('engine.py', 'r') as f:
    content = f.read()

# Add debug print at the start of _download_url_with_extension
search_str = 'def _download_url_with_extension(url: str, folder: Path, expected_type: str = \'auto\','
replace_str = '''def _download_url_with_extension(url: str, folder: Path, expected_type: str = 'auto',
                                 base_name: str = None) -> Path | None:
    """Download file with proper extension detection"""
    print(f"[DEBUG] _download_url_with_extension called:")
    print(f"  - URL: {url}")
    print(f"  - Folder: {folder}")
    print(f"  - Requests module: {requests}")'''

content = content.replace(
    search_str + '\n                                 base_name: str = None) -> Path | None:\n    """Download file with proper extension detection"""',
    replace_str
)

with open('engine.py', 'w') as f:
    f.write(content)

print("Added debug logging to _download_url_with_extension")
