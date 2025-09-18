#!/usr/bin/env python3

with open('engine.py', 'r') as f:
    lines = f.readlines()

# Find the video processing section
for i in range(len(lines)):
    # Look for the video processing loop that's incorrectly indented
    if 'for url in pixabay_videos + pexels_videos:' in lines[i]:
        # This line and everything after should be dedented to match the try block level
        current_indent = len(lines[i]) - len(lines[i].lstrip())
        
        # It should have 16 spaces (same as the try blocks above), not 20
        if current_indent == 20:
            print(f"Found incorrectly indented video loop at line {i+1}")
            # Fix this line and subsequent lines until we hit the except or another major block
            j = i
            while j < len(lines):
                if lines[j].strip() and not lines[j].lstrip().startswith('#'):
                    line_indent = len(lines[j]) - len(lines[j].lstrip())
                    if line_indent >= 20:
                        # Reduce indent by 4 spaces
                        lines[j] = lines[j][4:]
                    elif line_indent < 16:
                        # We've reached the end of this block
                        break
                j += 1
            print(f"Fixed indentation for lines {i+1} to {j}")
            break

with open('engine.py', 'w') as f:
    f.writelines(lines)

print("Video processing indentation fixed")
