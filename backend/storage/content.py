"""
Content storage functionality for Mitti Scraper
"""

import os
import json
import hashlib
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import logger

class ContentStorage:
    """Handles storage and retrieval of scraped content."""
    
    def __init__(self, storage_dir: str = "data/history"):
        """Initialize with storage directory."""
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
        
    def _get_filename(self, url: str) -> str:
        """Generate a filename from a URL."""
        # Create a unique but readable filename from the URL
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return os.path.join(self.storage_dir, f"{url_hash}.json")
        
    def store_content(self, url: str, content: Dict) -> None:
        """Store content for a URL."""
        filename = self._get_filename(url)
        try:
            # Add timestamp to the content
            content["stored_at"] = datetime.now().isoformat()
            
            # Use the extracted news items if available, otherwise extract them manually
            if "extracted_news" in content and content["extracted_news"]:
                # Keep extracted_news as the single source of news items
                # Add first_seen timestamp to each item if not already present
                for item in content["extracted_news"]:
                    if "first_seen" not in item:
                        item["first_seen"] = datetime.now().isoformat()
                    if "url" not in item:
                        item["url"] = url  # Use main URL as we don't have individual URLs
            elif "content" in content:
                # Fallback to regex extraction if no extracted news
                content["extracted_news"] = self._extract_news_items(content["content"])
            
            # If we already have a file, merge the extracted_news lists
            if os.path.exists(filename):
                try:
                    with open(filename, 'r') as f:
                        previous_content = json.load(f)
                        
                        # Handle both news_items and extracted_news for backward compatibility
                        previous_news_items = []
                        if "extracted_news" in previous_content:
                            previous_news_items = previous_content.get("extracted_news", [])
                        elif "news_items" in previous_content:
                            # Convert old news_items format to extracted_news format
                            previous_news_items = previous_content.get("news_items", [])
                            
                        # Keep track of existing items to avoid duplicates
                        existing_items = {item.get("title", ""): item for item in previous_news_items}
                            
                        # Add new items that aren't in the existing items
                        for item in content.get("extracted_news", []):
                            if item.get("title", "") not in existing_items:
                                existing_items[item.get("title", "")] = item
                            
                        # Update the content with the merged items
                        content["extracted_news"] = list(existing_items.values())
                        
                        # Remove old news_items field if it exists
                        if "news_items" in content:
                            del content["news_items"]
                except Exception as e:
                    logger.error(f"Error merging news items for {url}: {str(e)}")
            
            with open(filename, 'w') as f:
                json.dump(content, f, indent=2)
        except Exception as e:
            logger.error(f"Error storing content for {url}: {str(e)}")
    
    def _extract_news_items(self, content: str) -> List[Dict]:
        """Extract individual news items from content."""
        news_items = []
        
        # Basic extraction with regex - look for news item patterns
        # This is a simple approach; more sophisticated parsing might be needed for specific sites
        title_matches = re.finditer(r'\[\*\*(.*?)\*\*\]\((https?://[^)]+)\)', content)
        
        for match in title_matches:
            title = match.group(1)
            url = match.group(2)
            
            # Look for a date near the title
            date_match = re.search(r'(\d+\s+\w+,\s+\d{4})', content[match.end():match.end()+100])
            date = date_match.group(1) if date_match else None
            
            # Extract a snippet of content after the title
            content_start = match.end()
            content_end = content.find("[**", content_start)
            if content_end == -1:
                content_end = len(content)
            
            # Limit snippet to a reasonable length
            snippet = content[content_start:min(content_start + 500, content_end)].strip()
            
            news_items.append({
                "title": title,
                "url": url,
                "date": date,
                "content": snippet,  # Include content snippet matching Firecrawl's format
                "first_seen": datetime.now().isoformat()
            })
        
        return news_items
            
    def get_previous_content(self, url: str) -> Optional[Dict]:
        """Get previously stored content for a URL."""
        filename = self._get_filename(url)
        try:
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    return json.load(f)
            return None
        except Exception as e:
            logger.error(f"Error retrieving previous content for {url}: {str(e)}")
            return None
            
    def is_recent_news_item(self, url: str, title: str, days: int = 14) -> bool:
        """
        Check if a news item with this title has been seen recently.
        
        Args:
            url: The base URL of the content
            title: The title of the news item to check
            days: How many days back to check (default: 14)
            
        Returns:
            True if this news item was seen recently, False otherwise
        """
        previous_content = self.get_previous_content(url)
        if not previous_content or "news_items" not in previous_content:
            return False
            
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for item in previous_content.get("news_items", []):
            if item.get("title") == title:
                # Check when it was first seen
                try:
                    first_seen = datetime.fromisoformat(item.get("first_seen", ""))
                    if first_seen > cutoff_date:
                        return True
                except (ValueError, TypeError):
                    # If date parsing fails, be conservative and assume it's not recent
                    pass
                    
        return False