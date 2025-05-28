"""
URL management for Mitti Scraper
"""

import json
from typing import List, Dict

from utils import logger

class URLManager:
    """Manages URL lists for monitoring."""
    
    def __init__(self, url_list_path: str):
        """Initialize with URL list file path."""
        self.url_list_path = url_list_path
        self.urls = self._load_urls()
        
    def _load_urls(self) -> List[Dict]:
        """Load URLs from file."""
        try:
            with open(self.url_list_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"URL list file not found: {self.url_list_path}")
            raise
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in URL list file: {self.url_list_path}")
            raise
            
    def get_urls(self) -> List[Dict]:
        """Get the list of URLs to monitor."""
        return self.urls