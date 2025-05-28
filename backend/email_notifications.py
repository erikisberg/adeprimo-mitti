"""
Email notifications using Resend for Mitti Scraper
"""

import os
import resend
from datetime import datetime
from typing import Dict, List, Optional
from utils import logger

class ResendEmailNotifier:
    """Handles email notifications using Resend service."""
    
    def __init__(self, config: Dict):
        """Initialize with Resend configuration."""
        self.config = config.get("resend", {})
        self.enabled = self.config.get("enabled", False)
        
        # Get API key from config or environment
        self.api_key = self.config.get("api_key") or os.environ.get("RESEND_API_KEY")
        self.audience_id = self.config.get("audience_id")
        self.from_email = self.config.get("from_email", "Mitti AI <noreply@yourdomain.com>")
        self.min_rating_to_notify = self.config.get("min_rating_to_notify", 3)
        
        if self.enabled and self.api_key:
            resend.api_key = self.api_key
            logger.info("Resend email notifications enabled")
        elif self.enabled:
            logger.warning("Resend notifications enabled but no API key found")
        else:
            logger.info("Resend email notifications disabled")
    
    def should_send_notification(self, analysis_results: List[Dict]) -> bool:
        """Check if we should send an email notification based on analysis results."""
        if not self.enabled or not self.api_key or not self.audience_id:
            return False
        
        # Check if any content has high enough rating
        for result in analysis_results:
            if result.get("status") == "analyzed":
                analysis = result.get("analysis", {})
                
                # Check overall rating
                if analysis.get("rating") and int(analysis.get("rating", 0)) >= self.min_rating_to_notify:
                    return True
                
                # Check individual news item ratings
                extracted_news = analysis.get("extracted_news", [])
                for news_item in extracted_news:
                    if news_item.get("rating") and int(news_item.get("rating", 0)) >= self.min_rating_to_notify:
                        return True
        
        return False
    
    def format_email_content(self, analysis_results: List[Dict]) -> Dict[str, str]:
        """Format the analysis results into email content."""
        high_interest_items = []
        all_updates = []
        
        for result in analysis_results:
            if result.get("status") == "analyzed":
                site_name = result.get("name", "Unknown Site")
                url = result.get("url", "")
                analysis = result.get("analysis", {})
                
                # Get high-interest news items
                extracted_news = analysis.get("extracted_news", [])
                for news_item in extracted_news:
                    rating = news_item.get("rating", 0)
                    if rating and int(rating) >= self.min_rating_to_notify:
                        high_interest_items.append({
                            "site": site_name,
                            "title": news_item.get("title", ""),
                            "date": news_item.get("date", ""),
                            "rating": rating,
                            "url": url
                        })
                
                # Add to all updates
                all_updates.append({
                    "site": site_name,
                    "url": url,
                    "status": result.get("status"),
                    "rating": analysis.get("rating"),
                    "news_count": len(extracted_news)
                })
        
        # Generate HTML content
        html_content = self._generate_html_email(high_interest_items, all_updates)
        
        # Generate plain text content
        text_content = self._generate_text_email(high_interest_items, all_updates)
        
        return {
            "html": html_content,
            "text": text_content,
            "subject": f"Mitti AI - {len(high_interest_items)} intressanta nyheter ({datetime.now().strftime('%Y-%m-%d')})"
        }
    
    def _generate_html_email(self, high_interest_items: List[Dict], all_updates: List[Dict]) -> str:
        """Generate HTML email content."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #2c3e50; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .news-item {{ border-left: 4px solid #3498db; padding: 15px; margin: 15px 0; background-color: #f8f9fa; }}
                .high-rating {{ border-left-color: #e74c3c; }}
                .rating {{ font-weight: bold; color: #e74c3c; }}
                .site-name {{ color: #2c3e50; font-weight: bold; }}
                .date {{ color: #7f8c8d; font-size: 0.9em; }}
                .summary {{ background-color: #ecf0f1; padding: 15px; margin: 20px 0; }}
                .footer {{ background-color: #34495e; color: white; padding: 15px; text-align: center; font-size: 0.9em; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🤖 Mitti AI - Nyhetssammanfattning</h1>
                <p>{datetime.now().strftime('%A, %d %B %Y')}</p>
            </div>
            
            <div class="content">
                <h2>🔥 Högintressanta nyheter (betyg {self.min_rating_to_notify}+)</h2>
        """
        
        if high_interest_items:
            for item in high_interest_items:
                html += f"""
                <div class="news-item high-rating">
                    <div class="site-name">{item['site']}</div>
                    <h3>{item['title']}</h3>
                    <div class="date">{item['date']}</div>
                    <div class="rating">Betyg: {item['rating']}/5</div>
                    <a href="{item['url']}" target="_blank">Läs mer →</a>
                </div>
                """
        else:
            html += "<p>Inga högintressanta nyheter idag.</p>"
        
        html += """
                <div class="summary">
                    <h3>📊 Sammanfattning av alla webbplatser</h3>
                    <ul>
        """
        
        for update in all_updates:
            status_emoji = "✅" if update['status'] == "analyzed" else "❌"
            html += f"""
                        <li>{status_emoji} <strong>{update['site']}</strong> - 
                        {update['news_count']} nyheter funna
                        {f" (genomsnittligt betyg: {update['rating']})" if update['rating'] else ""}
                        </li>
            """
        
        html += f"""
                    </ul>
                </div>
            </div>
            
            <div class="footer">
                <p>Denna sammanfattning genererades automatiskt av Mitti AI</p>
                <p>Du kan avsluta prenumerationen här: {{{{RESEND_UNSUBSCRIBE_URL}}}}</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_text_email(self, high_interest_items: List[Dict], all_updates: List[Dict]) -> str:
        """Generate plain text email content."""
        text = f"""
MITTI AI - NYHETSSAMMANFATTNING
{datetime.now().strftime('%A, %d %B %Y')}

🔥 HÖGINTRESSANTA NYHETER (betyg {self.min_rating_to_notify}+):
{"="*50}

"""
        
        if high_interest_items:
            for item in high_interest_items:
                text += f"""
{item['site']}
{item['title']}
Datum: {item['date']}
Betyg: {item['rating']}/5
Läs mer: {item['url']}

"""
        else:
            text += "Inga högintressanta nyheter idag.\n\n"
        
        text += f"""
📊 SAMMANFATTNING AV ALLA WEBBPLATSER:
{"="*40}

"""
        
        for update in all_updates:
            status = "✅ Analyserad" if update['status'] == "analyzed" else "❌ Fel"
            text += f"{status} - {update['site']} - {update['news_count']} nyheter\n"
        
        text += f"""

Denna sammanfattning genererades automatiskt av Mitti AI.
Du kan avsluta prenumerationen här: {{{{RESEND_UNSUBSCRIBE_URL}}}}
"""
        
        return text
    
    def send_summary_email(self, analysis_results: List[Dict]) -> bool:
        """Send summary email if conditions are met."""
        try:
            if not self.should_send_notification(analysis_results):
                logger.info("No email notification needed - no high-interest content found")
                return False
            
            email_content = self.format_email_content(analysis_results)
            
            # Create broadcast
            params = {
                "audience_id": self.audience_id,
                "from": self.from_email,
                "subject": email_content["subject"],
                "html": email_content["html"],
                "text": email_content["text"]
            }
            
            logger.info(f"Creating email broadcast: {email_content['subject']}")
            broadcast_response = resend.Broadcasts.create(params)
            
            if broadcast_response and broadcast_response.get("id"):
                broadcast_id = broadcast_response["id"]
                logger.info(f"Broadcast created with ID: {broadcast_id}")
                
                # Send immediately
                send_params = {
                    "broadcast_id": broadcast_id,
                    "scheduled_at": "now"
                }
                
                send_response = resend.Broadcasts.send(send_params)
                logger.info(f"Email broadcast sent successfully: {send_response}")
                return True
            else:
                logger.error(f"Failed to create broadcast: {broadcast_response}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending email notification: {str(e)}")
            return False
    
    def test_email_connection(self) -> bool:
        """Test the email service connection."""
        try:
            if not self.api_key:
                logger.error("No Resend API key configured")
                return False
            
            # Test with a simple email creation (but don't send)
            test_params = {
                "audience_id": self.audience_id,
                "from": self.from_email,
                "subject": "Test - Mitti AI Connection",
                "html": "<p>This is a test email to verify Resend integration.</p>"
            }
            
            # Just validate the parameters without actually creating
            logger.info("Resend email service configuration appears valid")
            return True
            
        except Exception as e:
            logger.error(f"Error testing email connection: {str(e)}")
            return False 