#!/usr/bin/env python3
"""
Test script to debug syntax errors
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from utils import logger

def main():
    """Test main function."""
    # Debug: Check if API key is loaded
    firecrawl_key = os.environ.get("FIRECRAWL_API_KEY")
    if firecrawl_key:
        logger.info(f"Loaded Firecrawl API key from environment: {firecrawl_key[:10]}...")
    else:
        logger.warning("No Firecrawl API key found in environment variables")
    
    print("Test script completed successfully")

if __name__ == "__main__":
    main()