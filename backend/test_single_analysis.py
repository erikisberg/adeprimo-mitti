#!/usr/bin/env python3
"""
Test script to verify OpenAI analysis with a single sample content
instead of running the full scraper on all URLs.
"""

import json
import os
from datetime import datetime
from utils import logger
from analysis import OpenAIAnalyzer

def test_single_analysis():
    """Test the OpenAI analysis with a single piece of sample content."""
    print("Testing OpenAI content analysis with a single sample...")
    
    # Load credentials from config.json
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ config.json not found")
        return False
    
    api_key = config.get("openai_api_key")
    assistant_id = config.get("openai_assistant_id")
    
    if not api_key or api_key.startswith("your_"):
        print("❌ No valid OpenAI API key found in config.json")
        return False
    
    if not assistant_id or assistant_id.startswith("your_"):
        print("❌ No valid OpenAI Assistant ID found in config.json")
        return False
    
    print(f"Using API key starting with: {api_key[:8]}...")
    print(f"Using Assistant ID: {assistant_id}")
    
    # Initialize the analyzer
    analyzer = OpenAIAnalyzer(api_key, assistant_id)
    
    # Create a sample content dictionary (similar to what would come from the scraper)
    sample_content = {
        "url": "https://example.com/test",
        "content": "This is a sample content for testing the OpenAI analysis functionality.",
        "extracted_news": [
            {
                "title": "New community center opening in Sollentuna",
                "date": "2025-05-25",
                "content": "A new community center is opening in Sollentuna next month, offering various activities for residents."
            },
            {
                "title": "Road construction on Main Street",
                "date": "2025-05-26",
                "content": "Road construction will begin on Main Street next week and is expected to last for two months."
            }
        ]
    }
    
    # Sample changes text
    changes = "Added information about the new community center and road construction."
    
    try:
        print("\nSending sample content to OpenAI for analysis...")
        result = analyzer.analyze_content(sample_content["url"], sample_content, changes)
        
        print("\n=== Analysis Result ===")
        print(f"Status: {'Success' if 'analysis' in result else 'Failed'}")
        
        if 'analysis' in result:
            print(f"\nAnalysis: {result['analysis']}")
            
            if 'rating' in result:
                print(f"\nRating: {result['rating']}")
                
            print(f"\nTimestamp: {result['timestamp']}")
            
            if 'extracted_news' in result and result['extracted_news']:
                print("\nExtracted News Items:")
                for item in result['extracted_news']:
                    print(f"- {item['title']}")
                    if 'rating' in item:
                        print(f"  Rating: {item['rating']}")
            
            return True
        else:
            print("❌ Analysis failed, no analysis in result")
            return False
            
    except Exception as e:
        print(f"❌ Error analyzing content: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_single_analysis()
    
    if success:
        print("\n✅ OpenAI analysis test PASSED!")
    else:
        print("\n❌ OpenAI analysis test FAILED. Please check the error messages above.") 