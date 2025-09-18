#!/usr/bin/env python3
import requests
from requests.auth import HTTPBasicAuth

session = requests.Session()
base_url = "http://localhost:5001"

# Step 1: Get the login page to get CSRF token
login_page = session.get(f"{base_url}/login")
print(f"Login page status: {login_page.status_code}")

# Extract CSRF token from the login form
import re
csrf_match = re.search(r'name="csrf_token".*?value="([^"]+)"', login_page.text)
if csrf_match:
    csrf_token = csrf_match.group(1)
    print(f"CSRF token found: {csrf_token[:20]}...")
else:
    print("No CSRF token found!")
    exit(1)

# Step 2: Login
login_data = {
    'email': 'test@example.com',
    'password': 'testpass123',
    'csrf_token': csrf_token
}

login_response = session.post(f"{base_url}/login", data=login_data, allow_redirects=False)
print(f"Login response status: {login_response.status_code}")
if login_response.status_code == 302:
    print(f"Redirected to: {login_response.headers.get('Location')}")

# Step 3: Get the main page
main_page = session.get(f"{base_url}/")
print(f"Main page status: {main_page.status_code}")

# Step 4: Submit the video generation form
# Extract new CSRF token
csrf_match = re.search(r'name="csrf_token".*?value="([^"]+)"', main_page.text)
if csrf_match:
    csrf_token = csrf_match.group(1)

form_data = {
    'csrf_token': csrf_token,
    'target_language': 'en',
    'voice': 'en-US-AvaMultilingualNeural',
    'platform': 'YouTube',
    'genre': 'Soundtrack',
    'modify_kw': 'yes',
    'bypass': 'no',
    'video_title': 'Beautiful Nature Landscapes',
    'script': 'Nature is amazing. Mountains reach high. Rivers flow peacefully.',
    'base_dir': '/tmp/test_videos',
    'keywords': 'nature,landscape,mountains,rivers'
}

submit_response = session.post(f"{base_url}/", data=form_data)
print(f"Form submission status: {submit_response.status_code}")

# Check where we got redirected
if submit_response.history:
    print(f"Redirected through: {[r.url for r in submit_response.history]}")
print(f"Final URL: {submit_response.url}")

# Save the response
with open("authenticated_response.html", "w") as f:
    f.write(submit_response.text)
    print("Response saved to authenticated_response.html")

# Check if we're on the script page
if "/script" in submit_response.url:
    print("\nSuccessfully reached script generation page!")
    
    # Check for any generated content
    if "script-content" in submit_response.text or "textarea" in submit_response.text:
        print("Script generation form found")
