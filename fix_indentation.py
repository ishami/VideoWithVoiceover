#!/usr/bin/env python3

with open('engine.py', 'r') as f:
    lines = f.readlines()

# Find and fix the problematic line
for i in range(len(lines)):
    if 'print(f"[DEBUG] Pixabay videos:' in lines[i] and lines[i].strip() == lines[i]:
        # This line has no indentation but should have some
        # Look at previous line to determine correct indentation
        if i > 0:
            prev_indent = len(lines[i-1]) - len(lines[i-1].lstrip())
            lines[i] = ' ' * prev_indent + lines[i]
            print(f"Fixed indentation on line {i+1}")
    
    if 'print(f"[DEBUG] Pexels videos:' in lines[i] and lines[i].strip() == lines[i]:
        if i > 0:
            prev_indent = len(lines[i-1]) - len(lines[i-1].lstrip())
            lines[i] = ' ' * prev_indent + lines[i]
            print(f"Fixed indentation on line {i+1}")

with open('engine.py', 'w') as f:
    f.writelines(lines)

print("Indentation fixed")
