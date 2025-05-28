#!/usr/bin/env python3
"""
Test script to verify OpenAI Assistant configuration
"""

import os
import json
import requests

# First unset the environment variable to use config.json
if "OPENAI_API_KEY" in os.environ:
    del os.environ["OPENAI_API_KEY"]

# Load configuration
with open("config.json", "r") as f:
    config = json.load(f)

api_key = config["openai_api_key"]
assistant_id = config["openai_assistant_id"]

print(f"Testing OpenAI Assistant Configuration")
print(f"=====================================")
print(f"API Key: {api_key[:8]}...{api_key[-8:]}")
print(f"Assistant ID: {assistant_id}")

# Test 1: Verify API key is valid
print("\n1. Testing API key validity...")
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

response = requests.get(
    "https://api.openai.com/v1/models",
    headers=headers
)

if response.status_code == 200:
    print("   ✅ API key is valid")
else:
    print(f"   ❌ API key error: {response.status_code} - {response.text}")
    exit(1)

# Test 2: Check if assistant exists
print("\n2. Checking if assistant exists...")
headers["OpenAI-Beta"] = "assistants=v2"

response = requests.get(
    f"https://api.openai.com/v1/assistants/{assistant_id}",
    headers=headers
)

if response.status_code == 200:
    assistant_data = response.json()
    print(f"   ✅ Assistant found: {assistant_data.get('name', 'Unnamed')}")
    print(f"   Model: {assistant_data.get('model', 'Unknown')}")
    print(f"   Created: {assistant_data.get('created_at', 'Unknown')}")
else:
    print(f"   ❌ Assistant error: {response.status_code}")
    error_data = response.json()
    print(f"   Error message: {error_data.get('error', {}).get('message', 'Unknown error')}")
    
    # Provide guidance
    print("\n   Possible solutions:")
    print("   1. The assistant ID might be incorrect")
    print("   2. The assistant might have been deleted")
    print("   3. The assistant might belong to a different OpenAI account/organization")
    print("\n   To fix:")
    print("   1. Go to https://platform.openai.com/assistants")
    print("   2. Create a new assistant or find your existing one")
    print("   3. Copy the assistant ID (starts with 'asst_')")
    print("   4. Update the 'openai_assistant_id' in config.json")

# Test 3: List available assistants
print("\n3. Listing your available assistants...")
response = requests.get(
    "https://api.openai.com/v1/assistants",
    headers=headers
)

if response.status_code == 200:
    assistants = response.json().get("data", [])
    if assistants:
        print(f"   Found {len(assistants)} assistant(s):")
        for asst in assistants:
            print(f"   - {asst['id']}: {asst.get('name', 'Unnamed')} (Model: {asst.get('model', 'Unknown')})")
    else:
        print("   No assistants found. You need to create one at https://platform.openai.com/assistants")
else:
    print(f"   ❌ Error listing assistants: {response.status_code}")