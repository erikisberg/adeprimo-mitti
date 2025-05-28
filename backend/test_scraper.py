#!/usr/bin/env python3
"""
Test script for ContentScraper functionality.
This script tests both Firecrawl API scraping and direct scraping.
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv
from typing import Dict, Any

# Load environment variables
load_dotenv()

# Import the scraper module
from scraper import ContentScraper

def test_scraper(url: str, use_firecrawl: bool = True) -> Dict[str, Any]:
    """
    Test scraping a URL using either Firecrawl or direct scraping.
    
    Args:
        url: The URL to scrape
        use_firecrawl: Whether to use Firecrawl API (if available)
        
    Returns:
        Dictionary containing scraped content
    """
    print(f"\nTesting scraper on URL: {url}")
    
    # Initialize the scraper
    api_key = os.environ.get("FIRECRAWL_API_KEY") if use_firecrawl else None
    if use_firecrawl and not api_key:
        print("Warning: No FIRECRAWL_API_KEY found in environment variables")
    elif use_firecrawl:
        print(f"Found Firecrawl API key: {api_key[:10]}...")
    
    # Load config from file
    config = {}
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("Warning: Could not load config.json, using defaults")
    
    # Initialize the scraper
    scraper = ContentScraper(api_key, config)
    
    # Print status
    if scraper.use_firecrawl:
        print(f"Using Firecrawl API with key: {api_key[:8]}...")
    else:
        print("Using direct scraping (no Firecrawl API key provided)")
    
    # Scrape the URL
    try:
        print(f"Scraping URL: {url}")
        
        # Try Firecrawl first if configured
        if scraper.use_firecrawl:
            print("=== TESTING FIRECRAWL API DIRECTLY ===")
            
            try:
                print("Calling scraper._scrape_with_firecrawl() method...")
                firecrawl_result = scraper._scrape_with_firecrawl(url)
                if firecrawl_result:
                    print("Firecrawl API scraping successful")
                    print(f"Title: {firecrawl_result.get('title', 'No title')}")
                    print(f"Content length: {len(firecrawl_result.get('content', ''))}")
                    print(f"HTML length: {len(firecrawl_result.get('html', ''))}")
                    
                    if "extracted_news" in firecrawl_result and firecrawl_result["extracted_news"]:
                        news_items = firecrawl_result["extracted_news"]
                        print(f"Extracted {len(news_items)} news items directly from Firecrawl")
                        for i, item in enumerate(news_items[:3], 1):
                            print(f"  {i}. {item.get('title', 'No title')}")
                else:
                    print("Firecrawl API returned None, will fall back to direct scraping")
            except Exception as e:
                import traceback
                print(f"Firecrawl API error: {str(e)}")
                print(traceback.format_exc())
        
        print("\n=== TESTING FULL SCRAPE_URL METHOD ===")
        print("This calls scrape_url() which uses the Firecrawl extract API")
        # Now try the regular scrape_url method which handles fallbacks
        result = scraper.scrape_url(url)
        
        # Print results summary
        if "error" in result:
            print(f"Error: {result['error']}")
            return result
        
        print(f"Successfully scraped {url}")
        print(f"Title: {result.get('title', 'No title')}")
        print(f"Content length: {len(result.get('content', ''))}")
        print(f"HTML length: {len(result.get('html', ''))}")
        
        # If there are extracted news items, print them
        if "extracted_news" in result and result["extracted_news"]:
            news_items = result["extracted_news"]
            print(f"\nExtracted {len(news_items)} news items:")
            for i, item in enumerate(news_items[:5], 1):  # Show max 5 items
                print(f"  {i}. {item.get('title', 'No title')}")
                if i == 5 and len(news_items) > 5:
                    print(f"  ... and {len(news_items) - 5} more")
        
        return result
    except Exception as e:
        print(f"Error scraping URL: {str(e)}")
        return {"error": str(e)}

# NOTE: Batch scraping functionality has been removed to ensure
# each URL gets its own unique news items.

# def test_batch_scraping(urls: list) -> Dict[str, Dict]:
#     """
#     Test batch scraping multiple URLs using Firecrawl API.
#     
#     Args:
#         urls: List of URLs to scrape
#         
#     Returns:
#         Dictionary mapping URLs to their scraped content
#     """
#     print(f"\nTesting batch scraping on {len(urls)} URLs")
#     
#     # Initialize the scraper
#     api_key = os.environ.get("FIRECRAWL_API_KEY")
#     
#     # Load config from file
#     config = {}
#     try:
#         with open("config.json", "r") as f:
#             config = json.load(f)
#     except (FileNotFoundError, json.JSONDecodeError):
#         print("Warning: Could not load config.json, using defaults")
#     
#     # Initialize the scraper
#     scraper = ContentScraper(api_key, config)
#     
#     # Check if Firecrawl API is available
#     if not scraper.use_firecrawl:
#         print("Firecrawl API key not provided, cannot test batch scraping")
#         return {}
#     
#     # Batch scrape the URLs
#     try:
#         print(f"Batch scraping {len(urls)} URLs...")
#         # This method no longer exists
#         results = {}
#         
#         # Process each URL individually instead
#         for url in urls:
#             print(f"Scraping {url} individually...")
#             results[url] = scraper.scrape_url(url)
#         
#         # Print results summary
#         success_count = sum(1 for url, result in results.items() if "error" not in result)
#         print(f"Successfully scraped {success_count}/{len(urls)} URLs")
#         
#         for url, result in results.items():
#             if "error" in result:
#                 print(f"Error scraping {url}: {result['error']}")
#             else:
#                 print(f"Successfully scraped {url}")
#                 print(f"  Title: {result.get('title', 'No title')[:50]}...")
#                 print(f"  Content length: {len(result.get('content', ''))}")
#         
#         return results
#     except Exception as e:
#         print(f"Error in batch scraping: {str(e)}")
#         return {}

def main():
    """Main function to run tests."""
    print("Content Scraper Test")
    print("===================\n")
    
    # Get URL from command line arguments or use default
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        # Use a default URL
        print("No URL provided")
        return
    
    # Get scraping method from command line arguments
    use_firecrawl = True
    if len(sys.argv) > 2 and sys.argv[2].lower() == "direct":
        use_firecrawl = False
    
    # Test individual scraping
    result = test_scraper(url, use_firecrawl)
    
    # NOTE: Batch scraping has been removed to ensure each URL gets its own unique news items
    # # If we're using Firecrawl, also test batch scraping with a few URLs
    # if use_firecrawl and "error" not in result:
    #     test_urls = [
    #         url
    #     ]
    #     batch_results = test_batch_scraping(test_urls)
    
    print("\nTest completed")

if __name__ == "__main__":
    main()