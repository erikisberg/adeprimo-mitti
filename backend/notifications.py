"""
Notification functionality for Mitti Scraper
"""

import os
import re
import requests
from typing import Dict, List, Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from utils import logger

class SlackNotifier:
    """Handles Slack notifications about content changes."""
    
    def __init__(self, slack_config: Optional[Dict] = None):
        """Initialize with Slack configuration."""
        self.slack_config = slack_config or {}
        self.enabled = self.slack_config.get("enabled", False)
        self.client = None
        
        # Early return if disabled
        if not self.enabled:
            logger.info("Slack notifications are disabled in config")
            return
            
        # Check if we should force disable (for temporary disabling)
        force_disable = os.environ.get("DISABLE_SLACK", "").lower() in ("true", "1", "yes")
        if force_disable:
            logger.info("Slack notifications are force-disabled by environment variable")
            self.enabled = False
            return
            
        # Initialize Slack client if enabled and token is available
        slack_token = os.environ.get("SLACK_BOT_TOKEN")
        if slack_token:
            self.client = WebClient(token=slack_token)
            logger.info("Slack notifications enabled")
        else:
            logger.warning("Slack notifications enabled in config but SLACK_BOT_TOKEN not found in environment")
    
    def send_notification(self, url_info: Dict, analysis: Dict, content: Dict) -> None:
        """Send a notification to Slack about significant content changes."""
        # Immediate return if disabled (check both the instance flag and environment)
        if not self.enabled or os.environ.get("DISABLE_SLACK", "").lower() in ("true", "1", "yes"):
            logger.info("Slack notifications disabled, skipping")
            return
            
        try:
            url = url_info.get("url")
            name = url_info.get("name", url)
            min_rating = self.slack_config.get("min_rating_to_notify", 3)
            include_preview = self.slack_config.get("include_content_preview", True)
            # Try to get webhook URL from environment first, fall back to config
            webhook_url = os.environ.get("SLACK_WEBHOOK_URL") or self.slack_config.get("webhook_url")
            
            # Extract rating from analysis
            rating = None
            if isinstance(analysis, dict) and "rating" in analysis:
                rating = analysis.get("rating")
                if rating:
                    try:
                        rating = int(rating)
                    except ValueError:
                        # Try to extract rating from text using regex pattern
                        if isinstance(analysis.get("analysis"), str):
                            rating_match = re.search(r"(?:Betyg|Rating):\s*(\d)", analysis.get("analysis"))
                            if rating_match:
                                try:
                                    rating = int(rating_match.group(1))
                                except ValueError:
                                    rating = None
                                
            # Get analysis text
            analysis_text = ""
            if isinstance(analysis, dict):
                analysis_text = analysis.get("analysis", "Ingen analys tillgänglig")
            else:
                analysis_text = str(analysis)
            
            # Extract news items from analysis
            news_items = []
            if isinstance(analysis, dict):
                if "extracted_news" in analysis:
                    news_items = analysis.get("extracted_news", [])
                # Fallback for backward compatibility
                elif "news_items" in analysis:
                    news_items = analysis.get("news_items", [])
            
            # Only proceed with notification if there are news items worth reporting
            # First check overall rating, then check for any high-rated news items
            should_notify = False
            
            # Check if overall rating meets threshold
            if rating is None or rating >= min_rating:
                should_notify = True
            
            # Also notify if any individual news item has a high rating
            high_rated_items = []
            for item in news_items:
                item_rating = item.get("rating")
                if item_rating and item_rating >= min_rating:
                    high_rated_items.append(item)
                    should_notify = True
            
            # Check for recent news items
            from storage.content import ContentStorage
            content_storage = ContentStorage()
            
            # Check if any news items are very recent (less than 5 days old)
            new_news_items = []
            for item in news_items:
                title = item.get("title", "")
                # Skip items we've already reported recently
                if content_storage.is_recent_news_item(url, title, days=5):
                    logger.info(f"Skipping already reported news item: {title}")
                    continue
                new_news_items.append(item)
            
            # Only notify if we have new news items
            if not new_news_items:
                logger.info(f"No new news items to report for {name}")
                return
                
            # Only proceed with notification if we should notify and have new news
            if should_notify and new_news_items:
                # Create message
                blocks = [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"Innehållsändring upptäckt: {name}"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*URL:* <{url}|{url}>\n*Betyg:* {rating if rating else 'Inte betygsatt'}"
                        }
                    }
                ]
                
                # Add news items section if we have any
                if new_news_items:
                    news_items_text = "*Nya nyheter:*\n"
                    for item in new_news_items[:5]:  # Limit to top 5
                        item_rating = item.get("rating", "?")
                        item_date = item.get("date", "Inget datum")
                        item_title = item.get("title", "")
                        item_url = item.get("url", "")
                        
                        if item_url:
                            news_items_text += f"• <{item_url}|{item_title}> (Betyg: {item_rating}) - {item_date}\n"
                        else:
                            news_items_text += f"• {item_title} (Betyg: {item_rating}) - {item_date}\n"
                    
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": news_items_text
                        }
                    })
                
                # Add analysis section
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Analys:*\n{analysis_text[:800]}"
                    }
                })
                
                # Add content preview if enabled
                if include_preview:
                    content_text = content.get("content", "")
                    if content_text:
                        preview = content_text[:300] + "..." if len(content_text) > 300 else content_text
                        blocks.append({
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*Innehållsförhandsvisning:*\n```{preview}```"
                            }
                        })
                
                # Add divider
                blocks.append({"type": "divider"})
                
                # Send via webhook if configured
                if webhook_url:
                    requests.post(
                        webhook_url,
                        json={"blocks": blocks},
                        headers={"Content-Type": "application/json"}
                    )
                    logger.info(f"Slack notification sent for {name}")
                
                # Send via bot API if configured
                if self.client:
                    # Try to get the default channel from environment
                    channel = os.environ.get("SLACK_CHANNEL", "#content-monitoring")
                    
                    self.client.chat_postMessage(
                        channel=channel,
                        blocks=blocks
                    )
                    logger.info(f"Slack API message sent for {name} to {channel}")
            else:
                logger.info(f"No notification sent for {name}: Not enough interesting content")
                    
        except SlackApiError as e:
            logger.error(f"Error sending Slack notification: {str(e)}")
        except requests.RequestException as e:
            logger.error(f"Error sending Slack webhook: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in slack notification: {str(e)}")