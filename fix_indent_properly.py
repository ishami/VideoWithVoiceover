#!/usr/bin/env python3

with open('engine.py', 'r') as f:
    lines = f.readlines()

# Find and fix lines 1501 and similar
for i in range(len(lines)):
    # Remove extra indentation from the debug lines
    if 'print(f"[DEBUG] Pixabay videos:' in lines[i]:
        # This line has 8 extra spaces - it should align with the line above
        lines[i] = lines[i].replace('                        print(f"[DEBUG]', '                    print(f"[DEBUG]')
        print(f"Fixed line {i+1}: Pixabay videos debug")
    
    if 'print(f"[DEBUG] Pexels videos:' in lines[i]:
        lines[i] = lines[i].replace('                        print(f"[DEBUG]', '                    print(f"[DEBUG]')
        print(f"Fixed line {i+1}: Pexels videos debug")

with open('engine.py', 'w') as f:
    f.writelines(lines)

print("Indentation fixed properly")
