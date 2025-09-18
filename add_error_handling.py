#!/usr/bin/env python3

with open('engine.py', 'r') as f:
    lines = f.readlines()

# Find and modify the search functions
output = []
in_search_func = False
func_names = ['_search_pixabay_images', '_search_pexels_images', '_search_unsplash']

i = 0
while i < len(lines):
    line = lines[i]
    
    # Check if we're entering a search function
    for func_name in func_names:
        if f'def {func_name}' in line:
            in_search_func = func_name
            break
    
    # If we're in a search function and see the requests.get line, wrap it
    if in_search_func and 'r = requests.get(' in line:
        # Add try block before the request
        output.append('    try:\n')
        output.append('    ' + line)  # Indent the request line
        
        # Continue adding lines until we find the return statement
        i += 1
        while i < len(lines):
            line = lines[i]
            if line.strip().startswith('return'):
                output.append('    ' + line)  # Indent the return
                # Add except block
                output.append('    except Exception as e:\n')
                output.append(f'        print(f"[ERROR] {in_search_func} failed: {{e}}")\n')
                output.append('        import traceback\n')
                output.append('        traceback.print_exc()\n')
                output.append('        return []\n')
                in_search_func = False
                break
            else:
                output.append('    ' + line)  # Indent other lines
            i += 1
    else:
        output.append(line)
    
    i += 1

with open('engine.py', 'w') as f:
    f.writelines(output)

print("Added error handling to search functions")
