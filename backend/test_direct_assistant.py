#!/usr/bin/env python3
"""
Test using the assistant directly without going through the analyzer class
"""

import os
import json
import time
from openai import OpenAI

# Ensure we're using config.json
if "OPENAI_API_KEY" in os.environ:
    del os.environ["OPENAI_API_KEY"]

# Load configuration
with open("config.json", "r") as f:
    config = json.load(f)

# Initialize OpenAI client
client = OpenAI(api_key=config["openai_api_key"])
assistant_id = config["openai_assistant_id"]

print("Testing OpenAI Assistant with official SDK")
print("=" * 50)

try:
    # Step 1: Verify assistant exists
    print("\n1. Verifying assistant...")
    assistant = client.beta.assistants.retrieve(assistant_id)
    print(f"   ✅ Assistant found: {assistant.name}")
    
    # Step 2: Create a thread
    print("\n2. Creating thread...")
    thread = client.beta.threads.create()
    print(f"   ✅ Thread created: {thread.id}")
    
    # Step 3: Add a message
    print("\n3. Adding message...")
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content="Test message: Betygsätt detta innehåll: 'Sollentuna kommun öppnar ny lekplats i centrum.' Ge betyg 1-5."
    )
    print(f"   ✅ Message added")
    
    # Step 4: Run the assistant
    print("\n4. Running assistant...")
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id
    )
    print(f"   ✅ Run created: {run.id}")
    
    # Step 5: Wait for completion
    print("\n5. Waiting for completion...")
    while run.status in ["queued", "in_progress"]:
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
        print(f"   Status: {run.status}")
    
    if run.status == "completed":
        print("   ✅ Run completed!")
        
        # Get the response
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        for msg in messages.data:
            if msg.role == "assistant":
                print(f"\n6. Assistant response:")
                print(f"   {msg.content[0].text.value}")
                break
    else:
        print(f"   ❌ Run failed with status: {run.status}")
        if hasattr(run, 'last_error'):
            print(f"   Error: {run.last_error}")
            
except Exception as e:
    print(f"\n❌ Error: {type(e).__name__}: {e}")
    
    # If it's an API error, try to get more details
    if hasattr(e, 'response'):
        print(f"   Response status: {e.response.status_code}")
        print(f"   Response body: {e.response.text}")

print("\n" + "=" * 50)
print("If this test succeeds but the main app fails, the issue is in the analyzer implementation.")
print("If this test also fails, there's an API/configuration issue.")