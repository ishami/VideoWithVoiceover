#!/usr/bin/env python3
import re

with open('engine.py', 'r') as f:
    content = f.read()

# Remove all DEBUG print statements
content = re.sub(r'^\s*print\(.*?
$$
DEBUG
$$.*?\)$', '', content, flags=re.MULTILINE)

# Remove empty lines that result from removal
content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)

with open('engine.py', 'w') as f:
    f.write(content)

print("Removed DEBUG print statements")
