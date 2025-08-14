#!/usr/bin/env python3
"""
Test script to verify fallback scraping works when Firecrawl fails
"""

import sys
import os
sys.path.append('backend')

from scraper import ContentScraper
from utils import logger

def test_fallback_scraping():
    """Test the fallback scraping functionality"""
    
    print("🧪 Testing Fallback Scraping")
    print("=" * 50)
    
    # Test with a valid Firecrawl key that will fail due to payment
    test_config = {
        "scraping": {
            "max_content_length": 50000
        }
    }
    
    # Create scraper with a dummy key that will fail
    scraper = ContentScraper("dummy_key_that_will_fail", test_config)
    
    # Test URLs
    test_urls = [
        "https://www.sollentuna.se/",
        "https://www.skab.se/nyheter"
    ]
    
    for url in test_urls:
        print(f"\n🔗 Testing URL: {url}")
        print("-" * 40)
        
        try:
            result = scraper.scrape_url(url)
            
            if result.get("error"):
                print(f"❌ Error: {result['error']}")
            else:
                print(f"✅ Success!")
                print(f"   Title: {result.get('title', 'No title')}")
                print(f"   Content length: {len(result.get('content', ''))}")
                print(f"   News items: {len(result.get('extracted_news', []))}")
                
                # Show first news item if available
                news_items = result.get('extracted_news', [])
                if news_items:
                    first_item = news_items[0]
                    print(f"   First news: {first_item.get('title', 'No title')}")
                
                # Show content preview
                content = result.get('content', '')
                if content:
                    preview = content[:200] + "..." if len(content) > 200 else content
                    print(f"   Content preview: {preview}")
            
        except Exception as e:
            print(f"💥 Exception: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎯 Test completed!")
    
    # Show scraper status
    if scraper.use_firecrawl:
        print("🔗 Firecrawl is still enabled")
    else:
        print("⚠️ Firecrawl has been disabled (fallback mode)")

if __name__ == "__main__":
    test_fallback_scraping()
