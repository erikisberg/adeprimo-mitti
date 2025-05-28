"""
File-based notifications for Mitti Scraper - Simple alternative to email
"""

import os
import json
from datetime import datetime
from typing import Dict, List
from utils import logger

class FileNotifier:
    """Saves notification summaries to HTML files instead of sending emails."""
    
    def __init__(self, config: Dict):
        """Initialize with configuration."""
        self.output_dir = "notifications"
        self.enabled = True
        self.min_rating_to_notify = config.get("resend", {}).get("min_rating_to_notify", 3)
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info(f"File notifications enabled - saving to {self.output_dir}/")
    
    def should_send_notification(self, analysis_results: List[Dict]) -> bool:
        """Check if we should create a notification based on analysis results."""
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
    
    def send_summary_email(self, analysis_results: List[Dict]) -> bool:
        """Save summary to file instead of sending email."""
        try:
            if not self.should_send_notification(analysis_results):
                logger.info("No notification needed - no high-interest content found")
                return False
            
            # Collect high-interest items
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
                        "analysis_text": analysis.get("analysis", ""),
                        "news_count": len(extracted_news)
                    })
            
            # Generate HTML content
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            html_content = self._generate_html(high_interest_items, all_updates)
            
            # Save HTML file
            html_filename = f"{self.output_dir}/mitti_summary_{timestamp}.html"
            with open(html_filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Also save JSON for programmatic access
            json_filename = f"{self.output_dir}/mitti_summary_{timestamp}.json"
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "high_interest_items": high_interest_items,
                    "all_updates": all_updates
                }, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Notification saved to: {html_filename}")
            logger.info(f"✅ JSON data saved to: {json_filename}")
            logger.info(f"📊 Found {len(high_interest_items)} high-interest items")
            
            # Open in browser automatically on macOS
            try:
                os.system(f"open {html_filename}")
                logger.info("📂 Opened summary in browser")
            except:
                pass
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating notification file: {str(e)}")
            return False
    
    def _generate_html(self, high_interest_items: List[Dict], all_updates: List[Dict]) -> str:
        """Generate HTML content."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Mitti AI - Nyhetssammanfattning {datetime.now().strftime('%Y-%m-%d %H:%M')}</title>
            <style>
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                    line-height: 1.6; 
                    color: #333; 
                    max-width: 800px; 
                    margin: 0 auto; 
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .header {{ 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white; 
                    padding: 30px; 
                    text-align: center; 
                    border-radius: 10px;
                    margin-bottom: 30px;
                }}
                .header h1 {{ margin: 0; }}
                .content {{ 
                    background: white; 
                    padding: 30px; 
                    border-radius: 10px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .news-item {{ 
                    border-left: 4px solid #667eea; 
                    padding: 15px; 
                    margin: 15px 0; 
                    background-color: #f8f9fa; 
                    border-radius: 5px;
                }}
                .high-rating {{ border-left-color: #e74c3c; }}
                .rating {{ 
                    display: inline-block;
                    background: #e74c3c; 
                    color: white; 
                    padding: 2px 8px; 
                    border-radius: 3px;
                    font-weight: bold;
                }}
                .site-name {{ color: #667eea; font-weight: bold; }}
                .date {{ color: #7f8c8d; font-size: 0.9em; }}
                .summary {{ 
                    background-color: #f8f9fa; 
                    padding: 20px; 
                    margin: 20px 0; 
                    border-radius: 5px;
                    border: 1px solid #e9ecef;
                }}
                .stats {{ 
                    display: grid; 
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                    gap: 15px; 
                    margin: 20px 0;
                }}
                .stat-card {{
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 5px;
                    text-align: center;
                    border: 1px solid #e9ecef;
                }}
                .stat-number {{ font-size: 2em; font-weight: bold; color: #667eea; }}
                .footer {{ 
                    text-align: center; 
                    color: #7f8c8d; 
                    margin-top: 30px;
                    font-size: 0.9em;
                }}
                a {{ color: #667eea; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🤖 Mitti AI - Nyhetssammanfattning</h1>
                <p>{datetime.now().strftime('%A %d %B %Y, %H:%M')}</p>
            </div>
            
            <div class="content">
                <div class="stats">
                    <div class="stat-card">
                        <div class="stat-number">{len(high_interest_items)}</div>
                        <div>Intressanta nyheter</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{len([u for u in all_updates if u['status'] == 'analyzed'])}</div>
                        <div>Analyserade sidor</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{self.min_rating_to_notify}+</div>
                        <div>Minsta betyg</div>
                    </div>
                </div>
                
                <h2>🔥 Högintressanta nyheter (betyg {self.min_rating_to_notify}+)</h2>
        """
        
        if high_interest_items:
            for item in sorted(high_interest_items, key=lambda x: x['rating'], reverse=True):
                rating_class = "high-rating" if item['rating'] >= 4 else ""
                html += f"""
                <div class="news-item {rating_class}">
                    <div class="site-name">{item['site']}</div>
                    <h3>{item['title']}</h3>
                    <div class="date">{item['date'] or 'Inget datum'}</div>
                    <div class="rating">Betyg: {item['rating']}/5</div>
                    <div style="margin-top: 10px;">
                        <a href="{item['url']}" target="_blank">Läs mer →</a>
                    </div>
                </div>
                """
        else:
            html += "<p>Inga högintressanta nyheter hittades.</p>"
        
        html += """
                <div class="summary">
                    <h3>📊 Alla analyserade webbplatser</h3>
        """
        
        for update in all_updates:
            if update['status'] == 'analyzed':
                html += f"""
                    <div style="margin: 10px 0; padding: 10px; background: #f8f9fa; border-radius: 5px;">
                        <strong>{update['site']}</strong> - 
                        Betyg: {update['rating'] or 'N/A'} - 
                        {update['news_count']} nyheter - 
                        <a href="{update['url']}" target="_blank">Besök sida</a>
                    </div>
                """
        
        html += f"""
                </div>
            </div>
            
            <div class="footer">
                <p>Denna sammanfattning genererades automatiskt av Mitti AI</p>
                <p>Genererad: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </body>
        </html>
        """
        
        return html