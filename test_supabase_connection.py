#!/usr/bin/env python3
"""
Test script to verify Supabase connection
Run this to test if your Supabase credentials work
"""

import os
import sys
from supabase import create_client, Client

def test_supabase_connection():
    """Test Supabase connection with credentials from environment or secrets file"""
    
    # Try to get credentials from environment variables first
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    # If not in environment, try to read from .streamlit/secrets.toml
    if not supabase_url or not supabase_key:
        try:
            import toml
            secrets_path = ".streamlit/secrets.toml"
            if os.path.exists(secrets_path):
                secrets = toml.load(secrets_path)
                supabase_url = secrets.get("SUPABASE_URL")
                supabase_key = secrets.get("SUPABASE_KEY")
                print(f"✅ Loaded credentials from {secrets_path}")
            else:
                print(f"❌ Secrets file not found: {secrets_path}")
                return False
        except ImportError:
            print("❌ toml package not installed. Install with: pip install toml")
            return False
        except Exception as e:
            print(f"❌ Error reading secrets file: {e}")
            return False
    
    if not supabase_url or not supabase_key:
        print("❌ Supabase credentials not found")
        print("Set SUPABASE_URL and SUPABASE_KEY environment variables or check .streamlit/secrets.toml")
        return False
    
    print(f"🔗 Testing connection to: {supabase_url}")
    
    try:
        # Create client
        client = create_client(supabase_url, supabase_key)
        print("✅ Supabase client created successfully")
        
        # Test connection with a simple query
        try:
            response = client.table("monitored_urls").select("count", count="exact").limit(1).execute()
            print("✅ Connection test successful!")
            print(f"📊 Database accessible, table 'monitored_urls' exists")
            
            # Try to get actual data
            try:
                urls_response = client.table("monitored_urls").select("*").limit(5).execute()
                print(f"📋 Found {len(urls_response.data)} URLs in database")
                if urls_response.data:
                    print("Sample URLs:")
                    for url in urls_response.data[:3]:
                        print(f"  - {url.get('name', 'Unknown')}: {url.get('url', 'No URL')}")
            except Exception as data_error:
                print(f"⚠️ Could not fetch data: {data_error}")
            
            return True
            
        except Exception as connection_error:
            print(f"❌ Connection test failed: {connection_error}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating Supabase client: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Supabase Connection")
    print("=" * 40)
    
    success = test_supabase_connection()
    
    print("=" * 40)
    if success:
        print("🎉 All tests passed! Supabase connection is working.")
    else:
        print("💥 Tests failed. Check your credentials and network connection.")
        print("\nTroubleshooting tips:")
        print("1. Verify your Supabase URL and key are correct")
        print("2. Check if your Supabase project is active")
        print("3. Ensure your IP is not blocked by Supabase")
        print("4. Try accessing Supabase dashboard in your browser")
        print("5. Check if there are any network restrictions")
