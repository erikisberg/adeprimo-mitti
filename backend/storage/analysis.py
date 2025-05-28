"""
Analysis storage functionality for Mitti Scraper
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, List

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import logger

class AnalysisStorage:
    """Stores and retrieves content analysis results."""
    
    def __init__(self, storage_dir: str = "data/analysis"):
        """Initialize with storage directory."""
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
        
    def _get_filename(self, url: str) -> str:
        """Generate a filename from a URL."""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return os.path.join(self.storage_dir, f"{url_hash}.json")
        
    def store_analysis(self, url: str, content: Dict, analysis: Dict) -> None:
        """Store analysis results for a URL."""
        filename = self._get_filename(url)
        try:
            data = {
                "url": url,
                "content": content.get("content", "")[:500],  # Store a preview
                "analysis": analysis,
                "stored_at": datetime.now().isoformat()
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.info(f"Analysis stored for {url}")
        except Exception as e:
            logger.error(f"Error storing analysis for {url}: {str(e)}")
            
    def get_analysis_history(self, url: str) -> List[Dict]:
        """Get analysis history for a URL."""
        filename = self._get_filename(url)
        try:
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"Error retrieving analysis history for {url}: {str(e)}")
            return []