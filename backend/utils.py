"""
Utility functions for Mitti Scraper
"""

import logging
from typing import Dict, List, Optional, Tuple, Any, Union

# Configure logging
def setup_logging():
    """Configure and return logger."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("content_monitor.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("content_monitor")

# Create logger
logger = setup_logging()