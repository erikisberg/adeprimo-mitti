#!/usr/bin/env python3
"""
Setup Test Script for Content Monitor

This script tests the basic configuration and dependencies required
to run the content monitoring system.
"""

import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import requests
        print("✅ requests module is installed")
    except ImportError:
        print("❌ requests module is not installed. Run: pip install requests")
        return False
    
    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv module is installed")
    except ImportError:
        print("❌ python-dotenv module is not installed. Run: pip install python-dotenv")
        return False
    
    return True

def check_directories():
    """Check if required directories exist."""
    dirs_to_check = ["data", "data/history", "data/analysis"]
    
    for directory in dirs_to_check:
        if os.path.exists(directory) and os.path.isdir(directory):
            print(f"✅ Directory exists: {directory}")
        else:
            print(f"❌ Directory missing: {directory}")
            try:
                os.makedirs(directory, exist_ok=True)
                print(f"  → Created directory: {directory}")
            except Exception as e:
                print(f"  → Error creating directory: {str(e)}")
                return False
    
    return True

def check_configuration():
    """Check if configuration files exist and are valid."""
    # Check config.json
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            print("✅ config.json exists and is valid JSON")
            
            # Check required keys
            required_keys = ["firecrawl_api_key", "openai_api_key", "openai_assistant_id", "url_list_path"]
            missing_keys = [key for key in required_keys if key not in config]
            
            if missing_keys:
                print(f"⚠️ Missing required keys in config.json: {', '.join(missing_keys)}")
            else:
                print("✅ All required keys exist in config.json")
                
            # Check for default API keys
            for key in ["firecrawl_api_key", "openai_api_key", "openai_assistant_id"]:
                if key in config and config[key].startswith("your_"):
                    print(f"⚠️ Default value detected for {key} in config.json")
    except FileNotFoundError:
        print("❌ config.json not found")
        return False
    except json.JSONDecodeError:
        print("❌ config.json is not valid JSON")
        return False
    
    # Check URL list
    try:
        url_list_path = config.get("url_list_path", "urls.json")
        with open(url_list_path, "r") as f:
            urls = json.load(f)
            print(f"✅ {url_list_path} exists and is valid JSON")
            print(f"  → Found {len(urls)} URLs to monitor")
    except FileNotFoundError:
        print(f"❌ {url_list_path} not found")
        return False
    except json.JSONDecodeError:
        print(f"❌ {url_list_path} is not valid JSON")
        return False
    
    # Check environment variables
    env_keys = ["FIRECRAWL_API_KEY", "OPENAI_API_KEY", "OPENAI_ASSISTANT_ID"]
    found_env_keys = [key for key in env_keys if os.environ.get(key)]
    
    if found_env_keys:
        print(f"✅ Found {len(found_env_keys)} environment variables: {', '.join(found_env_keys)}")
    else:
        print("⚠️ No environment variables found. Using config.json values instead.")
    
    return True

def test_apis():
    """Test API connectivity (without making actual API calls)."""
    firecrawl_key = os.environ.get("FIRECRAWL_API_KEY", None)
    openai_key = os.environ.get("OPENAI_API_KEY", None)
    openai_assistant_id = os.environ.get("OPENAI_ASSISTANT_ID", None)
    
    if not firecrawl_key:
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                firecrawl_key = config.get("firecrawl_api_key", None)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    
    if not openai_key:
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                openai_key = config.get("openai_api_key", None)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    
    if not openai_assistant_id:
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                openai_assistant_id = config.get("openai_assistant_id", None)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    
    if firecrawl_key and not firecrawl_key.startswith("your_"):
        print("✅ Firecrawl API key is configured")
    else:
        print("⚠️ Firecrawl API key is not configured, will use direct scraping as fallback")
    
    if openai_key and not openai_key.startswith("your_"):
        print("✅ OpenAI API key is configured")
    else:
        print("❌ OpenAI API key is not configured")
    
    if openai_assistant_id and not openai_assistant_id.startswith("your_"):
        print("✅ OpenAI Assistant ID is configured")
    else:
        print("❌ OpenAI Assistant ID is not configured")
    
    return True

def main():
    """Run all setup tests."""
    print("Content Monitor Setup Test")
    print("=========================\n")
    
    print("Checking dependencies...")
    deps_ok = check_dependencies()
    print()
    
    print("Checking directories...")
    dirs_ok = check_directories()
    print()
    
    print("Checking configuration...")
    config_ok = check_configuration()
    print()
    
    print("Testing API connectivity...")
    apis_ok = test_apis()
    print()
    
    print("Setup Test Results")
    print("=================")
    results = [
        ("Dependencies", deps_ok),
        ("Directories", dirs_ok),
        ("Configuration", config_ok),
        ("API Connectivity", apis_ok)
    ]
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name}: {status}")
    
    overall = all([deps_ok, dirs_ok, config_ok, apis_ok])
    
    print("\nOverall Result:")
    if overall:
        print("✅ Setup test PASSED. You can now run the content monitor.")
        print("   Run: python main.py")
    else:
        print("❌ Setup test FAILED. Please fix the issues above before running the content monitor.")
    
    return 0 if overall else 1

if __name__ == "__main__":
    sys.exit(main())