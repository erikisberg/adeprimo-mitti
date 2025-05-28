"""
Content comparison functionality for Mitti Scraper
"""

import difflib
from typing import Dict, Tuple

class ContentComparator:
    """Compares content to detect changes."""
    
    def __init__(self, similarity_threshold: float = 0.9):
        """Initialize with similarity threshold."""
        self.similarity_threshold = similarity_threshold
        
    def has_significant_changes(self, old_content: Dict, new_content: Dict) -> Tuple[bool, float, str]:
        """
        Determine if there are significant changes between old and new content.
        
        Returns:
            Tuple containing:
            - Whether significant changes were detected (bool)
            - Similarity score (float)
            - Summary of changes (str)
        """
        if not old_content:
            return True, 0.0, "Initial content fetch"
        
        old_text = old_content.get("content", "")
        new_text = new_content.get("content", "")
        
        # Calculate similarity ratio
        similarity = difflib.SequenceMatcher(None, old_text, new_text).ratio()
        
        # Generate a diff summary
        diff = list(difflib.unified_diff(
            old_text.splitlines(), 
            new_text.splitlines(), 
            lineterm='',
            n=3
        ))
        diff_summary = "\n".join(diff[:20])  # Limit diff output
        
        # Check if changes are significant
        has_changes = similarity < self.similarity_threshold
        
        return has_changes, similarity, diff_summary