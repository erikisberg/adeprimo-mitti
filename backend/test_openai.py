#!/usr/bin/env python3
"""
Test script for OpenAI Assistant API integration.
This simple script tests that the OpenAI API key and Assistant ID are working correctly.
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

def test_openai_integration():
    """Test the OpenAI Assistant API integration."""
    print("Testing OpenAI Assistant API integration...")
    
    # Get credentials from environment
    api_key = os.environ.get("OPENAI_API_KEY")
    assistant_id = os.environ.get("OPENAI_ASSISTANT_ID")
    
    if not api_key:
        print("❌ No OpenAI API key found in .env file")
        return False
    
    if not assistant_id:
        print("❌ No OpenAI Assistant ID found in .env file")
        return False
    
    print(f"Using API key starting with: {api_key[:8]}...")
    print(f"Using Assistant ID: {assistant_id}")
    
    # Set up headers
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "OpenAI-Beta": "assistants=v2"  # Using v2 of the Assistants API
    }
    
    try:
        # Step 1: Create a thread
        print("\n1. Creating a thread...")
        thread_response = requests.post(
            "https://api.openai.com/v1/threads",
            headers=headers,
            json={}
        )
        thread_response.raise_for_status()
        thread_id = thread_response.json().get("id")
        print(f"   ✅ Thread created with ID: {thread_id}")
        
        # Step 2: Add a message to the thread
        print("\n2. Adding a test message to the thread...")
        test_message = "Please analyze the following and rate it on a scale of 1-5: This is a test message to verify the OpenAI Assistant integration is working correctly."
        
        message_response = requests.post(
            f"https://api.openai.com/v1/threads/{thread_id}/messages",
            headers=headers,
            json={
                "role": "user",
                "content": test_message
            }
        )
        message_response.raise_for_status()
        message_id = message_response.json().get("id")
        print(f"   ✅ Message added with ID: {message_id}")
        
        # Step 3: Run the assistant
        print("\n3. Running the assistant on the thread...")
        run_response = requests.post(
            f"https://api.openai.com/v1/threads/{thread_id}/runs",
            headers=headers,
            json={"assistant_id": assistant_id}
        )
        run_response.raise_for_status()
        run_id = run_response.json().get("id")
        print(f"   ✅ Run created with ID: {run_id}")
        
        # Step 4: Poll for completion
        print("\n4. Polling for completion...")
        status = "queued"
        poll_count = 0
        max_polls = 30
        
        while status in ["queued", "in_progress"] and poll_count < max_polls:
            poll_count += 1
            print(f"   Polling attempt {poll_count}/{max_polls}...")
            time.sleep(2)
            
            run_status_response = requests.get(
                f"https://api.openai.com/v1/threads/{thread_id}/runs/{run_id}",
                headers=headers
            )
            run_status_response.raise_for_status()
            status_data = run_status_response.json()
            status = status_data.get("status")
            
            print(f"   Current status: {status}")
            
            if status not in ["queued", "in_progress"]:
                break
        
        if status == "completed":
            print("   ✅ Assistant run completed successfully!")
        else:
            print(f"   ❌ Assistant run did not complete. Final status: {status}")
            return False
        
        # Step 5: Get messages
        print("\n5. Retrieving the assistant's response...")
        messages_response = requests.get(
            f"https://api.openai.com/v1/threads/{thread_id}/messages",
            headers=headers
        )
        messages_response.raise_for_status()
        messages = messages_response.json().get("data", [])
        
        # Find the assistant's response (most recent first)
        assistant_message = None
        for message in messages:
            if message.get("role") == "assistant":
                assistant_message = message
                break
        
        if assistant_message:
            content = assistant_message.get("content", [])
            if content and isinstance(content, list):
                for item in content:
                    if item.get("type") == "text":
                        text = item.get("text", {})
                        if isinstance(text, dict) and "value" in text:
                            print(f"\nAssistant response: {text['value']}")
                        else:
                            print(f"\nAssistant response: {text}")
                        return True
        
        print("   ❌ Could not find assistant response")
        return False
        
    except requests.RequestException as e:
        print(f"❌ Error communicating with OpenAI API: {str(e)}")
        
        # Try to extract more detailed error information
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                if 'error' in error_detail:
                    print(f"Error details: {error_detail['error']}")
            except:
                pass
        
        return False

if __name__ == "__main__":
    success = test_openai_integration()
    
    if success:
        print("\n✅ OpenAI integration test PASSED! The system is correctly configured.")
        sys.exit(0)
    else:
        print("\n❌ OpenAI integration test FAILED. Please check your credentials and Assistant ID.")
        sys.exit(1)