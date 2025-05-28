"""
OpenAI content analysis for Mitti Scraper - Fixed version using official SDK
"""

import re
import time
from datetime import datetime
from typing import Dict, List, Union
from openai import OpenAI

from utils import logger

class OpenAIAnalyzer:
    """Analyzes content using OpenAI Assistant API."""
    
    def __init__(self, api_key: str, assistant_id: str):
        """Initialize with OpenAI API key and Assistant ID."""
        # Clean the API key to remove any whitespace or newlines
        self.api_key = api_key.strip() if api_key else ""
        self.assistant_id = assistant_id.strip() if assistant_id else ""
        
        # Add extra logging for debugging
        logger.info(f"OpenAIAnalyzer initialized with assistant ID: {self.assistant_id}")
        
        # Initialize OpenAI client
        if self.api_key and not self.api_key.startswith("your_"):
            self.client = OpenAI(api_key=self.api_key)
            logger.info("OpenAI API key configured")
        else:
            self.client = None
            logger.warning("No valid OpenAI API key provided")
            
        if self.assistant_id and not self.assistant_id.startswith("your_"):
            logger.info("OpenAI Assistant ID configured")
        else:
            logger.warning("No valid OpenAI Assistant ID provided")
        
    def extract_news_items(self, content_data: Union[str, Dict]) -> List[Dict]:
        """
        Extract news items from content for analysis.
        Can accept either a string content or a full content dictionary with extracted news.
        """
        news_items = []
        
        # Check if we're getting a dictionary with extracted news already
        if isinstance(content_data, dict):
            # Check for extracted_news field first (standard format)
            if "extracted_news" in content_data and content_data["extracted_news"]:
                # Use the pre-extracted news items, but convert to our standard format if needed
                for item in content_data["extracted_news"]:
                    news_items.append({
                        "title": item.get("title", ""),
                        "url": content_data.get("url", ""),  # Main URL as fallback
                        "date": item.get("date", None),
                        "snippet": item.get("content", "")[:500] if item.get("content") else ""  # Limit to reasonable snippet length
                    })
                logger.info(f"Using {len(news_items)} news items from extracted_news field")
                return news_items
            # Check for news_items field (for backward compatibility)
            elif "news_items" in content_data and content_data["news_items"]:
                for item in content_data["news_items"]:
                    news_items.append({
                        "title": item.get("title", ""),
                        "url": content_data.get("url", ""),  # Main URL as fallback
                        "date": item.get("date", None),
                        "snippet": item.get("content", "")[:500] if item.get("content") else ""  # Limit to reasonable snippet length
                    })
                logger.info(f"Using {len(news_items)} news items from news_items field (legacy format)")
                return news_items
            # If no extracted news, use the content string
            content = content_data.get("content", "")
        else:
            # If string was passed directly
            content = content_data
        
        # Fallback: Extract news items with regex patterns
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
                "snippet": snippet
            })
        
        return news_items
    
    def analyze_content(self, url: str, content: Union[str, Dict], changes: str) -> Dict:
        """
        Analyze content using OpenAI Assistant.
        
        Content can be either a string or a dictionary containing the content and extracted news.
        Returns analysis with interest score and explanation.
        """
        # Extract news items from the content
        news_items = self.extract_news_items(content)
        
        # If content is a dictionary, get the actual content string
        if isinstance(content, dict):
            content_text = content.get("content", "")
        else:
            content_text = content
        
        # Skip if no valid API key or client
        if not self.client or not self.api_key or self.api_key.startswith("your_") or not self.assistant_id or self.assistant_id.startswith("your_"):
            logger.warning("Skipping OpenAI analysis: No valid API key or Assistant ID")
            
            # Provide a fallback analysis based on simple heuristics
            word_count = len(content_text.split())
            has_new_content = "new" in content_text.lower() or "ny" in content_text.lower()
            has_important_content = "important" in content_text.lower() or "viktig" in content_text.lower()
            has_update_content = "update" in content_text.lower() or "uppdatering" in content_text.lower()
            
            # Simple scoring based on content signals
            score = 1  # Base score
            if has_new_content:
                score += 1
            if has_important_content:
                score += 1
            if has_update_content:
                score += 1
            if word_count > 1000:
                score += 1
            
            # Cap at 5
            score = min(score, 5)
            
            return {
                "analysis": f"Automated analysis (OpenAI unavailable): Interest score {score}/5. This analysis is based on simple text patterns.",
                "score": score,
                "timestamp": datetime.now().isoformat(),
                "extracted_news": news_items
            }
            
        try:
            logger.info(f"Analyzing content from {url} with OpenAI Assistant")
            
            # Create a thread
            logger.info(f"Creating OpenAI thread with Assistant ID: {self.assistant_id}")
            thread = self.client.beta.threads.create()
            
            # Prepare the message content
            message_content = f"""Analysera följande webbinnehåll från {url} och betygsätt det på en skala från 1-5:
                
Innehåll:
{content_text[:5000]}  # Begränsa innehållslängden

Senaste ändringarna:
{changes}

Analysera detta innehåll baserat på nyhetsvärde, relevans och betydelse där:
1 = Inte intressant (rutinuppdateringar)
2 = Något intressant
3 = Måttligt intressant
4 = Mycket intressant (betydande utveckling)
5 = Extremt intressant (stor utveckling)

Ge ditt betyg (1-5) och en kort förklaring på svenska. Tänk på att det är lokala nyheter från Sollentuna kommun som är viktiga för boende i området. Fokusera på information som är relevant för Mitt i Sollentunas läsare.

Specifikt betygsätt nyhetsvärdet av följande specifika inslag (om de finns i innehållet), så vi kan se vilka nyheter som är mest intressanta:
"""
            
            # Add any extracted news items to the prompt
            if news_items:
                news_items_text = "\n".join([f"- \"{item['title']}\" ({item['date'] if item['date'] else 'Inget datum'})" for item in news_items[:5]])
                message_content += f"\n\nSpecifika nyheter att betygsätta:\n{news_items_text}"
            
            # Add a message to the thread
            message = self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=message_content
            )
            
            # Run the Assistant
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.assistant_id
            )
            
            # Poll for completion
            while run.status in ["queued", "in_progress"]:
                time.sleep(2)
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
            
            # Get the assistant's response
            if run.status == "completed":
                messages = self.client.beta.threads.messages.list(thread_id=thread.id)
                
                # Find the assistant's response
                for msg in messages.data:
                    if msg.role == "assistant":
                        # Extract the text content
                        formatted_text = ""
                        if msg.content and isinstance(msg.content, list):
                            for item in msg.content:
                                if hasattr(item, 'text') and hasattr(item.text, 'value'):
                                    formatted_text = item.text.value
                                    break
                                    
                        # Extract the rating if present in the text
                        rating = None
                        if formatted_text:
                            # Look for patterns like "Rating: 3" or "1." at the start
                            rating_match = re.search(r"(?:Rating:?\s*|^)(\d)[.:]", formatted_text)
                            if rating_match:
                                rating = rating_match.group(1)
                            
                        # Associate ratings with specific news items if possible
                        rated_news_items = self._associate_ratings_with_news_items(formatted_text, news_items)
                        
                        return {
                            "analysis": formatted_text,
                            "rating": rating,
                            "timestamp": datetime.now().isoformat(),
                            "extracted_news": rated_news_items if rated_news_items else news_items
                        }
                
                # If we couldn't extract content properly
                return {
                    "analysis": "Analysis completed but content format not recognized",
                    "timestamp": datetime.now().isoformat(),
                    "extracted_news": news_items
                }
            else:
                error_msg = f"Assistant run failed with status: {run.status}"
                if hasattr(run, 'last_error') and run.last_error:
                    error_msg += f" - {run.last_error.message}"
                    
                return {
                    "analysis": f"Error: {error_msg}",
                    "timestamp": datetime.now().isoformat(),
                    "extracted_news": news_items
                }
            
        except Exception as e:
            logger.error(f"Error analyzing content with OpenAI: {str(e)}")
                
            # Fall back to simple analysis
            word_count = len(content_text.split())
            has_new_content = "new" in content_text.lower() or "ny" in content_text.lower()
            has_important_content = "important" in content_text.lower() or "viktig" in content_text.lower()
            has_update_content = "update" in content_text.lower() or "uppdatering" in content_text.lower()
            
            # Simple scoring based on content signals
            score = 1  # Base score
            if has_new_content:
                score += 1
            if has_important_content:
                score += 1
            if has_update_content:
                score += 1
            if word_count > 1000:
                score += 1
            
            # Cap at 5
            score = min(score, 5)
            
            return {
                "analysis": f"Automated analysis (OpenAI error: {str(e)}): Interest score {score}/5.",
                "score": score,
                "timestamp": datetime.now().isoformat(),
                "extracted_news": news_items
            }
    
    def _associate_ratings_with_news_items(self, analysis_text: str, news_items: List[Dict]) -> List[Dict]:
        """Try to associate ratings with specific news items from the analysis text."""
        if not news_items or not analysis_text:
            return []
            
        rated_items = []
        
        # Look for structured format with news item sections
        # First, try to identify if the analysis has a structured format with items and ratings
        
        for item in news_items:
            title = item["title"]
            item_copy = item.copy()
            
            # Many possible patterns observed in OpenAI outputs:
            patterns = [
                # Match format "Title (date) - Betyg: 3"
                fr"\*\*{re.escape(title)}(?:\s*\([^)]*\))?\*\*(?:[^*]*?[Bb]etyg:\s*(\d))",
                
                # Match format "Title - Betyg: 3"
                fr"{re.escape(title)}(?:[^-]*)-[^-]*[Bb]etyg:\s*(\d)",
                
                # Match format where title and rating are separated with newline
                fr"{re.escape(title)}(?:.{{0,200}}?)(?:\n|\r)(?:.{{0,100}}?)[Bb]etyg:\s*(\d)",
                
                # Match bullets with ratings
                fr"[•\*-]\s*{re.escape(title)}(?:.{{0,100}}?)[Bb]etyg:\s*(\d)",
                
                # Match section headers with ratings inside parentheses
                fr"\*\*{re.escape(title)}[^\(]*\([^\)]*(\d)[^\)]*\)",
                
                # Match simple rating pattern (basic fallback)
                fr"{re.escape(title)}[^0-9]*?(\d)\s*/\s*5",
                
                # Match heading with rating on next line
                fr"\*\*{re.escape(title)}\*\*(?:\s*\([^)]*\))?(?:.{{0,50}}?)\n\s*-\s*\*\*Betyg:\s*(\d)\*\*"
            ]
            
            # Try each pattern until we find a match
            for pattern in patterns:
                rating_match = re.search(pattern, analysis_text, re.IGNORECASE | re.DOTALL)
                if rating_match:
                    try:
                        item_copy["rating"] = int(rating_match.group(1))
                        logger.info(f"Found rating {item_copy['rating']} for '{title}' using pattern: {pattern}")
                        break
                    except (ValueError, IndexError):
                        logger.warning(f"Failed to extract rating for '{title}' from match: {rating_match.group(0)}")
            
            # If no patterns matched, search for title and nearby digit as a last resort
            if "rating" not in item_copy:
                # Look for the title and a rating within a reasonable distance (300 chars)
                title_pos = analysis_text.find(title)
                if title_pos > -1:
                    # Look for a rating in the 300 characters after the title
                    search_region = analysis_text[title_pos:title_pos+300]
                    rating_match = re.search(r"[Bb]etyg:?\s*(\d)", search_region)
                    if rating_match:
                        try:
                            item_copy["rating"] = int(rating_match.group(1))
                            logger.info(f"Found rating {item_copy['rating']} for '{title}' using fallback search")
                        except (ValueError, IndexError):
                            logger.warning(f"Failed to extract rating from fallback search")
            
            rated_items.append(item_copy)
        
        return rated_items