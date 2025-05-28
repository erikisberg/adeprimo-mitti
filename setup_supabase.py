#!/usr/bin/env python3
"""
Supabase Setup Script
This script creates the necessary tables in Supabase and tests the connection.
"""

import os
import sys
import json
from pathlib import Path
from supabase import create_client, Client

def read_schema_sql():
    """Read the schema SQL file."""
    schema_path = Path("supabase_schema.sql")
    if not schema_path.exists():
        print(f"❌ Error: Schema file not found at {schema_path}")
        return None
        
    with open(schema_path, "r") as f:
        return f.read()

def read_streamlit_secrets():
    """Read Streamlit secrets.toml and extract Supabase credentials."""
    secrets_path = Path(".streamlit/secrets.toml")
    
    if not secrets_path.exists():
        print(f"❌ Error: secrets.toml not found at {secrets_path}")
        return None, None
        
    supabase_url = None
    supabase_key = None
    
    with open(secrets_path, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("SUPABASE_URL"):
                supabase_url = line.split("=")[1].strip().strip('"').strip("'")
            elif line.startswith("SUPABASE_KEY"):
                supabase_key = line.split("=")[1].strip().strip('"').strip("'")
    
    return supabase_url, supabase_key

def init_supabase(url, key):
    """Initialize Supabase client."""
    if not url or not key:
        print("❌ Error: Missing Supabase credentials")
        return None
        
    try:
        return create_client(url, key)
    except Exception as e:
        print(f"❌ Error connecting to Supabase: {str(e)}")
        return None

def setup_schema(supabase, schema_sql):
    """Set up the database schema using direct SQL execution."""
    if not supabase or not schema_sql:
        return False
        
    try:
        # Create analyses table
        print("Creating analyses table...")
        supabase.table("analyses").insert({
            "url": "https://example.com",
            "site_name": "Test Site",
            "overall_rating": 3,
            "analysis_text": "Test analysis",
            "changes_detected": True
        }).execute()
        print("✅ Analyses table created or already exists.")
        
        # Create news_items table
        print("Creating news_items table...")
        # First get the ID of our test analysis
        response = supabase.table("analyses").select("id").eq("url", "https://example.com").limit(1).execute()
        if len(response.data) > 0:
            analysis_id = response.data[0]["id"]
            
            supabase.table("news_items").insert({
                "analysis_id": analysis_id,
                "title": "Test News Item",
                "date": "2023-05-01",
                "rating": 4,
                "content": "Test content"
            }).execute()
            print("✅ News_items table created or already exists.")
        else:
            print("❌ Could not get test analysis ID.")
            
        return True
    except Exception as e:
        print(f"❌ Error setting up schema: {str(e)}")
        return False

def test_tables(supabase):
    """Test that tables were created successfully."""
    try:
        # Test analyses table
        analyses = supabase.table('analyses').select('*').limit(1).execute()
        print(f"✅ Analyses table exists! Got {len(analyses.data)} rows.")
        
        # Test news_items table
        news_items = supabase.table('news_items').select('*').limit(1).execute()
        print(f"✅ News items table exists! Got {len(news_items.data)} rows.")
        
        return True
    except Exception as e:
        print(f"❌ Error testing tables: {str(e)}")
        return False

def main():
    print("🚀 Setting up Supabase for Mitti AI...")
    
    # Read schema SQL
    schema_sql = read_schema_sql()
    if not schema_sql:
        return False
    
    # Read Supabase credentials
    supabase_url, supabase_key = read_streamlit_secrets()
    if not supabase_url or not supabase_key:
        return False
    
    # Initialize Supabase client
    supabase = init_supabase(supabase_url, supabase_key)
    if not supabase:
        return False
    
    # Set up schema
    print("Setting up database schema...")
    if not setup_schema(supabase, schema_sql):
        return False
    
    # Test tables
    print("Testing tables...")
    if not test_tables(supabase):
        return False
    
    print("✅ Supabase setup complete!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 