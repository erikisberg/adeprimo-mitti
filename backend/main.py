#!/usr/bin/env python3
"""
Content Monitor - Main Script

This script monitors web content from a list of URLs, detects changes,
and uses OpenAI to analyze the importance of those changes.
"""

import re
import os
import traceback
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from monitor import ContentMonitor
from utils import logger

def main():
    """Main entry point for the script."""
    try:
        # Debug: Check if API key is loaded
        firecrawl_key = os.environ.get("FIRECRAWL_API_KEY")
        if firecrawl_key:
            logger.info(f"Loaded Firecrawl API key from environment: {firecrawl_key[:10]}...")
        else:
            logger.warning("No Firecrawl API key found in environment variables")
            
        monitor = ContentMonitor()
        results = monitor.run()
        
        # Print summary
        print("\nSammanfattning av övervakningsresultat:")
        print("-" * 50)
        
        for result in results:
            status = result.get("status", "unknown")
            name = result.get("name", result.get("url", "unknown"))
            
            if status == "success":
                if result.get("changes_detected"):
                    if result.get("analyzed"):
                        # Safely get analysis text, handling both string and dict formats
                        analysis_data = result.get("analysis", {})
                        if isinstance(analysis_data, dict):
                            analysis_text = analysis_data.get("analysis", "Ingen analys")
                        else:
                            analysis_text = str(analysis_data)
                            
                        # Get rating if available directly in the analysis data
                        rating = None
                        if isinstance(analysis_data, dict) and "rating" in analysis_data:
                            rating = analysis_data.get("rating")
                        # Otherwise try to extract from text
                        elif isinstance(analysis_text, str):
                            rating_match = re.search(r"(?:Betyg|Rating):?\s*(\d)", analysis_text)
                            if rating_match:
                                rating = rating_match.group(1)
                        
                        rating_str = f"[Betyg: {rating}] " if rating else ""
                        print(f"✅ {name}: Ändringar upptäckta och analyserade {rating_str}")
                        
                        # Truncate and format the analysis text
                        if analysis_text and len(analysis_text) > 100:
                            # Try to find a clean break point
                            break_point = analysis_text[:100].rfind(". ")
                            if break_point > 50:
                                print(f"   Analys: {analysis_text[:break_point+1]}...")
                            else:
                                print(f"   Analys: {analysis_text[:100]}...")
                        else:
                            print(f"   Analys: {analysis_text}")
                    else:
                        print(f"⚠️ {name}: Ändringar upptäckta men inte analyserade")
                else:
                    print(f"ℹ️ {name}: Inga betydande förändringar")
            else:
                print(f"❌ {name}: Fel - {result.get('error', 'Okänt fel')}")
            
            print("-" * 50)
            
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        print(f"Error: {str(e)}")
        # Print stack trace for troubleshooting
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()