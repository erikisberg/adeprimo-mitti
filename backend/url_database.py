"""
URL database management for Mitti Scraper
Handles synchronization between local JSON file and Supabase
"""

import os
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
import traceback

from supabase import Client
from utils import logger

class URLDatabase:
    """Manages URLs between local JSON file and Supabase"""
    
    def __init__(self, supabase_client: Optional[Client] = None, local_path: str = "urls.json"):
        """Initialize with optional Supabase client and local file path"""
        self.supabase = supabase_client
        self.local_path = local_path
        self.has_supabase = supabase_client is not None
    
    def get_urls(self) -> List[Dict[str, Any]]:
        """Get URLs, preferring Supabase if available, falling back to local file"""
        if self.has_supabase:
            try:
                logger.info("Fetching URLs from Supabase")
                urls = self._get_urls_from_supabase()
                if urls:
                    return urls
                logger.warning("No URLs found in Supabase, falling back to local file")
            except Exception as e:
                logger.error(f"Error fetching from Supabase: {str(e)}")
                logger.info("Falling back to local file")
        
        return self._get_urls_from_file()
    
    def _get_urls_from_file(self) -> List[Dict[str, Any]]:
        """Get URLs from local JSON file"""
        try:
            with open(self.local_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading local URL file: {str(e)}")
            return []
    
    def _get_urls_from_supabase(self) -> List[Dict[str, Any]]:
        """Get URLs from Supabase"""
        if not self.supabase:
            return []
        
        try:
            response = self.supabase.table("monitored_urls")\
                .select("*")\
                .eq("active", True)\
                .execute()
            
            # Convert Supabase format to our format
            urls = []
            for item in response.data:
                urls.append({
                    "name": item.get("name", ""),
                    "url": item.get("url", ""),
                    "category": item.get("category", ""),
                    "id": item.get("id", "")  # Keep the ID for reference
                })
            return urls
        except Exception as e:
            logger.error(f"Error fetching URLs from Supabase: {str(e)}")
            logger.debug(traceback.format_exc())
            return []
    
    def sync_to_supabase(self) -> bool:
        """Sync local URLs to Supabase"""
        if not self.supabase:
            logger.warning("Cannot sync to Supabase: No Supabase client")
            return False
        
        try:
            # Get local URLs
            local_urls = self._get_urls_from_file()
            if not local_urls:
                logger.warning("No local URLs to sync")
                return False
            
            # Insert/update in Supabase
            for url_item in local_urls:
                self.supabase.table("monitored_urls")\
                    .upsert({
                        "url": url_item.get("url"),
                        "name": url_item.get("name"),
                        "category": url_item.get("category", "Övrigt"),
                        "active": True,
                        "updated_at": "now()"
                    })\
                    .execute()
            
            logger.info(f"Synced {len(local_urls)} URLs to Supabase")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing to Supabase: {str(e)}")
            logger.debug(traceback.format_exc())
            return False
    
    def sync_from_supabase(self) -> bool:
        """Sync Supabase URLs to local file"""
        if not self.supabase:
            logger.warning("Cannot sync from Supabase: No Supabase client")
            return False
        
        try:
            # Get Supabase URLs
            supabase_urls = self._get_urls_from_supabase()
            if not supabase_urls:
                logger.warning("No Supabase URLs to sync")
                return False
            
            # Format for local file
            local_format = []
            for url in supabase_urls:
                local_format.append({
                    "name": url.get("name"),
                    "url": url.get("url"),
                    "category": url.get("category", "Övrigt")
                })
            
            # Save to local file
            with open(self.local_path, "w", encoding="utf-8") as f:
                json.dump(local_format, f, indent=2)
            
            logger.info(f"Synced {len(supabase_urls)} URLs from Supabase to local file")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing from Supabase: {str(e)}")
            logger.debug(traceback.format_exc())
            return False
    
    def add_url(self, url: str, name: str, category: str = "Övrigt") -> bool:
        """Add a URL to both Supabase and local file"""
        # Add to Supabase if available
        supabase_success = True
        if self.has_supabase:
            try:
                self.supabase.table("monitored_urls")\
                    .insert({
                        "url": url,
                        "name": name,
                        "category": category,
                        "active": True
                    })\
                    .execute()
                logger.info(f"Added URL to Supabase: {name} ({url})")
            except Exception as e:
                logger.error(f"Error adding URL to Supabase: {str(e)}")
                supabase_success = False
        
        # Add to local file
        try:
            urls = self._get_urls_from_file()
            
            # Check if URL already exists
            for item in urls:
                if item.get("url") == url:
                    item["name"] = name
                    item["category"] = category
                    break
            else:
                # URL doesn't exist, add it
                urls.append({
                    "name": name,
                    "url": url,
                    "category": category
                })
            
            # Save to file
            with open(self.local_path, "w", encoding="utf-8") as f:
                json.dump(urls, f, indent=2)
            
            logger.info(f"Added URL to local file: {name} ({url})")
            return True
        except Exception as e:
            logger.error(f"Error adding URL to local file: {str(e)}")
            if not supabase_success:
                return False
        
        return supabase_success
    
    def remove_url(self, url: str) -> bool:
        """Remove a URL from both Supabase and local file"""
        # Remove from Supabase if available
        supabase_success = True
        if self.has_supabase:
            try:
                # In Supabase, we just set active to false rather than deleting
                self.supabase.table("monitored_urls")\
                    .update({"active": False})\
                    .eq("url", url)\
                    .execute()
                logger.info(f"Marked URL as inactive in Supabase: {url}")
            except Exception as e:
                logger.error(f"Error removing URL from Supabase: {str(e)}")
                supabase_success = False
        
        # Remove from local file
        try:
            urls = self._get_urls_from_file()
            
            # Filter out the URL to remove
            new_urls = [item for item in urls if item.get("url") != url]
            
            if len(new_urls) == len(urls):
                logger.warning(f"URL not found in local file: {url}")
            else:
                # Save to file
                with open(self.local_path, "w", encoding="utf-8") as f:
                    json.dump(new_urls, f, indent=2)
                
                logger.info(f"Removed URL from local file: {url}")
            
            return True
        except Exception as e:
            logger.error(f"Error removing URL from local file: {str(e)}")
            if not supabase_success:
                return False
        
        return supabase_success
    
    def update_url(self, old_url: str, new_data: Dict[str, str]) -> bool:
        """Update a URL in both Supabase and local file"""
        new_url = new_data.get("url", old_url)
        new_name = new_data.get("name")
        new_category = new_data.get("category")
        
        if not new_name:
            logger.error("Name is required for URL update")
            return False
        
        # Update in Supabase if available
        supabase_success = True
        if self.has_supabase:
            try:
                # Prepare update data
                update_data = {
                    "url": new_url,
                    "name": new_name,
                    "updated_at": "now()"
                }
                
                if new_category:
                    update_data["category"] = new_category
                
                self.supabase.table("monitored_urls")\
                    .update(update_data)\
                    .eq("url", old_url)\
                    .execute()
                logger.info(f"Updated URL in Supabase: {old_url} -> {new_url}")
            except Exception as e:
                logger.error(f"Error updating URL in Supabase: {str(e)}")
                supabase_success = False
        
        # Update in local file
        try:
            urls = self._get_urls_from_file()
            
            # Find and update the URL
            found = False
            for item in urls:
                if item.get("url") == old_url:
                    item["url"] = new_url
                    item["name"] = new_name
                    if new_category:
                        item["category"] = new_category
                    found = True
                    break
            
            if not found:
                logger.warning(f"URL not found in local file: {old_url}")
                return supabase_success
            
            # Save to file
            with open(self.local_path, "w", encoding="utf-8") as f:
                json.dump(urls, f, indent=2)
            
            logger.info(f"Updated URL in local file: {old_url} -> {new_url}")
            return True
        except Exception as e:
            logger.error(f"Error updating URL in local file: {str(e)}")
            if not supabase_success:
                return False
        
        return supabase_success 