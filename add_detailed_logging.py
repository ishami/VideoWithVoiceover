#!/usr/bin/env python3

with open('engine.py', 'r') as f:
    content = f.read()

# Add logging after each search function makes the request
search_replacements = [
    # Pixabay images
    ('    return [h["largeImageURL"] for h in r.json().get("hits", [])]',
     '''    data = r.json()
    print(f"[DEBUG] Pixabay response: status={r.status_code}, total={data.get('total', 0)}, hits={len(data.get('hits', []))}")
    urls = [h["largeImageURL"] for h in data.get("hits", [])]
    print(f"[DEBUG] Pixabay returning {len(urls)} URLs")
    return urls'''),
    
    # Pexels images
    ('    return [p["src"]["original"] for p in r.json().get("photos", [])]',
     '''    data = r.json()
    print(f"[DEBUG] Pexels response: status={r.status_code}, total={data.get('total_results', 0)}, photos={len(data.get('photos', []))}")
    urls = [p["src"]["original"] for p in data.get("photos", [])]
    print(f"[DEBUG] Pexels returning {len(urls)} URLs")
    return urls'''),
    
    # Unsplash
    ('    return [p["urls"]["regular"] for p in r.json().get("results", [])]',
     '''    data = r.json()
    print(f"[DEBUG] Unsplash response: status={r.status_code}, total={data.get('total', 0)}, results={len(data.get('results', []))}")
    urls = [p["urls"]["regular"] for p in data.get("results", [])]
    print(f"[DEBUG] Unsplash returning {len(urls)} URLs")
    return urls''')
]

for old, new in search_replacements:
    content = content.replace(old, new)

with open('engine.py', 'w') as f:
    f.write(content)

print("Added detailed logging to search functions")
