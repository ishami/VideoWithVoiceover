#!/usr/bin/env python3
import requests
import json

base_url = "http://localhost:5001"

# First, let's try to submit the main form
data = {
    "target_language": "en",
    "voice": "en-US-AvaMultilingualNeural",
    "platform": "YouTube",
    "genre": "Soundtrack",
    "modify_kw": "yes",
    "bypass": "no",
    "video_title": "Beautiful Nature Landscapes",
    "script": "Nature is amazing. Mountains reach high. Rivers flow peacefully.",
    "base_dir": "/srv/videos",
    "keywords": "nature,landscape,mountains,rivers"
}

# Try POST to main page
response = requests.post(f"{base_url}/", data=data)
print(f"Status: {response.status_code}")
print(f"Response length: {len(response.text)}")

# Check if we got redirected
if response.history:
    print(f"Redirected to: {response.url}")

# Print any error messages
if "error" in response.text.lower():
    print("Possible errors found in response")
    
# Save response for inspection
with open("test_response.html", "w") as f:
    f.write(response.text)
    print("Full response saved to test_response.html")
