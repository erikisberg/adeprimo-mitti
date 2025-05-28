"""
Content monitoring orchestration for Mitti Scraper
"""

import re
import os
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from utils import logger
from config import ConfigManager
from url_manager import URLManager
from url_database import URLDatabase
from scraper import ContentScraper
from storage.content import ContentStorage
from storage.analysis import AnalysisStorage
from comparison import ContentComparator
from analysis import OpenAIAnalyzer
from notifications import SlackNotifier
from email_notifications import ResendEmailNotifier
from file_notifications import FileNotifier
from supabase import create_client, Client

class ContentMonitor:
    """Main class that orchestrates the content monitoring process."""
    
    def __init__(self, config_path: str = "config.json", supabase_client: Optional[Client] = None):
        """Initialize the content monitor with configuration and optional Supabase client."""
        self.config_manager = ConfigManager(config_path)
        self.supabase = supabase_client
        
        # Initialize components in the right order - ContentStorage needs to be initialized before OpenAIAnalyzer
        # Use URLDatabase if Supabase client is provided, otherwise fall back to URLManager
        if supabase_client:
            logger.info("Using URLDatabase with Supabase integration")
            self.url_manager = URLDatabase(
                supabase_client, 
                self.config_manager.get("url_list_path")
            )
            # Initial sync from local to Supabase to ensure all URLs are available
            self.url_manager.sync_to_supabase()
        else:
            logger.info("Using local URLManager (no Supabase)")
            self.url_manager = URLManager(self.config_manager.get("url_list_path"))
        
        self.content_scraper = ContentScraper(
            self.config_manager.get("firecrawl_api_key"),
            self.config_manager.config
        )
        self.content_storage = ContentStorage(
            self.config_manager.get("content_storage_dir", "data/history")
        )
        self.content_comparator = ContentComparator(
            self.config_manager.get("similarity_threshold", 0.9)
        )
        self.analysis_storage = AnalysisStorage(
            self.config_manager.get("analysis_storage_dir", "data/analysis")
        )
        
        # Initialize OpenAI analyzer after storage components
        self.openai_analyzer = OpenAIAnalyzer(
            self.config_manager.get("openai_api_key"),
            self.config_manager.get("openai_assistant_id")
        )
        
        # Initialize Slack notifier if configured
        self.slack_config = self.config_manager.get("notifications", {}).get("slack", {})
        self.slack_notifier = SlackNotifier(self.slack_config)
        
        # Initialize Email notifier if configured
        self.email_notifier = ResendEmailNotifier(self.config_manager.get("notifications", {}))
        
        # Also initialize file notifier as a simple alternative
        self.file_notifier = FileNotifier(self.config_manager.get("notifications", {}))
    
    def monitor_url(self, url_info: Dict) -> Dict:
        """
        Monitor a single URL for changes and analyze if necessary.
        
        Returns a dictionary with monitoring results.
        """
        url = url_info.get("url")
        name = url_info.get("name", url)
        
        logger.info(f"Monitoring URL: {name} ({url})")
        
        result = {
            "url": url,
            "name": name,
            "timestamp": datetime.now().isoformat(),
            "changes_detected": False,
            "analyzed": False
        }
        
        try:
            # Step 1: Scrape current content
            current_content = self.content_scraper.scrape_url(url)
            
            if "error" in current_content:
                result["status"] = "error"
                result["error"] = current_content["error"]
                return result
                
            # Step 2: Get previous content
            previous_content = self.content_storage.get_previous_content(url)
            
            # Step 3: Compare content
            has_changes, similarity, diff_summary = self.content_comparator.has_significant_changes(
                previous_content, current_content
            )
            
            result["changes_detected"] = has_changes
            result["similarity"] = similarity
            
            if has_changes:
                logger.info(f"Significant changes detected for {name} (similarity: {similarity:.2f})")
                
                # Step 4: Analyze content with OpenAI
                analysis = self.openai_analyzer.analyze_content(
                    url, 
                    current_content,  # Pass the whole content dictionary
                    diff_summary
                )
                
                result["analyzed"] = True
                result["analysis"] = analysis
                
                # Step 5: Store analysis
                self.analysis_storage.store_analysis(url, current_content, analysis)
                
                # Step 6: Save to Supabase if available
                if self.supabase:
                    self._save_analysis_to_supabase(url_info, result)
            else:
                logger.info(f"No significant changes for {name} (similarity: {similarity:.2f})")
            
            # Always store the current content for future comparison
            self.content_storage.store_content(url, current_content)
            
            # Set status based on whether analysis was performed
            if result.get("analyzed"):
                result["status"] = "analyzed"
            else:
                result["status"] = "success"
            return result
            
        except Exception as e:
            logger.error(f"Error monitoring {name}: {str(e)}")
            result["status"] = "error"
            result["error"] = str(e)
            return result
    
    def _save_analysis_to_supabase(self, url_info: Dict, result: Dict) -> bool:
        """Save analysis results to Supabase."""
        if not self.supabase:
            return False
            
        try:
            analysis = result.get("analysis", {})
            
            # Save main analysis
            analysis_data = {
                "url": result.get("url"),
                "site_name": result.get("name"),
                "overall_rating": int(analysis.get("rating", 0)) if analysis.get("rating") else None,
                "analysis_text": analysis.get("analysis", ""),
                "analyzed_at": datetime.now().isoformat(),
                "changes_detected": result.get("changes_detected", False)
            }
            
            response = self.supabase.table("analyses").insert(analysis_data).execute()
            if not response.data:
                logger.error("No data returned from Supabase insert")
                return False
                
            analysis_id = response.data[0]["id"]
            
            # Save individual news items
            news_items = analysis.get("extracted_news", [])
            for item in news_items:
                news_data = {
                    "analysis_id": analysis_id,
                    "title": item.get("title", ""),
                    "date": item.get("date"),
                    "rating": int(item.get("rating", 0)) if item.get("rating") else None,
                    "content": item.get("snippet", "")
                }
                self.supabase.table("news_items").insert(news_data).execute()
                
            logger.info(f"Saved analysis to Supabase for {result.get('name')}")
            return True
        except Exception as e:
            logger.error(f"Error saving to Supabase: {str(e)}")
            return False
    
    def run(self) -> List[Dict]:
        """Run the monitoring process for all URLs."""
        results = []
        
        urls = self.url_manager.get_urls()
        total_urls = len(urls)
        
        logger.info(f"Starting monitoring process for {total_urls} URLs")
        
        # Process each URL individually instead of in batches
        for i, url_info in enumerate(urls):
            logger.info(f"Processing URL {i+1}/{total_urls}: {url_info.get('name', url_info.get('url'))}")
            result = self.monitor_url(url_info)
            results.append(result)
        
        # Send email summary after processing all URLs
        try:
            logger.info("Checking if email summary should be sent...")
            email_sent = self.email_notifier.send_summary_email(results)
            if email_sent:
                logger.info("Email summary sent successfully")
            else:
                logger.info("No email summary sent (no high-interest content or email disabled)")
        except Exception as e:
            logger.error(f"Error sending email summary: {str(e)}")
            
        # Always save to file as backup/alternative
        try:
            logger.info("Saving notification summary to file...")
            file_sent = self.file_notifier.send_summary_email(results)
            if file_sent:
                logger.info("✅ Notification summary saved to file")
        except Exception as e:
            logger.error(f"Error saving notification file: {str(e)}")
            
        logger.info(f"Completed monitoring process")
        return results
        
    def _process_url_content(self, url_info: Dict, current_content: Dict) -> Dict:
        """Process a URL with pre-scraped content."""
        url = url_info.get("url")
        name = url_info.get("name", url)
        
        logger.info(f"Processing content for: {name} ({url})")
        
        result = {
            "url": url,
            "name": name,
            "timestamp": datetime.now().isoformat(),
            "changes_detected": False,
            "analyzed": False
        }
        
        try:
            # Get previous content
            previous_content = self.content_storage.get_previous_content(url)
            
            # Check if we have news items in current content that weren't in previous content
            new_news_items = self._detect_new_news_items(previous_content, current_content)
            
            # Compare content
            has_changes, similarity, diff_summary = self.content_comparator.has_significant_changes(
                previous_content, current_content
            )
            
            result["changes_detected"] = has_changes
            result["similarity"] = similarity
            
            # Always analyze content if we have new news items, even if overall similarity is high
            should_analyze = has_changes or len(new_news_items) > 0
            
            if should_analyze:
                if has_changes:
                    logger.info(f"Significant changes detected for {name} (similarity: {similarity:.2f})")
                elif len(new_news_items) > 0:
                    logger.info(f"New news items detected for {name} ({len(new_news_items)} items)")
                
                # Analyze content with OpenAI - pass the full content dictionary
                analysis = self.openai_analyzer.analyze_content(
                    url, 
                    current_content,  # Pass the whole content dictionary with extracted news
                    diff_summary
                )
                
                result["analyzed"] = True
                result["analysis"] = analysis
                
                # Store analysis
                self.analysis_storage.store_analysis(url, current_content, analysis)
                
                # Send notification to Slack if enabled and rating is high enough
                # Check both the SlackNotifier enabled flag and the environment variable
                if self.slack_notifier.enabled and not os.environ.get("DISABLE_SLACK", "").lower() in ("true", "1", "yes"):
                    logger.info("Sending Slack notification...")
                    self.slack_notifier.send_notification(url_info, analysis, current_content)
                else:
                    logger.info("Skipping Slack notification (disabled)")
            else:
                logger.info(f"No significant changes for {name} (similarity: {similarity:.2f})")
            
            # Always store the current content for future comparison
            self.content_storage.store_content(url, current_content)
            
            # Set status based on whether analysis was performed
            if result.get("analyzed"):
                result["status"] = "analyzed"
            else:
                result["status"] = "success"
            return result
            
        except Exception as e:
            logger.error(f"Error processing {name}: {str(e)}")
            result["status"] = "error"
            result["error"] = str(e)
            return result
    
    def _detect_new_news_items(self, previous_content: Dict, current_content: Dict) -> List[Dict]:
        """
        Detect new news items by comparing previous and current content.
        
        Returns a list of new news items found in current content but not in previous content.
        """
        if not previous_content or not current_content:
            return []
            
        # Extract news items from both contents
        previous_items = []
        if previous_content:
            # Get previous news items from extracted_news (or news_items for backward compatibility)
            if "extracted_news" in previous_content:
                previous_items = previous_content.get("extracted_news", [])
            elif "news_items" in previous_content:
                previous_items = previous_content.get("news_items", [])
            
        # Get current news items
        current_items = []
        if "extracted_news" in current_content and current_content["extracted_news"]:
            # Use news items extracted by Firecrawl
            current_items = current_content.get("extracted_news", [])
            logger.info(f"Using {len(current_items)} news items extracted by Firecrawl")
        else:
            # Fall back to OpenAI extraction if no Firecrawl extracted news
            current_items = self.openai_analyzer.extract_news_items(current_content)
            # Store the extracted items in the content dictionary
            current_content["extracted_news"] = current_items
            logger.info(f"Using {len(current_items)} news items extracted by OpenAI")
        
        # Find new items by comparing titles
        previous_titles = {item.get("title", "").strip() for item in previous_items}
        new_items = [item for item in current_items if item.get("title", "").strip() not in previous_titles]
        
        if new_items:
            logger.info(f"Found {len(new_items)} new news items")
            for item in new_items:
                logger.info(f"  - {item.get('title', 'Untitled')}")
                
        return new_items