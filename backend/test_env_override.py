#!/usr/bin/env python3
"""
Test script to demonstrate environment variable override issue
"""

import os
import json

# Show current environment variable
print("1. Current OPENAI_API_KEY environment variable:")
env_key = os.environ.get("OPENAI_API_KEY", "Not set")
print(f"   First/Last 8 chars: {env_key[:8]}...{env_key[-8:]}")

# Show config.json value
print("\n2. Value in config.json:")
with open("config.json", "r") as f:
    config = json.load(f)
    config_key = config.get("openai_api_key", "Not set")
    print(f"   First/Last 8 chars: {config_key[:8]}...{config_key[-8:]}")

# Show what ConfigManager will use
print("\n3. What ConfigManager will use:")
from config import ConfigManager
config_manager = ConfigManager()
final_key = config_manager.get("openai_api_key", "Not set")
print(f"   First/Last 8 chars: {final_key[:8]}...{final_key[-8:]}")

print("\n4. Solution:")
print("   To fix this, unset the environment variable:")
print("   $ unset OPENAI_API_KEY")
print("   Then run your app again.")
print("\n   Or, update the environment variable to match config.json:")
print("   $ export OPENAI_API_KEY='<your-correct-key-from-config.json>'")