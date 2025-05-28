#!/usr/bin/env python3
"""
Test OpenAI organization context issue
"""

import os
import json
import requests

# Ensure we're using config.json
if "OPENAI_API_KEY" in os.environ:
    del os.environ["OPENAI_API_KEY"]

# Load configuration
from config import ConfigManager
config_manager = ConfigManager()
api_key = config_manager.get("openai_api_key")
assistant_id = config_manager.get("openai_assistant_id")

print(f"Testing OpenAI Organization Context")
print(f"===================================")

# Test with exact same headers as the analyzer
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "OpenAI-Beta": "assistants=v2"
}

print("\n1. Testing thread creation (like the analyzer does)...")
thread_response = requests.post(
    "https://api.openai.com/v1/threads",
    headers=headers,
    json={}
)

if thread_response.status_code == 200:
    thread_id = thread_response.json().get("id")
    print(f"   ✅ Thread created: {thread_id}")
    
    # Now try to run the assistant
    print("\n2. Testing assistant run...")
    run_response = requests.post(
        f"https://api.openai.com/v1/threads/{thread_id}/runs",
        headers=headers,
        json={"assistant_id": assistant_id}
    )
    
    if run_response.status_code == 200:
        print(f"   ✅ Assistant run started successfully")
    else:
        print(f"   ❌ Assistant run error: {run_response.status_code}")
        error_data = run_response.json()
        print(f"   Error: {error_data}")
        
        # Check if it's an organization issue
        if "organization" in str(error_data).lower():
            print("\n   This might be an organization/project mismatch issue.")
            print("   The assistant might belong to a different organization than your API key.")
        
else:
    print(f"   ❌ Thread creation error: {thread_response.status_code}")
    print(f"   Error: {thread_response.json()}")

# Check API key details
print("\n3. Checking API key organization...")
# Try to get organization info
org_response = requests.get(
    "https://api.openai.com/v1/organization",
    headers={"Authorization": f"Bearer {api_key}"}
)

if org_response.status_code == 200:
    org_data = org_response.json()
    print(f"   Organization: {org_data}")
else:
    # Alternative: check via models endpoint which includes org info
    models_response = requests.get(
        "https://api.openai.com/v1/models",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    if models_response.status_code == 200:
        print("   ✅ API key is valid and working")
    else:
        print("   ❌ API key might have issues")