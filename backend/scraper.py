"""
Web content scraping for Mitti Scraper
"""

import re
import time
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from utils import logger

class ContentScraper:
    """Handles web content scraping using Firecrawl API with direct requests fallback."""
    
    def __init__(self, api_key: str = None, config: Dict = None):
        """Initialize with Firecrawl API key and optional config."""
        self.api_key = api_key
        self.use_firecrawl = bool(api_key) and not api_key.startswith("your_")
        
        # Load settings from config
        self.config = config or {}
        self.scraping_config = self.config.get("scraping", {})
        self.max_content_length = self.scraping_config.get("max_content_length", 50000)  # Default to 50000
        
        # Track rate limits
        self.rate_limited = False
        self.rate_limit_reset = None
        self.consecutive_errors = 0
        self.max_consecutive_errors = 3
        
        if self.use_firecrawl:
            self.scrape_url_endpoint = "https://api.firecrawl.dev/v1/scrape"
            self.extract_endpoint = "https://api.firecrawl.dev/v1/extract"
            self.firecrawl_headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            logger.info(f"Using Firecrawl API for scraping with key: {self.api_key[:5]}...")
        else:
            logger.warning("Firecrawl API key not provided, using direct scraping as fallback")
            
        # Standard headers for direct requests
        self.direct_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
    # batch_scrape_urls method removed to process each URL individually
        
    def _scrape_with_firecrawl(self, url: str) -> Dict:
        """Scrape content using Firecrawl API with news extraction."""
        # If we've hit rate limits, wait and retry
        if self.rate_limited:
            now = datetime.now()
            if self.rate_limit_reset and now < self.rate_limit_reset:
                wait_time = (self.rate_limit_reset - now).total_seconds()
                logger.warning(f"Rate limited by Firecrawl. Will reset in {wait_time:.1f} seconds.")
                return {
                    "error": f"Rate limited by Firecrawl (resets in {wait_time:.1f} seconds)",
                    "content": "",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # Reset rate limit status
                self.rate_limited = False
                self.consecutive_errors = 0
        
        # If we've had too many consecutive errors, abort
        if self.consecutive_errors >= self.max_consecutive_errors:
            logger.warning(f"Too many consecutive Firecrawl errors ({self.consecutive_errors}). Aborting.")
            return {
                "error": f"Too many consecutive Firecrawl errors ({self.consecutive_errors})",
                "content": "",
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            logger.info(f"Scraping URL with Firecrawl extract endpoint: {url}")
            # Using extract endpoint to identify news items directly
            schema = {
                "type": "object",
                "properties": {
                    "news_items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "date": {"type": "string"},
                                "title": {"type": "string"},
                                "content": {"type": "string"}
                            },
                            "required": ["title"]
                        }
                    },
                    "general_information": {
                        "type": "object",
                        "properties": {
                            "body": {"type": "string"},
                            "description": {"type": "string"},
                            "contact_info": {"type": "string"}
                        }
                    }
                }
            }
            
            payload = {
                "urls": [url],
                "prompt": "Extract news items from this webpage. Each news item should have a title, date (if available), and the content of the news. Also extract general information about the site.",
                "schema": schema
            }
            
            response = requests.post(
                self.extract_endpoint, 
                headers=self.firecrawl_headers,
                json=payload,
                timeout=30  # Reduced timeout for extraction
            )
            
            # Check for rate limiting
            if response.status_code == 429:
                self.rate_limited = True
                # Check for a Retry-After header
                retry_after = response.headers.get('Retry-After')
                if retry_after:
                    try:
                        seconds = int(retry_after)
                        self.rate_limit_reset = datetime.now() + timedelta(seconds=seconds)
                        logger.warning(f"Rate limited by Firecrawl. Will retry after {seconds} seconds.")
                    except ValueError:
                        # If header is in HTTP date format or invalid, use a default
                        self.rate_limit_reset = datetime.now() + timedelta(minutes=5)
                        logger.warning("Rate limited by Firecrawl. Using default 5 minute cooldown.")
                else:
                    # Default to 5 minutes if no header
                    self.rate_limit_reset = datetime.now() + timedelta(minutes=5)
                    logger.warning("Rate limited by Firecrawl. Using default 5 minute cooldown.")
                return None
                
            response.raise_for_status()
            extract_result = response.json()
            
            # Log the structure of the response to help debugging
            logger.info(f"Firecrawl extract response type: {type(extract_result).__name__}")
            if isinstance(extract_result, dict):
                logger.info(f"Firecrawl extract response keys: {', '.join(extract_result.keys())}")
            elif isinstance(extract_result, list):
                logger.info(f"Firecrawl extract response list length: {len(extract_result)}")
                
            # Print the raw response for debugging
            logger.info(f"Firecrawl extract raw response: {json.dumps(extract_result, indent=2)[:1000]}...")
            
            # Handle asynchronous API response - poll for results if job ID is returned
            if isinstance(extract_result, dict) and extract_result.get("success") and extract_result.get("id"):
                job_id = extract_result.get("id")
                logger.info(f"Received job ID {job_id}, polling for results...")
                
                # Poll for job completion
                max_attempts = 3  # Reduced number of polling attempts
                poll_interval = 30  # Start with 30 seconds initial wait
                max_poll_time = 120  # Maximum time to wait in seconds
                
                # Construct the job URL - use the extract endpoint with job ID
                job_url = f"https://api.firecrawl.dev/v1/extract/{job_id}"
                logger.info(f"Polling job at URL: {job_url}")
                
                start_time = time.time()
                for attempt in range(max_attempts):
                    logger.info(f"Polling extract job (attempt {attempt+1}/{max_attempts})")
                    
                    # Check if we've exceeded the maximum polling time
                    elapsed_time = time.time() - start_time
                    if elapsed_time > max_poll_time:
                        logger.warning(f"Polling timed out after {elapsed_time:.1f} seconds")
                        break
                    
                    status_response = requests.get(
                        job_url,
                        headers=self.firecrawl_headers
                    )
                    status_response.raise_for_status()
                    status_data = status_response.json()
                    
                    # Log status response for debugging
                    logger.info(f"Job status response: {json.dumps(status_data, indent=2)[:500]}...")
                    
                    # Check if job is completed (possibly different status format)
                    job_status = status_data.get("status")
                    logger.info(f"Job status: {job_status}")
                    if job_status == "completed":
                        logger.info("Extract job completed")
                        extract_result = status_data.get("data", {})
                        break
                    
                    elif status_data.get("status") == "failed":
                        logger.error(f"Extract job failed: {status_data}")
                        return None
                    
                    # Exponential backoff with a maximum interval
                    time.sleep(min(poll_interval, 60))  # Maximum of 1 minute between polls
                    poll_interval *= 2.0  # Double the wait time each attempt
                    
                logger.info(f"Final extract result type: {type(extract_result).__name__}")
            
            # Try to fetch the page content for full text search and display
            content_result = {}
            try:
                regular_payload = {
                    "url": url,
                    "formats": ["markdown", "html"]
                }
                
                content_response = requests.post(
                    self.scrape_url_endpoint, 
                    headers=self.firecrawl_headers,
                    json=regular_payload,
                    timeout=20  # Reduced timeout for content scraping
                )
                
                content_response.raise_for_status()
                content_result = content_response.json()
                logger.info(f"Successfully fetched full content for {url}")
            except Exception as e:
                logger.warning(f"Failed to fetch full content for {url}: {str(e)}")
                # Continue with empty content_result, we'll generate synthetic content later
            
            # Success! Reset consecutive errors
            self.consecutive_errors = 0
            
            # Combine the extracted news and general content
            # Handle different response formats from Firecrawl API
            if isinstance(extract_result, list) and len(extract_result) > 0:
                extracted_news = extract_result[0]
            elif isinstance(extract_result, dict):
                extracted_news = extract_result
            else:
                extracted_news = {}
                
            news_items = extracted_news.get("news_items", [])
            general_info = extracted_news.get("general_information", {})
            
            # Generate synthetic content from extracted news items if the content_result is empty
            if not content_result.get("markdown") and news_items:
                logger.info(f"Generating synthetic content from {len(news_items)} extracted news items")
                
                # Generate a markdown version of the news items
                synthetic_content = f"# {url}\n\n"
                
                # Add general information if available
                if general_info:
                    if general_info.get("description"):
                        synthetic_content += f"{general_info.get('description')}\n\n"
                    if general_info.get("body"):
                        synthetic_content += f"{general_info.get('body')}\n\n"
                
                # Add each news item
                synthetic_content += "## Nyheter\n\n"
                for item in news_items:
                    title = item.get("title", "")
                    date = item.get("date", "")
                    content = item.get("content", "")
                    
                    if date:
                        synthetic_content += f"### {title} ({date})\n\n"
                    else:
                        synthetic_content += f"### {title}\n\n"
                        
                    synthetic_content += f"{content}\n\n"
                
                # Add contact information if available
                if general_info.get("contact_info"):
                    synthetic_content += f"## Kontakt\n\n{general_info.get('contact_info')}\n\n"
                    
                content = synthetic_content.strip()
                title = url.split("/")[-1] if url.split("/")[-1] else url
            else:
                # Use the original content from content_result
                content = content_result.get("markdown", "")
                title = content_result.get("metadata", {}).get("title", "")
            
            # Convert to our standard format
            return {
                "url": url,
                "title": title,
                "content": content,
                "html": content_result.get("html", ""),
                "extracted_news": news_items,
                "general_info": general_info,
                "timestamp": datetime.now().isoformat()
            }
        except requests.RequestException as e:
            self.consecutive_errors += 1
            error_msg = f"Error scraping URL with Firecrawl {url}: {str(e)}"
            logger.error(error_msg)
            return {
                "error": error_msg,
                "content": "",
                "timestamp": datetime.now().isoformat()
            }
        
    def _scrape_direct(self, url: str) -> Dict:
        """Scrape content directly using requests with improved news extraction."""
        try:
            logger.info(f"Scraping URL directly: {url}")
            response = requests.get(url, headers=self.direct_headers, timeout=30)
            response.raise_for_status()
            
            # Extract content
            html_content = response.text
            
            # Extract title if possible
            title = ""
            title_match = re.search(r"<title>(.*?)</title>", html_content, re.IGNORECASE | re.DOTALL)
            if title_match:
                title = title_match.group(1).strip()
            
            # Extract main content - improved approach
            # Remove script and style elements
            content = re.sub(r"<script[^>]*>.*?</script>", "", html_content, flags=re.DOTALL | re.IGNORECASE)
            content = re.sub(r"<style[^>]*>.*?</style>", "", content, flags=re.DOTALL | re.IGNORECASE)
            
            # Extract text from body
            body_match = re.search(r"<body[^>]*>(.*?)</body>", content, re.IGNORECASE | re.DOTALL)
            if body_match:
                content = body_match.group(1)
            
            # Try to extract news items using common patterns
            news_items = self._extract_news_from_html(html_content)
            
            # Remove HTML tags for plain text
            plain_content = re.sub(r"<[^>]*>", " ", content)
            # Clean up whitespace
            plain_content = re.sub(r"\s+", " ", plain_content).strip()
            
            # Generate synthetic content similar to Firecrawl format
            synthetic_content = f"# {title or url}\n\n"
            if news_items:
                synthetic_content += "## Nyheter\n\n"
                for item in news_items:
                    item_title = item.get("title", "")
                    item_date = item.get("date", "")
                    item_content = item.get("content", "")
                    
                    if item_date:
                        synthetic_content += f"### {item_title} ({item_date})\n\n"
                    else:
                        synthetic_content += f"### {item_title}\n\n"
                        
                    if item_content:
                        synthetic_content += f"{item_content}\n\n"
            
            # Add general content
            synthetic_content += f"## Innehåll\n\n{plain_content[:2000]}...\n\n"
            
            return {
                "url": url,
                "title": title or url,
                "content": synthetic_content.strip(),
                "html": html_content[:5000],  # Store a subset of the HTML
                "extracted_news": news_items,
                "general_info": {
                    "body": plain_content[:1000],
                    "description": title or "No description available"
                },
                "timestamp": datetime.now().isoformat()
            }
        except requests.RequestException as e:
            logger.error(f"Error scraping URL directly {url}: {str(e)}")
            return {"error": str(e), "content": "", "timestamp": datetime.now().isoformat()}
    
    def _extract_news_from_html(self, html_content: str) -> List[Dict]:
        """Extract news items from HTML using common patterns."""
        news_items = []
        
        try:
            # Look for common news patterns
            # Pattern 1: Article tags
            article_patterns = [
                r'<article[^>]*>(.*?)</article>',
                r'<div[^>]*class="[^"]*news[^"]*"[^>]*>(.*?)</div>',
                r'<div[^>]*class="[^"]*article[^"]*"[^>]*>(.*?)</div>',
                r'<div[^>]*class="[^"]*post[^"]*"[^>]*>(.*?)</div>',
                r'<li[^>]*class="[^"]*news[^"]*"[^>]*>(.*?)</li>'
            ]
            
            for pattern in article_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE | re.DOTALL)
                for match in matches[:5]:  # Limit to 5 items
                    # Extract title
                    title_match = re.search(r'<h[1-6][^>]*>(.*?)</h[1-6]>', match, re.IGNORECASE | re.DOTALL)
                    title = title_match.group(1).strip() if title_match else "Nyhet"
                    
                    # Extract date
                    date_match = re.search(r'<time[^>]*>(.*?)</time>', match, re.IGNORECASE | re.DOTALL)
                    date = date_match.group(1).strip() if date_match else ""
                    
                    # Extract content
                    content_match = re.search(r'<p[^>]*>(.*?)</p>', match, re.IGNORECASE | re.DOTALL)
                    content = content_match.group(1).strip() if content_match else ""
                    
                    # Clean HTML tags
                    title = re.sub(r'<[^>]*>', '', title)
                    content = re.sub(r'<[^>]*>', '', content)
                    
                    if title and title != "Nyhet":
                        news_items.append({
                            "title": title,
                            "date": date,
                            "content": content[:200]  # Limit content length
                        })
            
            # If no news items found, try to extract from headings
            if not news_items:
                heading_matches = re.findall(r'<h[1-6][^>]*>(.*?)</h[1-6]>', html_content, re.IGNORECASE | re.DOTALL)
                for heading in heading_matches[:3]:  # Limit to 3 headings
                    clean_heading = re.sub(r'<[^>]*>', '', heading).strip()
                    if clean_heading and len(clean_heading) > 5:
                        news_items.append({
                            "title": clean_heading,
                            "date": "",
                            "content": ""
                        })
            
        except Exception as e:
            logger.warning(f"Error extracting news from HTML: {str(e)}")
        
        return news_items
        
    def scrape_url(self, url: str) -> Dict:
        """Scrape content from a URL using Firecrawl extract endpoint.
        
        This method processes a single URL at a time to ensure that news items
        are correctly associated with their respective URLs and not mixed
        between different sources.
        """
        if not self.use_firecrawl:
            logger.error(f"No valid Firecrawl API key provided for {url}")
            return {"error": "No valid Firecrawl API key", "content": "", "timestamp": datetime.now().isoformat()}
            
        # Call the Firecrawl extract API
        result = self._scrape_with_firecrawl(url)
        
        # Handle None result (which could happen if rate limited)
        if result is None:
            logger.error(f"Failed to scrape {url} with Firecrawl (null result)")
            return {"error": "Failed to scrape with Firecrawl", "timestamp": datetime.now().isoformat()}
            
        # The _scrape_with_firecrawl method now always returns a dictionary,
        # either with content or with an error message
        return result