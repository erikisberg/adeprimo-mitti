#!/usr/bin/env python3
"""
Debug configuration loading
"""

import os
import json
from config import ConfigManager
from openai import OpenAI

print("=== Configuration Debug ===")

# Check environment
print("\n1. Environment variables:")
print(f"   OPENAI_API_KEY in env: {'OPENAI_API_KEY' in os.environ}")
if 'OPENAI_API_KEY' in os.environ:
    print(f"   Value: {os.environ['OPENAI_API_KEY'][:8]}...{os.environ['OPENAI_API_KEY'][-8:]}")

# Load config
print("\n2. ConfigManager loading:")
config_manager = ConfigManager()
api_key = config_manager.get("openai_api_key")
assistant_id = config_manager.get("openai_assistant_id")

print(f"   API Key from ConfigManager: {api_key[:8]}...{api_key[-8:]}")
print(f"   Assistant ID: {assistant_id}")

# Test OpenAI client
print("\n3. Testing OpenAI client initialization:")
try:
    client = OpenAI(api_key=api_key)
    print("   ✅ Client created successfully")
    
    # Test assistant access
    print("\n4. Testing assistant access:")
    assistant = client.beta.assistants.retrieve(assistant_id)
    print(f"   ✅ Assistant found: {assistant.name}")
    
    # Test creating and running a thread
    print("\n5. Testing thread creation and run:")
    thread = client.beta.threads.create()
    print(f"   ✅ Thread created: {thread.id}")
    
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content="Test"
    )
    print("   ✅ Message added")
    
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id
    )
    print(f"   ✅ Run created: {run.id}")
    
except Exception as e:
    print(f"   ❌ Error: {type(e).__name__}: {e}")
    if hasattr(e, 'response') and hasattr(e.response, 'json'):
        try:
            print(f"   Details: {e.response.json()}")
        except:
            pass

print("\n=== Summary ===")
print("If all tests pass here but fail in the app, check:")
print("1. How the analyzer is being initialized in monitor.py")
print("2. Whether config is being passed correctly")
print("3. Any environment variable overrides in the app flow")